from typing import Any

from ..core.schema import Schema
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
        file_manager: FileManager
    ):
        self.schema = schema
        self.file_manager = file_manager
        self.codec = RecordCodec(schema)

    def insert(
        self,
        row: dict[str, Any]
    ) -> RecordID:

        record = self.codec.encode(row)

        if len(record) > self._maximum_record_size():
            raise ValueError(
                "Record is too large to fit on a page."
            )

        page = self._find_page_for_record(
            record
        )

        slot_id = page.insert(record)

        self._save_page(page)

        return (
            page.page_id,
            slot_id
        )

    def read(
        self,
        record_id: RecordID
    ) -> dict[str, Any]:

        page_id, slot_id = self._validate_record_id(
            record_id
        )

        page = self._load_page(
            page_id
        )

        if page.is_deleted(slot_id):
            raise ValueError(
                f"Record has been deleted: "
                f"{record_id}"
            )

        record = page.read(slot_id)

        if not record:
            raise ValueError(
                f"Record does not exist: "
                f"{record_id}"
            )

        return self.codec.decode(record)

    def delete(
        self,
        record_id: RecordID
    ) -> None:

        page_id, slot_id = self._validate_record_id(
            record_id
        )

        page = self._load_page(
            page_id
        )

        if page.is_deleted(slot_id):
            raise ValueError(
                f"Record has already been deleted: "
                f"{record_id}"
            )

        page.delete(slot_id)

        self._save_page(page)

    def _find_page_for_record(
        self,
        record: bytes
    ) -> SlottedPage:

        required_space = (
            len(record)
            + SlottedPage.SLOT_SIZE
        )

        for page_id in range(
            1,
            self.file_manager.page_count()
        ):
            page = self._load_page(
                page_id
            )

            if page.free_space() >= required_space:
                return page

        return self._allocate_page()

    def _allocate_page(self) -> SlottedPage:

        physical_page = (
            self.file_manager.allocate_page()
        )

        return SlottedPage.from_bytes(
            physical_page.page_id,
            physical_page.read()
        )

    def _load_page(
        self,
        page_id: int
    ) -> SlottedPage:

        physical_page = (
            self.file_manager.read_page(
                page_id
            )
        )

        return SlottedPage.from_bytes(
            page_id,
            physical_page.read()
        )

    def _save_page(
        self,
        page: SlottedPage
    ) -> None:

        physical_page = Page(
            page.page_id,
            page.to_bytes()
        )

        self.file_manager.write_page(
            physical_page
        )

    def _validate_record_id(
        self,
        record_id: RecordID
    ) -> RecordID:

        if (
            not isinstance(record_id, tuple)
            or len(record_id) != 2
        ):
            raise TypeError(
                "Record ID must be a "
                "(page_id, slot_id) tuple."
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

        return page_id, slot_id

    def _maximum_record_size(self) -> int:
        return (
            PAGE_SIZE
            - SlottedPage.HEADER_SIZE
            - SlottedPage.SLOT_SIZE
        )