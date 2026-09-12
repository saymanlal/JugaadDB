import pytest

from jugaaddb.core.schema import Column, Schema
from jugaaddb.relational.table import Table


def create_students_table(save_callback=None):
    schema = Schema([
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
            "cgpa",
            "FLOAT"
        )
    ])

    storage = {
        "rows": []
    }

    return Table(
        "students",
        schema,
        storage,
        save_callback
    )


def test_insert():
    table = create_students_table()

    table.insert({
        "id": 1,
        "name": "Sayman",
        "cgpa": 8.5
    })

    assert len(table.rows) == 1
    assert table.rows[0]["name"] == "Sayman"


def test_duplicate_primary_key_rejected():
    table = create_students_table()

    table.insert({
        "id": 1,
        "name": "Sayman",
        "cgpa": 8.5
    })

    with pytest.raises(ValueError):
        table.insert({
            "id": 1,
            "name": "Rahul",
            "cgpa": 9.1
        })


def test_update():
    table = create_students_table()

    table.insert({
        "id": 1,
        "name": "Sayman",
        "cgpa": 8.5
    })

    updated = table.update(
        {"id": 1},
        {"cgpa": 9.0}
    )

    assert updated == 1
    assert table.rows[0]["cgpa"] == 9.0


def test_update_non_existing_row():
    table = create_students_table()

    updated = table.update(
        {"id": 999},
        {"name": "Nobody"}
    )

    assert updated == 0


def test_delete():
    table = create_students_table()

    table.insert({
        "id": 1,
        "name": "Sayman",
        "cgpa": 8.5
    })

    deleted = table.delete({
        "id": 1
    })

    assert deleted == 1
    assert table.rows == []


def test_delete_non_existing_row():
    table = create_students_table()

    deleted = table.delete({
        "id": 999
    })

    assert deleted == 0


def test_update_primary_key_collision_rejected():
    table = create_students_table()

    table.insert({
        "id": 1,
        "name": "Sayman",
        "cgpa": 8.5
    })

    table.insert({
        "id": 2,
        "name": "Rahul",
        "cgpa": 9.1
    })

    with pytest.raises(ValueError):
        table.update(
            {"id": 1},
            {"id": 2}
        )

    # Original data must remain untouched.
    assert table.rows[0]["id"] == 1
    assert table.rows[1]["id"] == 2


def test_update_unknown_column_rejected():
    table = create_students_table()

    with pytest.raises(ValueError):
        table.update(
            {"id": 1},
            {"unknown": "value"}
        )


def test_delete_unknown_column_rejected():
    table = create_students_table()

    with pytest.raises(ValueError):
        table.delete({
            "unknown": 123
        })


def test_save_callback_called_after_insert():
    calls = []

    def save():
        calls.append("saved")

    table = create_students_table(save)

    table.insert({
        "id": 1,
        "name": "Sayman",
        "cgpa": 8.5
    })

    assert calls == ["saved"]