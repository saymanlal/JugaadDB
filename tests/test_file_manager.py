import pytest

from jugaaddb.storage.constants import PAGE_SIZE
from jugaaddb.storage.file_manager import FileManager


def test_create_file(tmp_path):
    path = tmp_path / "test.jdb"

    manager = FileManager(str(path))

    manager.create()

    assert path.exists()
    assert path.stat().st_size == 0


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


def test_allocate_page(tmp_path):
    path = tmp_path / "test.jdb"

    manager = FileManager(str(path))
    manager.create()

    page = manager.allocate_page()

    assert page.page_id == 0
    assert manager.page_count() == 1
    assert path.stat().st_size == PAGE_SIZE


def test_allocate_multiple_pages(tmp_path):
    path = tmp_path / "test.jdb"

    manager = FileManager(str(path))
    manager.create()

    page0 = manager.allocate_page()
    page1 = manager.allocate_page()
    page2 = manager.allocate_page()

    assert page0.page_id == 0
    assert page1.page_id == 1
    assert page2.page_id == 2

    assert manager.page_count() == 3
    assert path.stat().st_size == PAGE_SIZE * 3


def test_write_and_read_page(tmp_path):
    path = tmp_path / "test.jdb"

    manager = FileManager(str(path))
    manager.create()

    page = manager.allocate_page()

    page.write(b"JUGAADDB")

    manager.write_page(page)

    loaded = manager.read_page(0)

    assert loaded.page_id == 0
    assert loaded.read()[:8] == b"JUGAADDB"


def test_read_missing_page_rejected(tmp_path):
    path = tmp_path / "test.jdb"

    manager = FileManager(str(path))
    manager.create()

    with pytest.raises(ValueError):
        manager.read_page(0)


def test_negative_page_id_rejected(tmp_path):
    path = tmp_path / "test.jdb"

    manager = FileManager(str(path))
    manager.create()

    with pytest.raises(ValueError):
        manager.read_page(-1)


def test_file_size_must_be_page_aligned(tmp_path):
    path = tmp_path / "test.jdb"

    manager = FileManager(str(path))
    manager.create()

    path.write_bytes(b"corrupted")

    with pytest.raises(ValueError):
        manager.page_count()