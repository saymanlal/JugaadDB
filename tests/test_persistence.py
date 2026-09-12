from jugaaddb.core.database import Database
from jugaaddb.core.schema import Column


def test_data_survives_database_reopen(tmp_path):
    db_path = tmp_path / "college.jdb"

    # Create database
    db = Database.create(str(db_path))

    students = db.create_table(
        "students",
        [
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
        ]
    )

    students.insert({
        "id": 1,
        "name": "Sayman",
        "cgpa": 8.5
    })

    students.insert({
        "id": 2,
        "name": "Rahul",
        "cgpa": 9.1
    })

    # Reopen database from disk
    reopened_db = Database.open(str(db_path))

    reopened_students = reopened_db.table(
        "students"
    )

    rows = reopened_students.select_all()

    assert len(rows) == 2
    assert rows[0]["name"] == "Sayman"
    assert rows[1]["name"] == "Rahul"


def test_update_survives_reopen(tmp_path):
    db_path = tmp_path / "college.jdb"

    db = Database.create(str(db_path))

    students = db.create_table(
        "students",
        [
            Column(
                "id",
                "INTEGER",
                primary_key=True,
                nullable=False
            ),
            Column("name", "TEXT"),
            Column("cgpa", "FLOAT")
        ]
    )

    students.insert({
        "id": 1,
        "name": "Sayman",
        "cgpa": 8.5
    })

    students.update(
        {"id": 1},
        {"cgpa": 9.5}
    )

    reopened_db = Database.open(str(db_path))
    reopened_students = reopened_db.table("students")

    rows = reopened_students.select_all()

    assert rows[0]["cgpa"] == 9.5


def test_delete_survives_reopen(tmp_path):
    db_path = tmp_path / "college.jdb"

    db = Database.create(str(db_path))

    students = db.create_table(
        "students",
        [
            Column(
                "id",
                "INTEGER",
                primary_key=True,
                nullable=False
            ),
            Column("name", "TEXT")
        ]
    )

    students.insert({
        "id": 1,
        "name": "Sayman"
    })

    students.insert({
        "id": 2,
        "name": "Rahul"
    })

    students.delete({
        "id": 2
    })

    reopened_db = Database.open(str(db_path))
    reopened_students = reopened_db.table("students")

    rows = reopened_students.select_all()

    assert len(rows) == 1
    assert rows[0]["id"] == 1