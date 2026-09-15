from pathlib import Path
from typing import Any

from .catalog import Catalog
from .schema import Column, Schema
from ..indexing.manager import IndexManager
from ..relational.table import Table
from ..storage.buffer_pool import BufferPool
from ..storage.engine import StorageEngine
from ..storage.file_manager import FileManager
from ..storage.physical_table import PhysicalTable


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
            else IndexManager(
                self._index_directory()
            )
        )

        self.catalog = Catalog(
            self.data["catalog"]
        )

        self._physical_tables = {}
        self._buffer_pools = {}

        self._connect_physical_tables()
        self.index_manager.load_all()

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
        schema = Schema(columns)

        physical_path = str(
            self._physical_table_path(name)
        )

        table_data = self.catalog.create_table(
            name,
            schema,
            physical_path,
        )

        physical_file_manager = FileManager(
            physical_path
        )

        physical_table = PhysicalTable(
            name,
            schema,
            physical_file_manager,
        )

        try:
            physical_table.create()
        except Exception:
            del self.catalog.tables[name]
            raise

        buffer_pool = BufferPool(
            physical_file_manager
        )

        physical_table = PhysicalTable(
            name,
            schema,
            physical_file_manager,
            buffer_pool=buffer_pool,
        )

        self._physical_tables[name] = (
            physical_table
        )

        self._buffer_pools[name] = (
            buffer_pool
        )

        try:
            self._save()
        except Exception:
            self._physical_tables.pop(
                name,
                None,
            )

            self._buffer_pools.pop(
                name,
                None,
            )

            try:
                physical_table.close()
            finally:
                self.catalog.tables.pop(
                    name,
                    None,
                )

            raise

        return Table(
            name,
            schema,
            table_data,
            self._save,
            self.index_manager,
            physical_table=physical_table,
        )

    def table(
        self,
        name: str,
    ) -> Table:
        table_data = self.catalog.get(
            name
        )

        schema = self.catalog.schema(
            name
        )

        physical_table = (
            self._get_or_create_physical_table(
                name,
                schema,
            )
        )

        return Table(
            name,
            schema,
            table_data,
            self._save,
            self.index_manager,
            physical_table=physical_table,
        )

    def tables(self) -> list[str]:
        return sorted(
            self.catalog.tables.keys()
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

        plan = Planner(self).plan(
            statement
        )

        return Executor(self).execute(
            plan
        )

    def flush(self) -> None:
        for buffer_pool in (
            self._buffer_pools.values()
        ):
            buffer_pool.flush_all()

        self.index_manager.persist_all()

    def close(self) -> None:
        self.flush()

        for physical_table in (
            self._physical_tables.values()
        ):
            physical_table.close()

        self._physical_tables.clear()
        self._buffer_pools.clear()

    def _connect_physical_tables(self) -> None:
        for name in self.catalog.tables:
            try:
                schema = self.catalog.schema(
                    name
                )

                physical_table = (
                    self._get_or_create_physical_table(
                        name,
                        schema,
                    )
                )

                self._physical_tables[name] = (
                    physical_table
                )

            except Exception:
                self._physical_tables.pop(
                    name,
                    None,
                )

                self._buffer_pools.pop(
                    name,
                    None,
                )

                raise

    def _get_or_create_physical_table(
        self,
        name: str,
        schema: Schema,
    ) -> PhysicalTable:
        existing = self._physical_tables.get(
            name
        )

        if existing is not None:
            return existing

        table_data = self.catalog.get(
            name
        )

        physical = table_data.get(
            "physical"
        )

        if isinstance(
            physical,
            dict,
        ):
            stored_path = physical.get(
                "path"
            )
        else:
            stored_path = None

        if not isinstance(
            stored_path,
            str,
        ) or not stored_path.strip():
            physical_path = (
                self._physical_table_path(name)
            )

            self.catalog.ensure_physical_metadata(
                name,
                str(physical_path),
            )
        else:
            physical_path = Path(
                stored_path
            )

            if not physical_path.is_absolute():
                physical_path = (
                    self.path.parent
                    / physical_path
                )

        physical_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        file_manager = FileManager(
            str(physical_path)
        )

        if physical_path.exists():
            file_manager.open()
        else:
            file_manager.create()

        buffer_pool = BufferPool(
            file_manager
        )

        physical_table = PhysicalTable(
            name,
            schema,
            file_manager,
            buffer_pool=buffer_pool,
        )

        self._buffer_pools[name] = (
            buffer_pool
        )

        self._physical_tables[name] = (
            physical_table
        )

        return physical_table

    def _physical_table_directory(
        self,
    ) -> Path:
        return Path(
            f"{self.path}.tables"
        )

    def _physical_table_path(
        self,
        name: str,
    ) -> Path:
        return (
            self._physical_table_directory()
            / f"{name}.tbl"
        )

    def _index_directory(
        self,
    ) -> Path:
        return Path(
            f"{self.path}.indexes"
        )

    def _save(self) -> None:
        self.storage.save(
            self.data
        )