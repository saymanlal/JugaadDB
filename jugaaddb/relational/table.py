from typing import Any, Callable

from ..core.schema import Schema


class Table:
    def __init__(
        self,
        name: str,
        schema: Schema,
        storage: dict[str, Any],
        save_callback: Callable[[], None] | None = None,
        index_manager=None,
    ):
        self.name = name
        self.schema = schema
        self.storage = storage
        self._save_callback = save_callback
        self.index_manager = index_manager

        self.storage.setdefault("rows", [])
        self.storage.setdefault("record_ids", [])

        self._initialize_record_ids()

    @property
    def rows(self) -> list[dict[str, Any]]:
        return self.storage["rows"]

    @property
    def record_ids(self) -> list[tuple[int, int]]:
        return self.storage["record_ids"]

    def insert(self, row: dict[str, Any]) -> None:
        self.schema.validate_row(row)
        self._check_primary_key(row)
        self._check_unique_columns(row)

        normalized = {
            column.name: row.get(column.name)
            for column in self.schema.columns
        }

        record_id = self._next_record_id()

        self.rows.append(normalized)
        self.record_ids.append(record_id)

        try:
            self._index_insert(normalized, record_id)
            self._save()
        except Exception:
            self.rows.pop()
            self.record_ids.pop()
            self._index_delete(
                normalized,
                record_id,
            )
            raise

    def select_all(self) -> list[dict[str, Any]]:
        return [
            row.copy()
            for row in self.rows
        ]

    def select_all_with_ids(
        self,
    ) -> list[tuple[tuple[int, int], dict[str, Any]]]:
        return [
            (
                record_id,
                row.copy(),
            )
            for record_id, row in zip(
                self.record_ids,
                self.rows,
            )
        ]

    def row_by_record_id(
        self,
        record_id: tuple[int, int],
    ) -> dict[str, Any]:
        if record_id not in self.record_ids:
            raise ValueError(
                f"Record does not exist: {record_id}"
            )

        index = self.record_ids.index(
            record_id
        )

        return self.rows[index].copy()

    def update(
        self,
        condition: dict[str, Any],
        changes: dict[str, Any],
    ) -> int:
        if not changes:
            return 0

        self._validate_columns(changes)
        self._validate_columns(condition)

        matched = [
            (
                index,
                self.rows[index],
                self.record_ids[index],
            )
            for index in range(len(self.rows))
            if self._matches(
                self.rows[index],
                condition,
            )
        ]

        if not matched:
            return 0

        updated_rows = []

        for index, row, record_id in matched:
            updated = row.copy()
            updated.update(changes)

            self.schema.validate_row(updated)

            updated_rows.append(
                (
                    index,
                    row,
                    updated,
                    record_id,
                )
            )

        candidate_rows = [
            row.copy()
            for row in self.rows
        ]

        for index, _, updated, _ in updated_rows:
            candidate_rows[index] = updated

        self._validate_primary_key_rows(
            candidate_rows
        )

        self._validate_unique_rows(
            candidate_rows
        )

        changed_indexes = []

        for index, old_row, new_row, record_id in updated_rows:
            indexes = self._changed_indexes(
                old_row,
                new_row,
            )

            for db_index in indexes:
                old_value = old_row.get(
                    db_index.column
                )
                new_value = new_row.get(
                    db_index.column
                )

                if old_value == new_value:
                    continue

                changed_indexes.append(
                    (
                        db_index,
                        old_value,
                        new_value,
                        record_id,
                    )
                )

        completed_deletes = []

        try:
            for (
                db_index,
                old_value,
                new_value,
                record_id,
            ) in changed_indexes:
                if old_value is not None:
                    db_index.delete(
                        old_value,
                        record_id,
                    )

                completed_deletes.append(
                    (
                        db_index,
                        old_value,
                        record_id,
                    )
                )

                if new_value is not None:
                    db_index.insert(
                        new_value,
                        record_id,
                    )

            for index, _, updated, _ in updated_rows:
                self.rows[index] = updated

            self._save()

        except Exception:
            for (
                db_index,
                old_value,
                new_value,
                record_id,
            ) in reversed(changed_indexes):
                try:
                    if new_value is not None:
                        db_index.delete(
                            new_value,
                            record_id,
                        )
                except Exception:
                    pass

                try:
                    if old_value is not None:
                        db_index.insert(
                            old_value,
                            record_id,
                        )
                except Exception:
                    pass

            for (
                index,
                old_row,
                _,
                _,
            ) in updated_rows:
                self.rows[index] = old_row

            raise

        return len(updated_rows)

    def delete(
        self,
        condition: dict[str, Any],
    ) -> int:
        self._validate_columns(condition)

        matched = [
            (
                index,
                self.rows[index].copy(),
                self.record_ids[index],
            )
            for index in range(len(self.rows))
            if self._matches(
                self.rows[index],
                condition,
            )
        ]

        if not matched:
            return 0

        deleted_index_entries = []

        try:
            for _, row, record_id in matched:
                for db_index in self._indexes():
                    value = row.get(
                        db_index.column
                    )

                    if value is None:
                        continue

                    db_index.delete(
                        value,
                        record_id,
                    )

                    deleted_index_entries.append(
                        (
                            db_index,
                            value,
                            record_id,
                        )
                    )

            matched_positions = {
                index
                for index, _, _ in matched
            }

            self.rows[:] = [
                row
                for index, row in enumerate(
                    self.rows
                )
                if index not in matched_positions
            ]

            self.record_ids[:] = [
                record_id
                for index, record_id in enumerate(
                    self.record_ids
                )
                if index not in matched_positions
            ]

            self._save()

        except Exception:
            for (
                db_index,
                value,
                record_id,
            ) in reversed(
                deleted_index_entries
            ):
                try:
                    db_index.insert(
                        value,
                        record_id,
                    )
                except Exception:
                    pass

            raise

        return len(matched)

    def _initialize_record_ids(self) -> None:
        rows = self.rows
        record_ids = self.record_ids

        if len(record_ids) > len(rows):
            raise ValueError(
                "Stored record ID count exceeds row count."
            )

        if len(record_ids) == len(rows):
            self._validate_record_ids()
            return

        if record_ids:
            next_slot = max(
                slot_id
                for page_id, slot_id
                in record_ids
            ) + 1
        else:
            next_slot = 0

        while len(record_ids) < len(rows):
            record_ids.append(
                (1, next_slot)
            )
            next_slot += 1

        self._validate_record_ids()

        if self._save_callback is not None:
            self._save_callback()

    def _next_record_id(
        self,
    ) -> tuple[int, int]:
        if not self.record_ids:
            return (1, 0)

        next_slot = max(
            slot_id
            for page_id, slot_id
            in self.record_ids
        ) + 1

        return (1, next_slot)

    def _validate_record_ids(self) -> None:
        seen = set()

        for record_id in self.record_ids:
            if (
                not isinstance(
                    record_id,
                    (list, tuple),
                )
                or len(record_id) != 2
            ):
                raise ValueError(
                    "Invalid stored record ID."
                )

            page_id, slot_id = record_id

            if type(page_id) is not int:
                raise ValueError(
                    "Invalid record page ID."
                )

            if type(slot_id) is not int:
                raise ValueError(
                    "Invalid record slot ID."
                )

            if page_id <= 0:
                raise ValueError(
                    "Invalid record page ID."
                )

            if slot_id < 0:
                raise ValueError(
                    "Invalid record slot ID."
                )

            normalized = (
                page_id,
                slot_id,
            )

            if normalized in seen:
                raise ValueError(
                    f"Duplicate record ID: {normalized}"
                )

            seen.add(normalized)

        self.storage["record_ids"] = [
            (
                record_id[0],
                record_id[1],
            )
            for record_id in self.record_ids
        ]

    def _matches(
        self,
        row: dict[str, Any],
        condition: dict[str, Any],
    ) -> bool:
        return all(
            row.get(column) == value
            for column, value
            in condition.items()
        )

    def _validate_columns(
        self,
        values: dict[str, Any],
    ) -> None:
        valid_columns = {
            column.name
            for column in self.schema.columns
        }

        unknown = (
            set(values.keys())
            - valid_columns
        )

        if unknown:
            raise ValueError(
                f"Unknown columns: {sorted(unknown)}"
            )

    def _validate_primary_key_rows(
        self,
        rows: list[dict[str, Any]],
    ) -> None:
        primary_key = next(
            (
                column
                for column in self.schema.columns
                if column.primary_key
            ),
            None,
        )

        if primary_key is None:
            return

        seen = set()

        for row in rows:
            value = row.get(
                primary_key.name
            )

            if value in seen:
                raise ValueError(
                    f"Duplicate primary key: {value}"
                )

            seen.add(value)

    def _validate_unique_rows(
        self,
        rows: list[dict[str, Any]],
    ) -> None:
        unique_columns = [
            column
            for column in self.schema.columns
            if column.unique
        ]

        for column in unique_columns:
            seen = set()

            for row in rows:
                value = row.get(
                    column.name
                )

                if value is None:
                    continue

                if value in seen:
                    raise ValueError(
                        f"Duplicate value for "
                        f"UNIQUE column "
                        f"'{column.name}': {value}"
                    )

                seen.add(value)

    def _check_primary_key(
        self,
        row: dict[str, Any],
    ) -> None:
        primary_key = next(
            (
                column
                for column in self.schema.columns
                if column.primary_key
            ),
            None,
        )

        if primary_key is None:
            return

        value = row.get(
            primary_key.name
        )

        for existing in self.rows:
            if (
                existing.get(
                    primary_key.name
                )
                == value
            ):
                raise ValueError(
                    f"Duplicate primary key: {value}"
                )

    def _check_unique_columns(
        self,
        row: dict[str, Any],
    ) -> None:
        unique_columns = [
            column
            for column in self.schema.columns
            if column.unique
        ]

        for column in unique_columns:
            value = row.get(
                column.name
            )

            if value is None:
                continue

            for existing in self.rows:
                if (
                    existing.get(
                        column.name
                    )
                    == value
                ):
                    raise ValueError(
                        f"Duplicate value for "
                        f"UNIQUE column "
                        f"'{column.name}': {value}"
                    )

    def _indexes(self):
        if self.index_manager is None:
            return []

        return self.index_manager.list_all(
            self.name
        )

    def _changed_indexes(
        self,
        old_row: dict[str, Any],
        new_row: dict[str, Any],
    ):
        return [
            db_index
            for db_index in self._indexes()
            if old_row.get(
                db_index.column
            )
            != new_row.get(
                db_index.column
            )
        ]

    def _index_insert(
        self,
        row: dict[str, Any],
        record_id: tuple[int, int],
    ) -> None:
        inserted = []

        try:
            for db_index in self._indexes():
                value = row.get(
                    db_index.column
                )

                if value is None:
                    continue

                db_index.insert(
                    value,
                    record_id,
                )

                inserted.append(
                    (
                        db_index,
                        value,
                    )
                )

        except Exception:
            for db_index, value in reversed(
                inserted
            ):
                try:
                    db_index.delete(
                        value,
                        record_id,
                    )
                except Exception:
                    pass

            raise

    def _index_delete(
        self,
        row: dict[str, Any],
        record_id: tuple[int, int],
    ) -> None:
        for db_index in self._indexes():
            value = row.get(
                db_index.column
            )

            if value is None:
                continue

            try:
                db_index.delete(
                    value,
                    record_id,
                )
            except Exception:
                pass

    def _save(self) -> None:
        if self._save_callback is not None:
            self._save_callback()