from typing import Any

from .base import Index, IndexEntry, RecordID


class MemoryIndex(Index):
    def __init__(self, name: str, column: str):
        super().__init__(name, column)
        self._entries: dict[Any, list[RecordID]] = {}

    def insert(self, key: Any, record_id: RecordID) -> None:
        self._validate_record_id(record_id)

        records = self._entries.setdefault(key, [])

        if record_id in records:
            raise ValueError(
                f"Record ID already exists in index: {record_id}"
            )

        records.append(record_id)

    def delete(self, key: Any, record_id: RecordID) -> None:
        self._validate_record_id(record_id)

        if key not in self._entries:
            raise ValueError(f"Index key does not exist: {key}")

        records = self._entries[key]

        if record_id not in records:
            raise ValueError(
                f"Record ID does not exist for index key: {record_id}"
            )

        records.remove(record_id)

        if not records:
            del self._entries[key]

    def search(self, key: Any) -> list[RecordID]:
        return list(self._entries.get(key, []))

    def scan(self) -> list[IndexEntry]:
        entries = []

        for key in sorted(self._entries, key=lambda value: (type(value).__name__, repr(value))):
            for record_id in self._entries[key]:
                entries.append(IndexEntry(key, record_id))

        return entries

    def _validate_record_id(self, record_id: RecordID) -> None:
        if not isinstance(record_id, tuple) or len(record_id) != 2:
            raise TypeError(
                "Record ID must be a (page_id, slot_id) tuple."
            )

        page_id, slot_id = record_id

        if type(page_id) is not int:
            raise TypeError("Page ID must be an integer.")

        if type(slot_id) is not int:
            raise TypeError("Slot ID must be an integer.")

        if page_id <= 0:
            raise ValueError("Record page ID must be greater than zero.")

        if slot_id < 0:
            raise ValueError("Record slot ID cannot be negative.")