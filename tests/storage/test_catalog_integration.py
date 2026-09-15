from pathlib import Path

from jugaaddb.core.database import Database


def create_database(tmp_path: Path):
    return Database.create(
        str(tmp_path / "college.jdb")
    )


def create_students(db):
    db.execute(
        "CREATE TABLE students ("
        "id INTEGER PRIMARY KEY, "
        "name TEXT, "
        "cgpa FLOAT"
        ")"
    )


def test_catalog_contains_physical_metadata(
    tmp_path,
):
    db = create_database(tmp_path)

    create_students(db)

    table_data = db.data[
        "catalog"
    ][
        "tables"
    ][
        "students"
    ]

    assert "physical" in table_data
    assert table_data["physical"]["format"] == (
        "slotted-page"
    )
    assert table_data["physical"]["path"].endswith(
        "students.tbl"
    )


def test_catalog_schema_reconstructs_after_reopen(
    tmp_path,
):
    path = tmp_path / "college.jdb"

    db = Database.create(
        str(path)
    )

    create_students(db)

    reopened = Database.open(
        str(path)
    )

    schema = reopened.table(
        "students"
    ).schema

    assert [
        (
            column.name,
            column.data_type,
            column.primary_key,
            column.nullable,
            column.unique,
        )
        for column in schema.columns
    ] == [
        (
            "id",
            "INTEGER",
            True,
            False,
            False,
        ),
        (
            "name",
            "TEXT",
            False,
            True,
            False,
        ),
        (
            "cgpa",
            "FLOAT",
            False,
            True,
            False,
        ),
    ]


def test_physical_table_reconnects_after_reopen(
    tmp_path,
):
    path = tmp_path / "college.jdb"

    db = Database.create(
        str(path)
    )

    create_students(db)

    db.execute(
        "INSERT INTO students "
        "(id, name, cgpa) "
        "VALUES (1, 'Sayman', 8.5)"
    )

    reopened = Database.open(
        str(path)
    )

    table = reopened.table(
        "students"
    )

    assert table.physical_table is not None

    assert table.physical_table.count() == 1

    assert table.select_all() == [
        {
            "id": 1,
            "name": "Sayman",
            "cgpa": 8.5,
        }
    ]


def test_multiple_tables_have_separate_physical_storage(
    tmp_path,
):
    db = create_database(tmp_path)

    db.execute(
        "CREATE TABLE students "
        "(id INTEGER PRIMARY KEY, name TEXT)"
    )

    db.execute(
        "CREATE TABLE teachers "
        "(id INTEGER PRIMARY KEY, name TEXT)"
    )

    students = db.table(
        "students"
    )

    teachers = db.table(
        "teachers"
    )

    assert students.physical_table.path != (
        teachers.physical_table.path
    )

    assert students.physical_table.path.name == (
        "students.tbl"
    )

    assert teachers.physical_table.path.name == (
        "teachers.tbl"
    )


def test_physical_files_exist_for_catalog_tables(
    tmp_path,
):
    db = create_database(tmp_path)

    create_students(db)

    students = db.table(
        "students"
    )

    assert students.physical_table.path.exists()


def test_catalog_survives_data_persistence(
    tmp_path,
):
    path = tmp_path / "college.jdb"

    db = Database.create(
        str(path)
    )

    create_students(db)

    db.execute(
        "INSERT INTO students "
        "(id, name, cgpa) "
        "VALUES (1, 'Sayman', 9.1)"
    )

    reopened = Database.open(
        str(path)
    )

    assert reopened.tables() == [
        "students"
    ]

    assert reopened.table(
        "students"
    ).select_all() == [
        {
            "id": 1,
            "name": "Sayman",
            "cgpa": 9.1,
        }
    ]


def test_legacy_table_gets_physical_metadata(
    tmp_path,
):
    path = tmp_path / "college.jdb"

    db = Database.create(
        str(path)
    )

    db.data["catalog"]["tables"][
        "legacy"
    ] = {
        "schema": [
            {
                "name": "id",
                "data_type": "INTEGER",
                "primary_key": True,
                "nullable": True,
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
        "legacy"
    )

    assert table.physical_table is not None
    assert table.physical_table.path.exists()

    assert table.select_all() == [
        {
            "id": 1,
            "name": "Legacy",
        }
    ]


def test_catalog_physical_path_is_persistent(
    tmp_path,
):
    path = tmp_path / "college.jdb"

    db = Database.create(
        str(path)
    )

    create_students(db)

    first_path = db.data[
        "catalog"
    ][
        "tables"
    ][
        "students"
    ][
        "physical"
    ][
        "path"
    ]

    reopened = Database.open(
        str(path)
    )

    second_path = reopened.data[
        "catalog"
    ][
        "tables"
    ][
        "students"
    ][
        "physical"
    ][
        "path"
    ]

    assert first_path == second_path


def test_table_returns_same_physical_storage(
    tmp_path,
):
    db = create_database(tmp_path)

    create_students(db)

    first = db.table(
        "students"
    )

    second = db.table(
        "students"
    )

    assert first.physical_table is (
        second.physical_table
    )


def test_catalog_table_listing(
    tmp_path,
):
    db = create_database(tmp_path)

    db.execute(
        "CREATE TABLE zeta "
        "(id INTEGER)"
    )

    db.execute(
        "CREATE TABLE alpha "
        "(id INTEGER)"
    )

    assert db.tables() == [
        "alpha",
        "zeta",
    ]