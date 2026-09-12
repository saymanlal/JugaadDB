from pathlib import Path
from typing import Any

from .schema import Column, Schema
from ..storage.engine import StorageEngine
from ..relational.table import Table


class Database:
    def __init__(
        self,
        path: str,
        storage: StorageEngine,
        data: dict[str, Any]
    ):
        self.path = Path(path)
        self.storage = storage
        self.data = data

    @classmethod
    def create(cls, path: str) -> "Database":
        storage = StorageEngine(path)
        storage.create()

        data = storage.load()

        return cls(path, storage, data)

    @classmethod
    def open(cls, path: str) -> "Database":
        storage = StorageEngine(path)
        data = storage.load()

        return cls(path, storage, data)

    def create_table(
        self,
        name: str,
        columns: list[Column]
    ) -> Table:

        tables = self.data["catalog"]["tables"]

        if name in tables:
            raise ValueError(
                f"Table already exists: {name}"
            )

        schema = Schema(columns)

        tables[name] = {
            "schema": [
                {
                    "name": column.name,
                    "data_type": column.data_type,
                    "primary_key": column.primary_key,
                    "nullable": column.nullable,
                    "unique": column.unique,
                }
                for column in schema.columns
            ],
            "rows": []
        }

        self._save()

        return Table(
           name,
           schema,
           tables[name],
           self._save
         )

    def table(self, name: str) -> Table:
        tables = self.data["catalog"]["tables"]

        if name not in tables:
            raise ValueError(
                f"Table does not exist: {name}"
            )

        table_data = tables[name]

        schema = Schema([
            Column(
                name=column["name"],
                data_type=column["data_type"],
                primary_key=column["primary_key"],
                nullable=column["nullable"],
                unique=column["unique"],
            )
            for column in table_data["schema"]
        ])

        return Table(
           name,
           schema,
           tables[name],
           self._save
         )

    def _save(self) -> None:
        self.storage.save(self.data)