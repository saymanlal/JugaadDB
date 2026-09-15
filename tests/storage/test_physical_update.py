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


def test_physical_update_changes_stored_record(
    tmp_path,
):
    db = create_database(tmp_path)

    insert_students(db)

    table = db.table("students")
    record_id = table.record_ids[0]

    table.update(
        {"id": 1},
        {
            "id": 1,
            "name": "Sayman Updated",
            "cgpa": 9.9,
        },
    )

    assert table.physical_table.read(
        record_id
    ) == {
        "id": 1,
        "name": "Sayman Updated",
        "cgpa": 9.9,
    }


def test_physical_update_preserves_record_id(
    tmp_path,
):
    db = create_database(tmp_path)

    insert_students(db)

    table = db.table("students")

    first_id = table.record_ids[0]
    second_id = table.record_ids[1]

    table.update(
        {"id": 1},
        {
            "id": 1,
            "name": "Changed",
            "cgpa": 9.7,
        },
    )

    assert table.record_ids == [
        first_id,
        second_id,
    ]


def test_physical_update_can_grow_record(
    tmp_path,
):
    db = create_database(tmp_path)

    db.execute(
        "INSERT INTO students (id, name, cgpa) VALUES (1, 'A', 8.5)"
    )

    table = db.table("students")
    record_id = table.record_ids[0]

    long_name = "A" * 500

    table.update(
        {"id": 1},
        {
            "id": 1,
            "name": long_name,
            "cgpa": 8.5,
        },
    )

    assert table.physical_table.read(
        record_id
    ) == {
        "id": 1,
        "name": long_name,
        "cgpa": 8.5,
    }


def test_physical_update_can_shrink_record(
    tmp_path,
):
    db = create_database(tmp_path)

    long_name = "A" * 500

    db.execute(
        f"INSERT INTO students (id, name, cgpa) VALUES (1, '{long_name}', 8.5)"
    )

    table = db.table("students")
    record_id = table.record_ids[0]

    table.update(
        {"id": 1},
        {
            "id": 1,
            "name": "A",
            "cgpa": 8.5,
        },
    )

    assert table.physical_table.read(
        record_id
    ) == {
        "id": 1,
        "name": "A",
        "cgpa": 8.5,
    }


def test_physical_update_preserves_other_records(
    tmp_path,
):
    db = create_database(tmp_path)

    insert_students(db)

    table = db.table("students")

    first_id = table.record_ids[0]
    second_id = table.record_ids[1]

    table.update(
        {"id": 1},
        {
            "id": 1,
            "name": "Changed",
            "cgpa": 10.0,
        },
    )

    assert table.physical_table.read(
        first_id
    ) == {
        "id": 1,
        "name": "Changed",
        "cgpa": 10.0,
    }

    assert table.physical_table.read(
        second_id
    ) == {
        "id": 2,
        "name": "Rahul",
        "cgpa": 9.1,
    }


def test_multiple_physical_updates_persist(
    tmp_path,
):
    db = create_database(tmp_path)

    insert_students(db)

    table = db.table("students")
    record_id = table.record_ids[0]

    table.update(
        {"id": 1},
        {
            "id": 1,
            "name": "First",
            "cgpa": 8.8,
        },
    )

    table.update(
        {"id": 1},
        {
            "id": 1,
            "name": "Second",
            "cgpa": 9.2,
        },
    )

    table.update(
        {"id": 1},
        {
            "id": 1,
            "name": "Final",
            "cgpa": 9.9,
        },
    )

    assert table.physical_table.read(
        record_id
    ) == {
        "id": 1,
        "name": "Final",
        "cgpa": 9.9,
    }


def test_physical_update_survives_reopen(
    tmp_path,
):
    path = tmp_path / "students.jdb"

    db = Database.create(
        str(path)
    )

    db.execute(
        "CREATE TABLE students (id INTEGER PRIMARY KEY, name TEXT, cgpa FLOAT)"
    )

    db.execute(
        "INSERT INTO students (id, name, cgpa) VALUES (1, 'Sayman', 8.5)"
    )

    table = db.table("students")

    table.update(
        {"id": 1},
        {
            "id": 1,
            "name": "Persisted",
            "cgpa": 9.8,
        },
    )

    reopened = Database.open(
        str(path)
    )

    assert reopened.table(
        "students"
    ).select_all() == [
        {
            "id": 1,
            "name": "Persisted",
            "cgpa": 9.8,
        }
    ]


def test_sql_update_changes_physical_storage(
    tmp_path,
):
    db = create_database(tmp_path)

    insert_students(db)

    db.execute(
        "UPDATE students SET cgpa = 10.0 WHERE id = 1"
    )

    table = db.table("students")
    record_id = table.record_ids[0]

    assert table.physical_table.read(
        record_id
    )["cgpa"] == 10.0


def test_sql_update_with_and_changes_physical_storage(
    tmp_path,
):
    db = create_database(tmp_path)

    insert_students(db)

    db.execute(
        "UPDATE students SET cgpa = 10.0 "
        "WHERE id = 1 AND name = 'Sayman'"
    )

    table = db.table("students")
    record_id = table.record_ids[0]

    assert table.physical_table.read(
        record_id
    )["cgpa"] == 10.0


def test_non_matching_update_does_not_change_physical_storage(
    tmp_path,
):
    db = create_database(tmp_path)

    insert_students(db)

    table = db.table("students")

    before = table.physical_table.scan()

    db.execute(
        "UPDATE students SET cgpa = 10.0 WHERE id = 999"
    )

    after = table.physical_table.scan()

    assert after == before