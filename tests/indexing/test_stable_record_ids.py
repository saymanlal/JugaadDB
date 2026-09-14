from jugaaddb.core.database import Database
from jugaaddb.core.schema import Column


def create_database(tmp_path):
    db = Database.create(
        str(tmp_path / "stable_ids.jdb")
    )

    db.create_table(
        "students",
        [
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
        ],
    )

    return db


def test_record_ids_are_assigned_independently_of_row_position(
    tmp_path,
):
    db = create_database(tmp_path)
    table = db.table("students")

    table.insert(
        {
            "id": 101,
            "name": "A",
        }
    )

    table.insert(
        {
            "id": 102,
            "name": "B",
        }
    )

    table.insert(
        {
            "id": 103,
            "name": "C",
        }
    )

    assert table.record_ids == [
        (1, 0),
        (1, 1),
        (1, 2),
    ]


def test_delete_does_not_shift_remaining_record_ids(
    tmp_path,
):
    db = create_database(tmp_path)
    table = db.table("students")

    table.insert(
        {
            "id": 101,
            "name": "A",
        }
    )

    table.insert(
        {
            "id": 102,
            "name": "B",
        }
    )

    table.insert(
        {
            "id": 103,
            "name": "C",
        }
    )

    table.delete(
        {
            "id": 102,
        }
    )

    assert table.record_ids == [
        (1, 0),
        (1, 2),
    ]


def test_insert_after_delete_gets_new_record_id(
    tmp_path,
):
    db = create_database(tmp_path)
    table = db.table("students")

    table.insert(
        {
            "id": 101,
            "name": "A",
        }
    )

    table.insert(
        {
            "id": 102,
            "name": "B",
        }
    )

    table.delete(
        {
            "id": 101,
        }
    )

    table.insert(
        {
            "id": 103,
            "name": "C",
        }
    )

    assert table.record_ids == [
        (1, 1),
        (1, 2),
    ]


def test_index_points_to_correct_row_after_middle_delete(
    tmp_path,
):
    db = create_database(tmp_path)
    table = db.table("students")

    table.insert(
        {
            "id": 101,
            "name": "A",
        }
    )

    table.insert(
        {
            "id": 102,
            "name": "B",
        }
    )

    table.insert(
        {
            "id": 103,
            "name": "C",
        }
    )

    db.execute(
        "CREATE INDEX students_id_idx "
        "ON students (id);"
    )

    table.delete(
        {
            "id": 102,
        }
    )

    result = db.execute(
        "SELECT * FROM students WHERE id = 103;"
    )

    assert result.rows == (
        {
            "id": 103,
            "name": "C",
        },
    )


def test_index_remains_correct_after_delete_and_insert(
    tmp_path,
):
    db = create_database(tmp_path)
    table = db.table("students")

    table.insert(
        {
            "id": 101,
            "name": "A",
        }
    )

    table.insert(
        {
            "id": 102,
            "name": "B",
        }
    )

    table.insert(
        {
            "id": 103,
            "name": "C",
        }
    )

    db.execute(
        "CREATE INDEX students_id_idx "
        "ON students (id);"
    )

    table.delete(
        {
            "id": 102,
        }
    )

    table.insert(
        {
            "id": 104,
            "name": "D",
        }
    )

    assert db.execute(
        "SELECT * FROM students WHERE id = 101;"
    ).rows == (
        {
            "id": 101,
            "name": "A",
        },
    )

    assert db.execute(
        "SELECT * FROM students WHERE id = 103;"
    ).rows == (
        {
            "id": 103,
            "name": "C",
        },
    )

    assert db.execute(
        "SELECT * FROM students WHERE id = 104;"
    ).rows == (
        {
            "id": 104,
            "name": "D",
        },
    )