from typing import Any

from .base import Index, RecordID


class IndexScan:
    def __init__(
        self,
        index: Index,
    ):
        if not isinstance(index, Index):
            raise TypeError("Index scan requires an Index.")

        self.index = index

    def exact(
        self,
        key: Any,
    ) -> list[RecordID]:
        return list(
            self.index.search(key)
        )

    def range(
        self,
        start_key: Any | None = None,
        end_key: Any | None = None,
        include_start: bool = True,
        include_end: bool = True,
    ) -> list[RecordID]:
        if not hasattr(
            self.index,
            "search_range",
        ):
            raise TypeError(
                "Index does not support range scans."
            )

        entries = self.index.search_range(
            start_key=start_key,
            end_key=end_key,
            include_start=include_start,
            include_end=include_end,
        )

        return [
            entry.record_id
            for entry in entries
        ]

    def all(self) -> list[RecordID]:
        return [
            entry.record_id
            for entry in self.index.scan()
        ]