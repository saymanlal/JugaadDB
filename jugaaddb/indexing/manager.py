from .base import Index
from .btree import BPlusTreeIndex
from .memory import MemoryIndex


class IndexManager:
    def __init__(self):
        self._indexes: dict[
            str,
            dict[str, Index],
        ] = {}

    def create_index(
        self,
        table_name: str,
        index_name: str,
        column: str,
        index_type: str = "memory",
        order: int = 4,
    ) -> Index:
        self._validate_name(
            table_name,
            "Table name",
        )

        self._validate_name(
            index_name,
            "Index name",
        )

        self._validate_name(
            column,
            "Column name",
        )

        if not isinstance(
            index_type,
            str,
        ):
            raise TypeError(
                "Index type must be a string."
            )

        normalized_type = index_type.lower()

        table_indexes = self._indexes.setdefault(
            table_name,
            {},
        )

        if index_name in table_indexes:
            raise ValueError(
                f"Index already exists: {index_name}"
            )

        if normalized_type == "memory":
            index = MemoryIndex(
                index_name,
                column,
            )

        elif normalized_type == "btree":
            index = BPlusTreeIndex(
                index_name,
                column,
                order=order,
            )

        else:
            raise ValueError(
                f"Unsupported index type: {index_type}"
            )

        table_indexes[index_name] = index

        return index

    def drop_index(
        self,
        table_name: str,
        index_name: str,
    ) -> None:
        table_indexes = self._get_table_indexes(
            table_name
        )

        if index_name not in table_indexes:
            raise ValueError(
                f"Index does not exist: {index_name}"
            )

        del table_indexes[index_name]

        if not table_indexes:
            del self._indexes[
                table_name
            ]

    def get_index(
        self,
        table_name: str,
        index_name: str,
    ) -> Index:
        table_indexes = self._get_table_indexes(
            table_name
        )

        if index_name not in table_indexes:
            raise ValueError(
                f"Index does not exist: {index_name}"
            )

        return table_indexes[
            index_name
        ]

    def list_indexes(
        self,
        table_name: str,
    ) -> list[str]:
        table_indexes = self._indexes.get(
            table_name,
            {},
        )

        return sorted(
            table_indexes
        )

    def list_all(
        self,
        table_name: str,
    ) -> list[Index]:
        table_indexes = self._indexes.get(
            table_name,
            {},
        )

        return sorted(
            table_indexes.values(),
            key=lambda index: index.name,
        )

    def indexes_for_column(
        self,
        table_name: str,
        column: str,
    ) -> list[Index]:
        table_indexes = self._indexes.get(
            table_name,
            {},
        )

        return sorted(
            [
                index
                for index in table_indexes.values()
                if index.column == column
            ],
            key=lambda index: index.name,
        )

    def _get_table_indexes(
        self,
        table_name: str,
    ) -> dict[str, Index]:
        if table_name not in self._indexes:
            raise ValueError(
                f"No indexes exist for table: {table_name}"
            )

        return self._indexes[
            table_name
        ]

    def _validate_name(
        self,
        value: str,
        label: str,
    ) -> None:
        if not isinstance(
            value,
            str,
        ) or not value.strip():
            raise ValueError(
                f"{label} must be a non-empty string."
            )