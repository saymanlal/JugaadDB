from pathlib import Path

from .base import Index
from .btree import BPlusTreeIndex
from .memory import MemoryIndex
from .metadata import IndexMetadata
from .persistence import BTreePersistence


class IndexManager:
    def __init__(
        self,
        persistence_directory: str | Path | None = None,
    ):
        self._indexes: dict[
            str,
            dict[str, Index],
        ] = {}

        self.persistence_directory = (
            Path(persistence_directory)
            if persistence_directory is not None
            else None
        )

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

        self._delete_persistent_index(
            table_name,
            index_name,
        )

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

    def save_index(
        self,
        table_name: str,
        index_name: str,
    ) -> None:
        self._validate_persistence_directory()

        index = self.get_index(
            table_name,
            index_name,
        )

        if not isinstance(
            index,
            BPlusTreeIndex,
        ):
            raise ValueError(
                "Only B+Tree indexes can be persisted."
            )

        metadata = IndexMetadata(
            table_name=table_name,
            index_name=index.name,
            column=index.column,
            index_type="btree",
            order=index.order,
        )

        path = self._index_path(
            table_name,
            index_name,
        )

        path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        BTreePersistence.save(
            index,
            path,
            metadata,
        )

    def load_index(
        self,
        table_name: str,
        index_name: str,
    ) -> Index:
        self._validate_persistence_directory()

        path = self._index_path(
            table_name,
            index_name,
        )

        if not path.exists():
            raise ValueError(
                f"Persistent index does not exist: {index_name}"
            )

        index, metadata = BTreePersistence.load(
            path
        )

        if metadata.table_name != table_name:
            raise ValueError(
                "Persistent index table name does not match."
            )

        if metadata.index_name != index_name:
            raise ValueError(
                "Persistent index name does not match."
            )

        table_indexes = self._indexes.setdefault(
            table_name,
            {},
        )

        if index_name in table_indexes:
            raise ValueError(
                f"Index already exists: {index_name}"
            )

        table_indexes[index_name] = index

        return index

    def load_all(self) -> None:
        if self.persistence_directory is None:
            return

        if not self.persistence_directory.exists():
            return

        for table_directory in sorted(
            self.persistence_directory.iterdir()
        ):
            if not table_directory.is_dir():
                continue

            table_name = table_directory.name

            for index_path in sorted(
                table_directory.glob("*.idx")
            ):
                index_name = index_path.stem

                table_indexes = self._indexes.get(
                    table_name,
                    {},
                )

                if index_name in table_indexes:
                    continue

                self.load_index(
                    table_name,
                    index_name,
                )

    def persist_all(self) -> None:
        if self.persistence_directory is None:
            return

        for table_name in sorted(
            self._indexes
        ):
            for index_name in sorted(
                self._indexes[table_name]
            ):
                index = self._indexes[
                    table_name
                ][index_name]

                if isinstance(
                    index,
                    BPlusTreeIndex,
                ):
                    self.save_index(
                        table_name,
                        index_name,
                    )

    def _index_path(
        self,
        table_name: str,
        index_name: str,
    ) -> Path:
        if self.persistence_directory is None:
            raise ValueError(
                "Persistence directory is not configured."
            )

        return (
            self.persistence_directory
            / table_name
            / f"{index_name}.idx"
        )

    def _delete_persistent_index(
        self,
        table_name: str,
        index_name: str,
    ) -> None:
        if self.persistence_directory is None:
            return

        path = self._index_path(
            table_name,
            index_name,
        )

        if path.exists():
            path.unlink()

        parent = path.parent

        if parent.exists() and not any(
            parent.iterdir()
        ):
            parent.rmdir()

    def _validate_persistence_directory(
        self,
    ) -> None:
        if self.persistence_directory is None:
            raise ValueError(
                "Persistence directory is not configured."
            )

        self.persistence_directory.mkdir(
            parents=True,
            exist_ok=True,
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