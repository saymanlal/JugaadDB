import struct

from .constants import PAGE_SIZE


class SlottedPage:
    HEADER_FORMAT = ">HH"
    HEADER_SIZE = struct.calcsize(HEADER_FORMAT)

    SLOT_FORMAT = ">HH"
    SLOT_SIZE = struct.calcsize(SLOT_FORMAT)

    def __init__(self, page_id: int):
        if type(page_id) is not int:
            raise TypeError(
                "Page ID must be an integer."
            )

        if page_id < 0:
            raise ValueError(
                "Page ID cannot be negative."
            )

        self.page_id = page_id
        self.data = bytearray(PAGE_SIZE)
        self.slot_count = 0
        self.free_space_start = self.HEADER_SIZE

        self._write_header()

    @classmethod
    def from_bytes(
        cls,
        page_id: int,
        data: bytes
    ) -> "SlottedPage":

        if type(page_id) is not int:
            raise TypeError(
                "Page ID must be an integer."
            )

        if page_id < 0:
            raise ValueError(
                "Page ID cannot be negative."
            )

        if not isinstance(data, bytes):
            raise TypeError(
                "Page data must be bytes."
            )

        if len(data) != PAGE_SIZE:
            raise ValueError(
                f"Page must contain exactly "
                f"{PAGE_SIZE} bytes."
            )

        if data == b"\x00" * PAGE_SIZE:
            return cls(page_id)

        page = cls.__new__(cls)

        page.page_id = page_id
        page.data = bytearray(data)

        (
            page.slot_count,
            page.free_space_start
        ) = struct.unpack_from(
            cls.HEADER_FORMAT,
            page.data,
            0
        )

        if page.free_space_start < cls.HEADER_SIZE:
            raise ValueError(
                "Corrupted slotted page: "
                "invalid free space pointer."
            )

        if page.free_space_start > PAGE_SIZE:
            raise ValueError(
                "Corrupted slotted page: "
                "free space pointer exceeds page size."
            )

        slot_directory_start = (
            PAGE_SIZE
            - (page.slot_count * cls.SLOT_SIZE)
        )

        if slot_directory_start < page.free_space_start:
            raise ValueError(
                "Corrupted slotted page: "
                "slot directory overlaps record area."
            )

        return page

    def to_bytes(self) -> bytes:
        return bytes(self.data)

    def insert(self, record: bytes) -> int:
        if not isinstance(record, bytes):
            raise TypeError(
                "Record must be bytes."
            )

        required_space = (
            len(record)
            + self.SLOT_SIZE
        )

        if required_space > self.free_space():
            raise ValueError(
                "Not enough free space on page."
            )

        record_offset = self.free_space_start

        self.data[
            record_offset:
            record_offset + len(record)
        ] = record

        slot_id = self.slot_count

        slot_offset = (
            PAGE_SIZE
            - ((slot_id + 1) * self.SLOT_SIZE)
        )

        struct.pack_into(
            self.SLOT_FORMAT,
            self.data,
            slot_offset,
            record_offset,
            len(record)
        )

        self.slot_count += 1
        self.free_space_start += len(record)

        self._write_header()

        return slot_id

    def read(self, slot_id: int) -> bytes:
        self._validate_slot_id(slot_id)

        offset, length = self._read_slot(
            slot_id
        )

        if length == 0:
            return b""

        return bytes(
            self.data[
                offset:
                offset + length
            ]
        )

    def delete(self, slot_id: int) -> None:
        self._validate_slot_id(slot_id)

        if self.is_deleted(slot_id):
            raise ValueError(
                f"Record has already been deleted: "
                f"slot {slot_id}"
            )

        slot_offset = (
            PAGE_SIZE
            - ((slot_id + 1) * self.SLOT_SIZE)
        )

        offset, _ = self._read_slot(
            slot_id
        )

        struct.pack_into(
            self.SLOT_FORMAT,
            self.data,
            slot_offset,
            offset,
            0
        )

    def slot_count_total(self) -> int:
        return self.slot_count

    def free_space(self) -> int:
        slot_directory_start = (
            PAGE_SIZE
            - (self.slot_count * self.SLOT_SIZE)
        )

        return max(
            0,
            slot_directory_start
            - self.free_space_start
        )

    def is_deleted(self, slot_id: int) -> bool:
        self._validate_slot_id(slot_id)

        _, length = self._read_slot(
            slot_id
        )

        return length == 0

    def _read_slot(
        self,
        slot_id: int
    ) -> tuple[int, int]:

        slot_offset = (
            PAGE_SIZE
            - ((slot_id + 1) * self.SLOT_SIZE)
        )

        return struct.unpack_from(
            self.SLOT_FORMAT,
            self.data,
            slot_offset
        )

    def _write_header(self) -> None:
        struct.pack_into(
            self.HEADER_FORMAT,
            self.data,
            0,
            self.slot_count,
            self.free_space_start
        )

    def _validate_slot_id(
        self,
        slot_id: int
    ) -> None:

        if type(slot_id) is not int:
            raise TypeError(
                "Slot ID must be an integer."
            )

        if slot_id < 0:
            raise ValueError(
                "Slot ID cannot be negative."
            )

        if slot_id >= self.slot_count:
            raise ValueError(
                f"Slot does not exist: {slot_id}"
            )