from pathlib import Path

from .constants import PAGE_SIZE
from .page import Page


class FileManager:
    """
    Low-level manager for fixed-size pages inside a JugaadDB file.

    Responsibilities:
    - Create/open database file
    - Read pages
    - Write pages
    - Allocate new pages
    - Report number of pages

    This layer knows nothing about tables, rows, schemas, or SQL.
    """

    def __init__(self, path: str):
        self.path = Path(path)

    def create(self) -> None:
        """
        Create an empty database file.

        Fails if the file already exists.
        """
        if self.path.exists():
            raise FileExistsError(
                f"Database file already exists: {self.path}"
            )

        self.path.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        self.path.touch()

    def open(self) -> None:
        """
        Open an existing database file.

        The current implementation keeps file access simple
        and opens files per operation.
        """
        if not self.path.exists():
            raise FileNotFoundError(
                f"Database file does not exist: {self.path}"
            )

        if not self.path.is_file():
            raise ValueError(
                f"Database path is not a file: {self.path}"
            )

    def page_count(self) -> int:
        """
        Return the number of complete pages in the file.
        """
        self.open()

        size = self.path.stat().st_size

        if size % PAGE_SIZE != 0:
            raise ValueError(
                "Database file is corrupted: "
                "file size is not aligned to page size."
            )

        return size // PAGE_SIZE

    def read_page(self, page_id: int) -> Page:
        """
        Read a page from disk.
        """
        self._validate_page_id(page_id)
        self.open()

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
        Write a page to disk.

        Existing pages are overwritten.
        New pages extend the file.
        """
        self.open()

        if not isinstance(page, Page):
            raise TypeError(
                "write_page expects a Page instance."
            )

        offset = page.page_id * PAGE_SIZE

        with self.path.open("r+b") as file:
            file.seek(offset)
            file.write(page.read())
            file.flush()

    def allocate_page(self) -> Page:
        """
        Allocate a new empty page at the end of the file.

        Returns the newly allocated Page object.
        """
        self.open()

        page_id = self.page_count()
        page = Page(page_id)

        with self.path.open("ab") as file:
            file.write(page.read())
            file.flush()

        return page

    def _validate_page_id(self, page_id: int) -> None:
        if not isinstance(page_id, int):
            raise TypeError(
                "Page ID must be an integer."
            )

        if page_id < 0:
            raise ValueError(
                "Page ID cannot be negative."
            )