from pathlib import Path

import pytest

from jugaaddb.core.database import Database


def create_database(tmp_path: Path):
    db = Database.create(
        str(tmp_path / "students.jdb")
    )

    db.execute(
        "CREATE TABLE students (id INTEGER PRIMARY KEY, name TEXT, cgpa FLOAT)"
    )

    return db


def insert_students(db):
    db.execute(
        "INSERT INTO students (id, name, cgpa) VALUES (1, 'Sayman', 8.5)"
    )

    db.execute(
        "INSERT INTO students (id, name, cgpa) VALUES (2, 'Rahul', 9.1)"
    )

    db.execute(
        "INSERT INTO students (id, name, cgpa) VALUES (3, 'Aman', 8.8)"
    )


def test_physical_delete_removes_record(
    tmp_path,
):
    db = create_database(tmp_path)

    insert_students(db)

    table = db.table("students")
    record_id = table.record_ids[0]

    table.delete(
        {"id": 1}
    )

    assert table.physical_table.count() == 2

    with pytest.raises(ValueError):
        table.physical_table.read(record_id)


def test_physical_delete_preserves_other_records(
    tmp_path,
):
    db = create_database(tmp_path)

    insert_students(db)

    table = db.table("students")

    first_id = table.record_ids[0]
    second_id = table.record_ids[1]
    third_id = table.record_ids[2]

    table.delete(
        {"id": 2}
    )

    assert table.physical_table.read(
        first_id
    ) == {
        "id": 1,
        "name": "Sayman",
        "cgpa": 8.5,
    }

    assert table.physical_table.read(
        third_id
    ) == {
        "id": 3,
        "name": "Aman",
        "cgpa": 8.8,
    }

    assert second_id not in table.record_ids


def test_physical_delete_keeps_remaining_record_ids_stable(
    tmp_path,
):
    db = create_database(tmp_path)

    insert_students(db)

    table = db.table("students")

    first_id = table.record_ids[0]
    second_id = table.record_ids[1]
    third_id = table.record_ids[2]

    table.delete(
        {"id": 2}
    )

    assert table.record_ids == [
        first_id,
        third_id,
    ]

    assert first_id == (1, 0)
    assert second_id == (1, 1)
    assert third_id == (1, 2)


def test_multiple_physical_deletes(
    tmp_path,
):
    db = create_database(tmp_path)

    insert_students(db)

    table = db.table("students")

    table.delete(
        {"id": 1}
    )

    table.delete(
        {"id": 3}
    )

    assert table.physical_table.scan() == [
        (
            table.record_ids[0],
            {
                "id": 2,
                "name": "Rahul",
                "cgpa": 9.1,
            },
        )
    ]


def test_physical_delete_survives_reopen(
    tmp_path,
):
    path = tmp_path / "students.jdb"

    db = Database.create(
        str(path)
    )

    db.execute(
        "CREATE TABLE students (id INTEGER PRIMARY KEY, name TEXT, cgpa FLOAT)"
    )

    insert_students(db)

    db.table("students").delete(
        {"id": 2}
    )

    reopened = Database.open(
        str(path)
    )

    assert reopened.table(
        "students"
    ).select_all() == [
        {
            "id": 1,
            "name": "Sayman",
            "cgpa": 8.5,
        },
        {
            "id": 3,
            "name": "Aman",
            "cgpa": 8.8,
        },
    ]


def test_sql_delete_changes_physical_storage(
    tmp_path,
):
    db = create_database(tmp_path)

    insert_students(db)

    table = db.table("students")
    deleted_id = table.record_ids[0]

    db.execute(
        "DELETE FROM students WHERE id = 1"
    )

    assert table.physical_table.count() == 2

    with pytest.raises(ValueError):
        table.physical_table.read(
            deleted_id
        )


def test_sql_delete_with_and_changes_physical_storage(
    tmp_path,
):
    db = create_database(tmp_path)

    insert_students(db)

    table = db.table("students")
    deleted_id = table.record_ids[0]

    db.execute(
        "DELETE FROM students "
        "WHERE id = 1 AND name = 'Sayman'"
    )

    with pytest.raises(ValueError):
        table.physical_table.read(
            deleted_id
        )


def test_non_matching_delete_does_not_change_physical_storage(
    tmp_path,
):
    db = create_database(tmp_path)

    insert_students(db)

    table = db.table("students")

    before = table.physical_table.scan()

    db.execute(
        "DELETE FROM students WHERE id = 999"
    )

    after = table.physical_table.scan()

    assert after == before


def test_deleted_record_cannot_be_deleted_again(
    tmp_path,
):
    db = create_database(tmp_path)

    insert_students(db)

    table = db.table("students")

    deleted_record_id = table.record_ids[0]

    table.delete(
        {"id": 1}
    )

    with pytest.raises(ValueError):
        table.physical_table.delete(
            deleted_record_id
        )


def test_deleted_record_can_be_restored_with_same_record_id(
    tmp_path,
):
    db = create_database(tmp_path)

    insert_students(db)

    table = db.table("students")

    record_id = table.record_ids[0]

    table.physical_table.delete(
        record_id
    )

    table.physical_table.restore(
        record_id,
        {
            "id": 1,
            "name": "Restored",
            "cgpa": 9.5,
        },
    )

    assert table.physical_table.read(
        record_id
    ) == {
        "id": 1,
        "name": "Restored",
        "cgpa": 9.5,
    }