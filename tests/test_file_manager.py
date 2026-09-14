import pytest

from jugaaddb.storage.constants import (
    FILE_MAGIC,
    FILE_VERSION,
    HEADER_SIZE,
    PAGE_SIZE,
)
from jugaaddb.storage.file_manager import FileManager


def test_create_file_with_header(tmp_path):
    path = tmp_path / "test.jdb"

    manager = FileManager(str(path))
    manager.create()

    assert path.exists()
    assert path.stat().st_size == PAGE_SIZE

    with path.open("rb") as file:
        header = file.read(HEADER_SIZE)

    assert header[:len(FILE_MAGIC)] == FILE_MAGIC
    assert header[8] == FILE_VERSION


def test_create_existing_file_rejected(tmp_path):
    path = tmp_path / "test.jdb"

    manager = FileManager(str(path))
    manager.create()

    with pytest.raises(FileExistsError):
        manager.create()


def test_open_missing_file_rejected(tmp_path):
    path = tmp_path / "missing.jdb"

    manager = FileManager(str(path))

    with pytest.raises(FileNotFoundError):
        manager.open()


def test_page_count_after_create(tmp_path):
    path = tmp_path / "test.jdb"

    manager = FileManager(str(path))
    manager.create()

    assert manager.page_count() == 1
    assert manager.data_page_count() == 0


def test_allocate_page(tmp_path):
    path = tmp_path / "test.jdb"

    manager = FileManager(str(path))
    manager.create()

    page = manager.allocate_page()

    assert page.page_id == 1
    assert manager.page_count() == 2
    assert manager.data_page_count() == 1
    assert path.stat().st_size == PAGE_SIZE * 2


def test_allocate_multiple_pages(tmp_path):
    path = tmp_path / "test.jdb"

    manager = FileManager(str(path))
    manager.create()

    page1 = manager.allocate_page()
    page2 = manager.allocate_page()
    page3 = manager.allocate_page()

    assert page1.page_id == 1
    assert page2.page_id == 2
    assert page3.page_id == 3

    assert manager.page_count() == 4
    assert manager.data_page_count() == 3
    assert path.stat().st_size == PAGE_SIZE * 4


def test_write_and_read_page(tmp_path):
    path = tmp_path / "test.jdb"

    manager = FileManager(str(path))
    manager.create()

    page = manager.allocate_page()

    page.write(b"JUGAADDB")

    manager.write_page(page)

    loaded = manager.read_page(1)

    assert loaded.page_id == 1
    assert loaded.read()[:8] == b"JUGAADDB"


def test_read_header_page_rejected(tmp_path):
    path = tmp_path / "test.jdb"

    manager = FileManager(str(path))
    manager.create()

    with pytest.raises(ValueError):
        manager.read_page(0)


def test_read_missing_page_rejected(tmp_path):
    path = tmp_path / "test.jdb"

    manager = FileManager(str(path))
    manager.create()

    with pytest.raises(ValueError):
        manager.read_page(1)


def test_negative_page_id_rejected(tmp_path):
    path = tmp_path / "test.jdb"

    manager = FileManager(str(path))
    manager.create()

    with pytest.raises(ValueError):
        manager.read_page(-1)


def test_invalid_magic_rejected(tmp_path):
    path = tmp_path / "test.jdb"

    manager = FileManager(str(path))
    manager.create()

    with path.open("r+b") as file:
        file.seek(0)
        file.write(b"INVALID!")

    with pytest.raises(ValueError):
        manager.open()


def test_invalid_version_rejected(tmp_path):
    path = tmp_path / "test.jdb"

    manager = FileManager(str(path))
    manager.create()

    with path.open("r+b") as file:
        file.seek(8)
        file.write(b"\xff")

    with pytest.raises(ValueError):
        manager.open()


def test_file_size_must_be_page_aligned(tmp_path):
    path = tmp_path / "test.jdb"

    manager = FileManager(str(path))
    manager.create()

    with path.open("ab") as file:
        file.write(b"corrupted")

    with pytest.raises(ValueError):
        manager.page_count()