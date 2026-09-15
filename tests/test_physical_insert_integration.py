from pathlib import Path

from jugaaddb.core.database import Database
from jugaaddb.sql.result import CommandResult


def create_database(tmp_path: Path) -> Database:
    return Database.create(
        str(
            tmp_path / "students.jdb"
        )
    )


def create_students(
    db: Database,
) -> None:
    db.execute(
        """
        CREATE TABLE students (
            id INTEGER PRIMARY KEY,
            name TEXT,
            cgpa FLOAT
        )
        """
    )


def test_database_table_has_physical_storage(
    tmp_path,
):
    db = create_database(tmp_path)

    create_students(db)

    table = db.table(
        "students"
    )

    assert table.physical_table is not None

    assert table.physical_table.path == Path(
        f"{db.path}.tables/students.tbl"
    )

    assert table.physical_table.path.exists()


def test_sql_insert_creates_physical_record(
    tmp_path,
):
    db = create_database(tmp_path)

    create_students(db)

    result = db.execute(
        """
        INSERT INTO students (id, name, cgpa)
        VALUES (1, 'Sayman', 8.5)
        """
    )

    assert isinstance(
        result,
        CommandResult,
    )

    table = db.table(
        "students"
    )

    assert table.physical_table.count() == 1

    assert table.physical_table.scan() == [
        (
            (1, 0),
            {
                "id": 1,
                "name": "Sayman",
                "cgpa": 8.5,
            },
        )
    ]

    assert table.record_ids == [
        (1, 0)
    ]


def test_multiple_sql_inserts_use_physical_record_ids(
    tmp_path,
):
    db = create_database(tmp_path)

    create_students(db)

    db.execute(
        """
        INSERT INTO students (id, name)
        VALUES (1, 'A')
        """
    )

    db.execute(
        """
        INSERT INTO students (id, name)
        VALUES (2, 'B')
        """
    )

    db.execute(
        """
        INSERT INTO students (id, name)
        VALUES (3, 'C')
        """
    )

    table = db.table(
        "students"
    )

    assert table.record_ids == [
        (1, 0),
        (1, 1),
        (1, 2),
    ]

    assert table.physical_table.count() == 3


def test_physical_insert_survives_database_reopen(
    tmp_path,
):
    path = tmp_path / "students.jdb"

    db = Database.create(
        str(path)
    )

    create_students(db)

    db.execute(
        """
        INSERT INTO students (id, name)
        VALUES (1, 'Sayman')
        """
    )

    reopened = Database.open(
        str(path)
    )

    table = reopened.table(
        "students"
    )

    assert table.physical_table.count() == 1

    assert table.physical_table.read(
        (1, 0)
    ) == {
        "id": 1,
        "name": "Sayman",
        "cgpa": None,
    }


def test_legacy_rows_are_migrated_to_physical_storage(
    tmp_path,
):
    path = tmp_path / "legacy.jdb"

    db = Database.create(
        str(path)
    )

    db.data["catalog"]["tables"]["students"] = {
        "schema": [
            {
                "name": "id",
                "data_type": "INTEGER",
                "primary_key": True,
                "nullable": False,
                "unique": False,
            },
            {
                "name": "name",
                "data_type": "TEXT",
                "primary_key": False,
                "nullable": True,
                "unique": False,
            },
        ],
        "rows": [
            {
                "id": 1,
                "name": "Legacy",
            }
        ],
        "record_ids": [
            (1, 0)
        ],
    }

    db._save()

    reopened = Database.open(
        str(path)
    )

    table = reopened.table(
        "students"
    )

    assert table.physical_table.count() == 1

    assert table.physical_table.scan() == [
        (
            (1, 0),
            {
                "id": 1,
                "name": "Legacy",
            },
        )
    ]