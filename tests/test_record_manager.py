import pytest

from jugaaddb.core.schema import Column, Schema
from jugaaddb.storage.file_manager import FileManager
from jugaaddb.storage.record_manager import RecordManager


def make_schema():
    return Schema([
        Column(
            "id",
            "INTEGER",
            primary_key=True,
            nullable=False
        ),
        Column(
            "name",
            "TEXT",
            nullable=False
        ),
        Column(
            "score",
            "FLOAT"
        ),
        Column(
            "active",
            "BOOLEAN"
        ),
    ])


def make_manager(tmp_path):
    path = tmp_path / "records.jdb"

    file_manager = FileManager(
        str(path)
    )

    file_manager.create()

    return RecordManager(
        make_schema(),
        file_manager
    )


def test_insert_returns_record_id(tmp_path):
    manager = make_manager(tmp_path)

    record_id = manager.insert({
        "id": 1,
        "name": "Ayush",
        "score": 95.5,
        "active": True
    })

    assert record_id == (1, 0)


def test_insert_and_read(tmp_path):
    manager = make_manager(tmp_path)

    row = {
        "id": 1,
        "name": "Ayush",
        "score": 95.5,
        "active": True
    }

    record_id = manager.insert(row)

    assert manager.read(record_id) == row


def test_multiple_records_get_different_slots(
    tmp_path
):
    manager = make_manager(tmp_path)

    first = manager.insert({
        "id": 1,
        "name": "Ayush"
    })

    second = manager.insert({
        "id": 2,
        "name": "Rahul"
    })

    assert first == (1, 0)
    assert second == (1, 1)


def test_records_survive_reload(tmp_path):
    path = tmp_path / "records.jdb"

    file_manager = FileManager(
        str(path)
    )

    file_manager.create()

    manager = RecordManager(
        make_schema(),
        file_manager
    )

    row = {
        "id": 101,
        "name": "Persistent",
        "score": 88.5,
        "active": True
    }

    record_id = manager.insert(row)

    reopened_file_manager = FileManager(
        str(path)
    )

    reopened_manager = RecordManager(
        make_schema(),
        reopened_file_manager
    )

    assert reopened_manager.read(
        record_id
    ) == row


def test_delete_record(tmp_path):
    manager = make_manager(tmp_path)

    record_id = manager.insert({
        "id": 1,
        "name": "Ayush"
    })

    manager.delete(record_id)

    with pytest.raises(ValueError):
        manager.read(record_id)


def test_double_delete_rejected(tmp_path):
    manager = make_manager(tmp_path)

    record_id = manager.insert({
        "id": 1,
        "name": "Ayush"
    })

    manager.delete(record_id)

    with pytest.raises(ValueError):
        manager.delete(record_id)


def test_invalid_record_id_rejected(tmp_path):
    manager = make_manager(tmp_path)

    with pytest.raises(TypeError):
        manager.read(123)


def test_header_page_cannot_be_record_page(
    tmp_path
):
    manager = make_manager(tmp_path)

    with pytest.raises(ValueError):
        manager.read((0, 0))


def test_schema_validation_still_applies(
    tmp_path
):
    manager = make_manager(tmp_path)

    with pytest.raises(TypeError):
        manager.insert({
            "id": "wrong",
            "name": "Ayush"
        })


def test_unknown_column_rejected(tmp_path):
    manager = make_manager(tmp_path)

    with pytest.raises(ValueError):
        manager.insert({
            "id": 1,
            "name": "Ayush",
            "unknown": "value"
        })