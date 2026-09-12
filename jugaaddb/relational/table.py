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

        # Add row to memory
        self.rows.append(normalized)

        # Persist row to database file
        self._save()

    def select_all(self) -> list[dict[str, Any]]:
        return [row.copy() for row in self.rows]

    def _save(self) -> None:
        if self._save_callback is not None:
            self._save_callback()

    def _check_primary_key(self, row: dict[str, Any]) -> None:
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

    def _check_unique_columns(self, row: dict[str, Any]) -> None:
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