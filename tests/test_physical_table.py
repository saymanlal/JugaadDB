import pytest

from jugaaddb.core.schema import Column, Schema
from jugaaddb.storage.file_manager import FileManager
from jugaaddb.storage.physical_table import PhysicalTable


def make_schema():
    return Schema([
        Column(
            "id",
            "INTEGER",
            primary_key=True,
            nullable=False,
        ),
        Column(
            "name",
            "TEXT",
            nullable=False,
        ),
        Column(
            "cgpa",
            "FLOAT",
        ),
    ])


def make_table(tmp_path):
    path = tmp_path / "students.tbl"

    table = PhysicalTable(
        "students",
        make_schema(),
        FileManager(str(path)),
    )

    table.create()

    return table


def test_create_physical_table(tmp_path):
    table = make_table(tmp_path)

    assert table.path.exists()
    assert table.file_manager.data_page_count() == 0
    assert table.count() == 0


def test_insert_read_and_scan(tmp_path):
    table = make_table(tmp_path)

    first = table.insert({
        "id": 1,
        "name": "Sayman",
        "cgpa": 8.5,
    })

    second = table.insert({
        "id": 2,
        "name": "Rahul",
        "cgpa": 9.1,
    })

    assert first == (1, 0)
    assert second == (1, 1)

    assert table.read(first)["name"] == "Sayman"

    assert table.count() == 2

    assert table.scan() == [
        (
            first,
            {
                "id": 1,
                "name": "Sayman",
                "cgpa": 8.5,
            },
        ),
        (
            second,
            {
                "id": 2,
                "name": "Rahul",
                "cgpa": 9.1,
            },
        ),
    ]


def test_scan_excludes_deleted_records(tmp_path):
    table = make_table(tmp_path)

    first = table.insert({
        "id": 1,
        "name": "Sayman",
    })

    second = table.insert({
        "id": 2,
        "name": "Rahul",
    })

    table.delete(first)

    assert table.count() == 1

    assert table.scan() == [
        (
            second,
            {
                "id": 2,
                "name": "Rahul",
                "cgpa": None,
            },
        )
    ]


def test_physical_table_survives_reopen(tmp_path):
    path = tmp_path / "students.tbl"
    schema = make_schema()

    table = PhysicalTable(
        "students",
        schema,
        FileManager(str(path)),
    )

    table.create()

    record_id = table.insert({
        "id": 101,
        "name": "Persistent",
        "cgpa": 9.2,
    })

    reopened = PhysicalTable(
        "students",
        schema,
        FileManager(str(path)),
    )

    reopened.open()

    assert reopened.read(record_id) == {
        "id": 101,
        "name": "Persistent",
        "cgpa": 9.2,
    }

    assert reopened.count() == 1


def test_duplicate_create_is_rejected(tmp_path):
    path = tmp_path / "students.tbl"
    schema = make_schema()

    first = PhysicalTable(
        "students",
        schema,
        FileManager(str(path)),
    )

    first.create()

    second = PhysicalTable(
        "students",
        schema,
        FileManager(str(path)),
    )

    with pytest.raises(FileExistsError):
        second.create()


def test_invalid_name_is_rejected(tmp_path):
    with pytest.raises(ValueError):
        PhysicalTable(
            "",
            make_schema(),
            FileManager(str(tmp_path / "x.tbl")),
        )


def test_invalid_schema_is_rejected(tmp_path):
    with pytest.raises(TypeError):
        PhysicalTable(
            "students",
            object(),
            FileManager(str(tmp_path / "x.tbl")),
        )


def test_invalid_file_manager_is_rejected(tmp_path):
    with pytest.raises(TypeError):
        PhysicalTable(
            "students",
            make_schema(),
            object(),
        )


def test_schema_validation_is_preserved(tmp_path):
    table = make_table(tmp_path)

    with pytest.raises(TypeError):
        table.insert({
            "id": "wrong",
            "name": "Sayman",
        })


def test_physical_table_uses_multiple_pages(tmp_path):
    table = make_table(tmp_path)

    for index in range(100):
        table.insert({
            "id": index,
            "name": "x" * 80,
        })

    assert table.file_manager.data_page_count() > 1
    assert table.count() == 100
    assert table.read((2, 0))["id"] > 0