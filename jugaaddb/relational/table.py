from typing import Any, Callable

from ..core.schema import Schema


class Table:
    def __init__(
        self,
        name: str,
        schema: Schema,
        storage: dict[str, Any],
        save_callback: Callable[[], None] | None = None
    ):
        self.name = name
        self.schema = schema
        self.storage = storage
        self._save_callback = save_callback

        self.storage.setdefault("rows", [])

    @property
    def rows(self) -> list[dict[str, Any]]:
        return self.storage["rows"]

    def insert(self, row: dict[str, Any]) -> None:
        self.schema.validate_row(row)

        self._check_primary_key(row)
        self._check_unique_columns(row)

        normalized = {
            column.name: row.get(column.name)
            for column in self.schema.columns
        }

        self.rows.append(normalized)
        self._save()

    def select_all(self) -> list[dict[str, Any]]:
        return [row.copy() for row in self.rows]

    def update(
        self,
        condition: dict[str, Any],
        changes: dict[str, Any]
    ) -> int:
        """
        Update rows matching all values in condition.

        Returns the number of updated rows.
        """

        if not changes:
            return 0

        self._validate_columns(changes)
        self._validate_columns(condition)

        matched_rows = [
            row
            for row in self.rows
            if self._matches(row, condition)
        ]

        if not matched_rows:
            return 0

        # Create updated copies first.
        updated_rows = []

        for row in matched_rows:
            updated = row.copy()
            updated.update(changes)

            self.schema.validate_row(updated)
            updated_rows.append((row, updated))

        # Validate constraints against the final table state
        # before modifying anything.
        candidate_rows = [row.copy() for row in self.rows]

        for old_row, new_row in updated_rows:
            index = candidate_rows.index(old_row)
            candidate_rows[index] = new_row

        self._validate_primary_key_rows(candidate_rows)
        self._validate_unique_rows(candidate_rows)

        # Apply changes.
        for old_row, new_row in updated_rows:
            index = self.rows.index(old_row)
            self.rows[index] = new_row

        self._save()

        return len(updated_rows)

    def delete(self, condition: dict[str, Any]) -> int:
        """
        Delete rows matching all values in condition.

        Returns the number of deleted rows.
        """

        self._validate_columns(condition)

        original_count = len(self.rows)

        self.rows[:] = [
            row
            for row in self.rows
            if not self._matches(row, condition)
        ]

        deleted_count = original_count - len(self.rows)

        if deleted_count > 0:
            self._save()

        return deleted_count

    def _matches(
        self,
        row: dict[str, Any],
        condition: dict[str, Any]
    ) -> bool:
        return all(
            row.get(column) == value
            for column, value in condition.items()
        )

    def _validate_columns(
        self,
        values: dict[str, Any]
    ) -> None:
        valid_columns = {
            column.name
            for column in self.schema.columns
        }

        unknown = set(values.keys()) - valid_columns

        if unknown:
            raise ValueError(
                f"Unknown columns: {sorted(unknown)}"
            )

    def _validate_primary_key_rows(
        self,
        rows: list[dict[str, Any]]
    ) -> None:
        primary_key = next(
            (
                column
                for column in self.schema.columns
                if column.primary_key
            ),
            None
        )

        if primary_key is None:
            return

        seen = set()

        for row in rows:
            value = row.get(primary_key.name)

            if value in seen:
                raise ValueError(
                    f"Duplicate primary key: {value}"
                )

            seen.add(value)

    def _validate_unique_rows(
        self,
        rows: list[dict[str, Any]]
    ) -> None:
        unique_columns = [
            column
            for column in self.schema.columns
            if column.unique
        ]

        for column in unique_columns:
            seen = set()

            for row in rows:
                value = row.get(column.name)

                if value is None:
                    continue

                if value in seen:
                    raise ValueError(
                        f"Duplicate value for UNIQUE column "
                        f"'{column.name}': {value}"
                    )

                seen.add(value)

    def _check_primary_key(
        self,
        row: dict[str, Any]
    ) -> None:
        primary_key = next(
            (
                column
                for column in self.schema.columns
                if column.primary_key
            ),
            None
        )

        if primary_key is None:
            return

        value = row.get(primary_key.name)

        for existing in self.rows:
            if existing.get(primary_key.name) == value:
                raise ValueError(
                    f"Duplicate primary key: {value}"
                )

    def _check_unique_columns(
        self,
        row: dict[str, Any]
    ) -> None:
        unique_columns = [
            column
            for column in self.schema.columns
            if column.unique
        ]

        for column in unique_columns:
            value = row.get(column.name)

            if value is None:
                continue

            for existing in self.rows:
                if existing.get(column.name) == value:
                    raise ValueError(
                        f"Duplicate value for UNIQUE column "
                        f"'{column.name}': {value}"
                    )

    def _save(self) -> None:
        if self._save_callback is not None:
            self._save_callback()