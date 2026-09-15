from pathlib import Path
from typing import Any

from ..core.schema import Schema
from .buffer_pool import BufferPool
from .file_manager import FileManager
from .record_manager import RecordID, RecordManager


class PhysicalTable:
    def __init__(
        self,
        name: str,
        schema: Schema,
        file_manager: FileManager,
        buffer_pool: BufferPool | None = None,
    ):
        if not isinstance(name, str) or not name.strip():
            raise ValueError(
                "Table name must be a non-empty string."
            )

        if not isinstance(schema, Schema):
            raise TypeError(
                "Physical table requires a Schema."
            )

        if not isinstance(file_manager, FileManager):
            raise TypeError(
                "Physical table requires a FileManager."
            )

        if buffer_pool is not None:
            if not isinstance(buffer_pool, BufferPool):
                raise TypeError(
                    "buffer_pool must be a BufferPool."
                )

            if (
                buffer_pool.file_manager.path
                != file_manager.path
            ):
                raise ValueError(
                    "Buffer pool must use the same FileManager."
                )

        self.name = name
        self.schema = schema
        self.file_manager = file_manager
        self.buffer_pool = buffer_pool

        self.record_manager = RecordManager(
            schema,
            file_manager,
            buffer_pool=buffer_pool,
        )

    @property
    def path(self) -> Path:
        return self.file_manager.path

    def create(self) -> None:
        if self.path.exists():
            raise FileExistsError(
                f"Physical table file already exists: {self.path}"
            )

        self.file_manager.create()

    def open(self) -> None:
        self.file_manager.open()

    def insert(
        self,
        row: dict[str, Any],
    ) -> RecordID:
        return self.record_manager.insert(row)

    def read(
        self,
        record_id: RecordID,
    ) -> dict[str, Any]:
        self._validate_record_id(record_id)

        return self.record_manager.read(
            record_id
        )

    def update(
        self,
        record_id: RecordID,
        row: dict[str, Any],
    ) -> None:
        self._validate_record_id(record_id)

        self.record_manager.update(
            record_id,
            row,
        )

    def delete(
        self,
        record_id: RecordID,
    ) -> None:
        self._validate_record_id(record_id)

        self.record_manager.delete(
            record_id
        )

    def restore(
        self,
        record_id: RecordID,
        row: dict[str, Any],
    ) -> None:
        self._validate_record_id(record_id)

        self.record_manager.restore(
            record_id,
            row,
        )

    def exists(
        self,
        record_id: RecordID,
    ) -> bool:
        self._validate_record_id(record_id)

        try:
            self.record_manager.read(
                record_id
            )
        except ValueError:
            return False

        return True

    def scan(
        self,
    ) -> list[tuple[RecordID, dict[str, Any]]]:
        return self.record_manager.scan()

    def record_ids(self) -> list[RecordID]:
        return [
            record_id
            for record_id, _ in self.scan()
        ]

    def count(self) -> int:
        return self.record_manager.count()

    def flush(self) -> None:
        if self.buffer_pool is not None:
            self.buffer_pool.flush_all()

    def close(self) -> None:
        self.flush()

    def _validate_record_id(
        self,
        record_id: RecordID,
    ) -> None:
        if (
            not isinstance(record_id, tuple)
            or len(record_id) != 2
        ):
            raise TypeError(
                "Record ID must be a (page_id, slot_id) tuple."
            )

        page_id, slot_id = record_id

        if type(page_id) is not int:
            raise TypeError(
                "Page ID must be an integer."
            )

        if type(slot_id) is not int:
            raise TypeError(
                "Slot ID must be an integer."
            )

        if page_id <= 0:
            raise ValueError(
                "Record page ID must be greater than zero."
            )

        if slot_id < 0:
            raise ValueError(
                "Record slot ID cannot be negative."
            )