from pathlib import Path

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


def test_select_reads_physical_storage(
    tmp_path,
):
    db = create_database(tmp_path)

    insert_students(db)

    table = db.table("students")

    assert table.physical_table is not None

    physical_rows = table.physical_table.scan()

    assert physical_rows == [
        (
            table.record_ids[0],
            {
                "id": 1,
                "name": "Sayman",
                "cgpa": 8.5,
            },
        ),
        (
            table.record_ids[1],
            {
                "id": 2,
                "name": "Rahul",
                "cgpa": 9.1,
            },
        ),
    ]

    rows = table.select_all()

    assert rows == [
        {
            "id": 1,
            "name": "Sayman",
            "cgpa": 8.5,
        },
        {
            "id": 2,
            "name": "Rahul",
            "cgpa": 9.1,
        },
    ]


def test_projection_reads_physical_storage(
    tmp_path,
):
    db = create_database(tmp_path)

    insert_students(db)

    result = db.execute(
        "SELECT name, cgpa FROM students"
    )

    assert result == [
        {
            "name": "Sayman",
            "cgpa": 8.5,
        },
        {
            "name": "Rahul",
            "cgpa": 9.1,
        },
    ]


def test_row_by_record_id_reads_physical_storage(
    tmp_path,
):
    db = create_database(tmp_path)

    insert_students(db)

    table = db.table("students")

    record_ids = table.record_ids

    assert table.row_by_record_id(
        record_ids[0]
    ) == {
        "id": 1,
        "name": "Sayman",
        "cgpa": 8.5,
    }

    assert table.row_by_record_id(
        record_ids[1]
    ) == {
        "id": 2,
        "name": "Rahul",
        "cgpa": 9.1,
    }


def test_select_after_reopen_reads_physical_storage(
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

    reopened = Database.open(
        str(path)
    )

    table = reopened.table("students")

    rows = table.select_all()

    assert rows == [
        {
            "id": 1,
            "name": "Sayman",
            "cgpa": 8.5,
        },
        {
            "id": 2,
            "name": "Rahul",
            "cgpa": 9.1,
        },
    ]


def test_physical_delete_excludes_record_from_select(
    tmp_path,
):
    db = create_database(tmp_path)

    insert_students(db)

    table = db.table("students")

    record_ids = table.record_ids

    table.physical_table.delete(
        record_ids[0]
    )

    rows = table.select_all()

    assert rows == [
        {
            "id": 2,
            "name": "Rahul",
            "cgpa": 9.1,
        }
    ]
