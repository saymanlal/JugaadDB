from typing import Any

from ..core.schema import Schema
from .buffer_pool import BufferPool
from .constants import PAGE_SIZE
from .file_manager import FileManager
from .page import Page
from .record_codec import RecordCodec
from .slotted_page import SlottedPage


RecordID = tuple[int, int]


class RecordManager:
    def __init__(
        self,
        schema: Schema,
        file_manager: FileManager,
        buffer_pool: BufferPool | None = None,
    ):
        self.schema = schema
        self.file_manager = file_manager
        self.codec = RecordCodec(schema)

        if buffer_pool is not None:
            if not isinstance(
                buffer_pool,
                BufferPool,
            ):
                raise TypeError(
                    "buffer_pool must be a BufferPool."
                )

            if buffer_pool.file_manager.path != (
                file_manager.path
            ):
                raise ValueError(
                    "Buffer pool must use the same FileManager."
                )

        self.buffer_pool = buffer_pool

    def insert(
        self,
        row: dict[str, Any],
    ) -> RecordID:
        record = self.codec.encode(row)

        if len(record) > self._maximum_record_size():
            raise ValueError(
                "Record is too large to fit on a page."
            )

        page = self._find_page_for_record(record)

        slot_id = page.insert(record)

        self._save_page(page)

        return (
            page.page_id,
            slot_id,
        )

    def read(
        self,
        record_id: RecordID,
    ) -> dict[str, Any]:
        page_id, slot_id = self._validate_record_id(
            record_id
        )

        page = self._load_page(page_id)

        if page.is_deleted(slot_id):
            raise ValueError(
                f"Record has been deleted: {record_id}"
            )

        record = page.read(slot_id)

        if not record:
            raise ValueError(
                f"Record does not exist: {record_id}"
            )

        return self.codec.decode(record)

    def update(
        self,
        record_id: RecordID,
        row: dict[str, Any],
    ) -> None:
        page_id, slot_id = self._validate_record_id(
            record_id
        )

        record = self.codec.encode(row)

        if len(record) > self._maximum_record_size():
            raise ValueError(
                "Record is too large to fit on a page."
            )

        page = self._load_page(page_id)

        if page.is_deleted(slot_id):
            raise ValueError(
                f"Record has been deleted: {record_id}"
            )

        page.update(
            slot_id,
            record,
        )

        self._save_page(page)

    def scan(
        self,
    ) -> list[
        tuple[
            RecordID,
            dict[str, Any],
        ]
    ]:
        records = []

        for page_id in range(
            1,
            self.file_manager.page_count(),
        ):
            page = self._load_page(page_id)

            for slot_id in range(
                page.slot_count_total()
            ):
                if page.is_deleted(slot_id):
                    continue

                record = page.read(slot_id)

                if not record:
                    continue

                record_id = (
                    page_id,
                    slot_id,
                )

                records.append(
                    (
                        record_id,
                        self.codec.decode(record),
                    )
                )

        return records

    def count(self) -> int:
        return len(self.scan())

    def delete(
        self,
        record_id: RecordID,
    ) -> None:
        page_id, slot_id = self._validate_record_id(
            record_id
        )

        page = self._load_page(page_id)

        if page.is_deleted(slot_id):
            raise ValueError(
                f"Record has already been deleted: {record_id}"
            )

        page.delete(slot_id)

        self._save_page(page)

    def restore(
        self,
        record_id: RecordID,
        row: dict[str, Any],
    ) -> None:
        page_id, slot_id = self._validate_record_id(
            record_id
        )

        record = self.codec.encode(row)

        if len(record) > self._maximum_record_size():
            raise ValueError(
                "Record is too large to fit on a page."
            )

        page = self._load_page(page_id)

        if not page.is_deleted(slot_id):
            raise ValueError(
                f"Record is not deleted: {record_id}"
            )

        page.restore(
            slot_id,
            record,
        )

        self._save_page(page)

    def _find_page_for_record(
        self,
        record: bytes,
    ) -> SlottedPage:
        required_space = (
            len(record)
            + SlottedPage.SLOT_SIZE
        )

        for page_id in range(
            1,
            self.file_manager.page_count(),
        ):
            page = self._load_page(page_id)

            if page.free_space() >= required_space:
                return page

        return self._allocate_page()

    def _allocate_page(self) -> SlottedPage:
        if self.buffer_pool is not None:
            physical_page = (
                self.buffer_pool.new_page()
            )
        else:
            physical_page = (
                self.file_manager.allocate_page()
            )

        return SlottedPage.from_bytes(
            physical_page.page_id,
            physical_page.read(),
        )

    def _load_page(
        self,
        page_id: int,
    ) -> SlottedPage:
        if self.buffer_pool is not None:
            physical_page = (
                self.buffer_pool.fetch(
                    page_id
                )
            )
        else:
            physical_page = (
                self.file_manager.read_page(
                    page_id
                )
            )

        return SlottedPage.from_bytes(
            page_id,
            physical_page.read(),
        )

    def _save_page(
        self,
        page: SlottedPage,
    ) -> None:
        physical_page = Page(
            page.page_id,
            page.to_bytes(),
        )

        if self.buffer_pool is not None:
            self.buffer_pool.store(
                physical_page
            )
        else:
            self.file_manager.write_page(
                physical_page
            )

    def _validate_record_id(
        self,
        record_id: RecordID,
    ) -> RecordID:
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

        return (
            page_id,
            slot_id,
        )

    def _maximum_record_size(self) -> int:
        return (
            PAGE_SIZE
            - SlottedPage.HEADER_SIZE
            - SlottedPage.SLOT_SIZE
        )