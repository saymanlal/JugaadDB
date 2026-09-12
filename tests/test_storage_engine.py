from jugaaddb.storage.constants import PAGE_SIZE
from jugaaddb.storage.engine import StorageEngine


def test_create_binary_database(tmp_path):
    path = tmp_path / "test.jdb"

    storage = StorageEngine(str(path))
    storage.create()

    assert path.exists()
    assert path.stat().st_size >= PAGE_SIZE


def test_load_empty_database(tmp_path):
    path = tmp_path / "test.jdb"

    storage = StorageEngine(str(path))
    storage.create()

    data = storage.load()

    assert data == {
        "catalog": {
            "tables": {}
        }
    }


def test_save_and_load_database(tmp_path):
    path = tmp_path / "test.jdb"

    storage = StorageEngine(str(path))
    storage.create()

    data = {
        "catalog": {
            "tables": {
                "students": {
                    "schema": [],
                    "rows": [
                        {
                            "id": 1,
                            "name": "Ayush"
                        }
                    ]
                }
            }
        }
    }

    storage.save(data)

    loaded = storage.load()

    assert loaded == data


def test_large_payload_spans_multiple_pages(tmp_path):
    path = tmp_path / "test.jdb"

    storage = StorageEngine(str(path))
    storage.create()

    large_text = "JUGAADDB" * 2000

    data = {
        "catalog": {
            "tables": {
                "large_table": {
                    "schema": [],
                    "rows": [
                        {
                            "id": 1,
                            "data": large_text
                        }
                    ]
                }
            }
        }
    }

    storage.save(data)

    assert storage.file_manager.data_page_count() > 1

    loaded = storage.load()

    assert loaded == data


def test_data_survives_storage_engine_reopen(tmp_path):
    path = tmp_path / "test.jdb"

    storage = StorageEngine(str(path))
    storage.create()

    data = {
        "catalog": {
            "tables": {
                "users": {
                    "schema": [],
                    "rows": [
                        {
                            "id": 1,
                            "username": "krushn"
                        }
                    ]
                }
            }
        }
    }

    storage.save(data)

    reopened = StorageEngine(str(path))

    assert reopened.load() == data


def test_corrupted_payload_is_rejected(tmp_path):
    path = tmp_path / "test.jdb"

    storage = StorageEngine(str(path))
    storage.create()

    # Page 1 exists after create().
    page = storage.file_manager.read_page(1)

    page.write(b"\x00\x00\x00\x10corrupted")

    storage.file_manager.write_page(page)

    try:
        storage.load()
    except ValueError as exc:
        assert "Corrupted" in str(exc)
    else:
        raise AssertionError(
            "Corrupted payload should have been rejected."
        )