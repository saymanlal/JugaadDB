from pathlib import Path
import struct

from .constants import (
    FILE_MAGIC,
    FILE_VERSION,
    HEADER_SIZE,
    PAGE_SIZE,
)
from .page import Page


class FileManager:
    """
    Low-level fixed-page file manager for JugaadDB.

    File layout:

        Page 0
        ┌──────────────────────────────┐
        │ File Header                 │
        │                              │
        │ magic                       │
        │ version                     │
        │ reserved                    │
        ├──────────────────────────────┤
        │ Page Data                   │
        │                              │
        │ ...                         │
        └──────────────────────────────┘

    Page 0 is reserved for the database file header.
    User/data pages start from page 1.
    """

    def __init__(self, path: str):
        self.path = Path(path)

    def create(self) -> None:
        """
        Create a new JugaadDB file with a valid header.
        """

        if self.path.exists():
            raise FileExistsError(
                f"Database file already exists: {self.path}"
            )

        self.path.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        header = self._build_header()

        # Page 0 contains header + zero padding.
        page_zero = bytearray(PAGE_SIZE)
        page_zero[:HEADER_SIZE] = header

        with self.path.open("wb") as file:
            file.write(page_zero)
            file.flush()

    def open(self) -> None:
        """
        Validate that an existing file is a JugaadDB file.
        """

        if not self.path.exists():
            raise FileNotFoundError(
                f"Database file does not exist: {self.path}"
            )

        if not self.path.is_file():
            raise ValueError(
                f"Database path is not a file: {self.path}"
            )

        if self.path.stat().st_size < PAGE_SIZE:
            raise ValueError(
                "Invalid JugaadDB file: file is too small."
            )

        if self.path.stat().st_size % PAGE_SIZE != 0:
            raise ValueError(
                "Invalid JugaadDB file: "
                "file size is not page aligned."
            )

        self._validate_header()

    def page_count(self) -> int:
        """
        Return total number of physical pages.

        Page 0 is the file header page.
        """

        self.open()

        return self.path.stat().st_size // PAGE_SIZE

    def data_page_count(self) -> int:
        """
        Return number of pages available for actual data.

        Page 0 is reserved for the header.
        """

        return max(0, self.page_count() - 1)

    def read_page(self, page_id: int) -> Page:
        """
        Read a physical page from disk.

        Page 0 is the header page and cannot be returned
        as a normal Page object.
        """

        self._validate_page_id(page_id)
        self.open()

        if page_id == 0:
            raise ValueError(
                "Page 0 is reserved for the file header."
            )

        if page_id >= self.page_count():
            raise ValueError(
                f"Page does not exist: {page_id}"
            )

        offset = page_id * PAGE_SIZE

        with self.path.open("rb") as file:
            file.seek(offset)
            data = file.read(PAGE_SIZE)

        if len(data) != PAGE_SIZE:
            raise ValueError(
                f"Could not read complete page: {page_id}"
            )

        return Page(page_id, data)

    def write_page(self, page: Page) -> None:
        """
        Write an existing physical page to disk.
        """

        self.open()

        if not isinstance(page, Page):
            raise TypeError(
                "write_page expects a Page instance."
            )

        if page.page_id == 0:
            raise ValueError(
                "Page 0 is reserved for the file header."
            )

        if page.page_id >= self.page_count():
            raise ValueError(
                f"Cannot overwrite non-existent page: "
                f"{page.page_id}"
            )

        offset = page.page_id * PAGE_SIZE

        with self.path.open("r+b") as file:
            file.seek(offset)
            file.write(page.read())
            file.flush()

    def allocate_page(self) -> Page:
        """
        Allocate a new data page at the end of the file.
        """

        self.open()

        page_id = self.page_count()

        page = Page(page_id)

        with self.path.open("ab") as file:
            file.write(page.read())
            file.flush()

        return page

    def _build_header(self) -> bytes:
        """
        Build the fixed-size file header.
        """

        header = bytearray(HEADER_SIZE)

        header[:len(FILE_MAGIC)] = FILE_MAGIC

        # One unsigned byte for format version.
        header[8] = FILE_VERSION

        return bytes(header)

    def _validate_header(self) -> None:
        """
        Validate file magic and format version.
        """

        with self.path.open("rb") as file:
            header = file.read(HEADER_SIZE)

        magic = header[:len(FILE_MAGIC)]
        version = header[8]

        if magic != FILE_MAGIC:
            raise ValueError(
                "Invalid JugaadDB file: bad magic."
            )

        if version != FILE_VERSION:
            raise ValueError(
                f"Unsupported JugaadDB file version: {version}"
            )

    def _validate_page_id(self, page_id: int) -> None:
        if not isinstance(page_id, int):
            raise TypeError(
                "Page ID must be an integer."
            )

        if page_id < 0:
            raise ValueError(
                "Page ID cannot be negative."
            )