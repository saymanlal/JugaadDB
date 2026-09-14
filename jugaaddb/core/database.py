from pathlib import Path
from typing import Any

from .schema import Column, Schema
from ..indexing.manager import IndexManager
from ..relational.table import Table
from ..storage.engine import StorageEngine


class Database:
    def __init__(
        self,
        path: str,
        storage: StorageEngine,
        data: dict[str, Any],
        index_manager: IndexManager | None = None,
    ):
        self.path = Path(path)
        self.storage = storage
        self.data = data
        self.index_manager = (
            index_manager
            if index_manager is not None
            else IndexManager()
        )

    @classmethod
    def create(
        cls,
        path: str,
    ) -> "Database":
        storage = StorageEngine(path)
        storage.create()
        data = storage.load()

        return cls(
            path,
            storage,
            data,
        )

    @classmethod
    def open(
        cls,
        path: str,
    ) -> "Database":
        storage = StorageEngine(path)
        data = storage.load()

        return cls(
            path,
            storage,
            data,
        )

    def create_table(
        self,
        name: str,
        columns: list[Column],
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
            "rows": [],
            "record_ids": [],
        }

        self._save()

        return Table(
            name,
            schema,
            tables[name],
            self._save,
            self.index_manager,
        )

    def table(
        self,
        name: str,
    ) -> Table:
        tables = self.data["catalog"]["tables"]

        if name not in tables:
            raise ValueError(
                f"Table does not exist: {name}"
            )

        table_data = tables[name]

        schema = Schema(
            [
                Column(
                    name=column["name"],
                    data_type=column["data_type"],
                    primary_key=column["primary_key"],
                    nullable=column["nullable"],
                    unique=column["unique"],
                )
                for column in table_data["schema"]
            ]
        )

        return Table(
            name,
            schema,
            table_data,
            self._save,
            self.index_manager,
        )

    def execute(
        self,
        sql: str,
    ):
        from ..sql.executor import Executor
        from ..sql.lexer import Lexer
        from ..sql.parser import Parser
        from ..sql.planner import Planner

        if not isinstance(sql, str):
            raise TypeError(
                "SQL query must be a string."
            )

        if not sql.strip():
            raise ValueError(
                "SQL query cannot be empty."
            )

        tokens = Lexer(sql).tokenize()
        statement = Parser(tokens).parse()
        plan = Planner(self).plan(statement)

        return Executor(self).execute(
            plan
        )

    def _save(self) -> None:
        self.storage.save(
            self.data
        )