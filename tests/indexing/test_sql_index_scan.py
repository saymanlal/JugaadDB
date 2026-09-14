from jugaaddb.core.database import Database
from jugaaddb.core.schema import Column


def create_database(tmp_path):
    db = Database.create(
        str(tmp_path / "index_scan.jdb")
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
            Column(
                "cgpa",
                "FLOAT",
            ),
        ],
    )

    table = db.table("students")

    table.insert(
        {
            "id": 101,
            "name": "Sayman",
            "cgpa": 8.7,
        }
    )

    table.insert(
        {
            "id": 102,
            "name": "Rahul",
            "cgpa": 9.1,
        }
    )

    table.insert(
        {
            "id": 103,
            "name": "Aman",
            "cgpa": 8.4,
        }
    )

    return db


def test_select_uses_index_for_exact_match(tmp_path):
    db = create_database(tmp_path)

    db.execute(
        "CREATE INDEX students_id_idx "
        "ON students (id);"
    )

    result = db.execute(
        "SELECT * FROM students WHERE id = 102;"
    )

    assert result.rows == (
        {
            "id": 102,
            "name": "Rahul",
            "cgpa": 9.1,
        },
    )


def test_select_without_index_still_works(tmp_path):
    db = create_database(tmp_path)

    result = db.execute(
        "SELECT * FROM students WHERE id = 102;"
    )

    assert result.rows == (
        {
            "id": 102,
            "name": "Rahul",
            "cgpa": 9.1,
        },
    )


def test_select_index_on_text_column(tmp_path):
    db = create_database(tmp_path)

    db.execute(
        "CREATE INDEX students_name_idx "
        "ON students (name);"
    )

    result = db.execute(
        "SELECT * FROM students "
        "WHERE name = 'Rahul';"
    )

    assert result.rows == (
        {
            "id": 102,
            "name": "Rahul",
            "cgpa": 9.1,
        },
    )


def test_select_index_on_float_column(tmp_path):
    db = create_database(tmp_path)

    db.execute(
        "CREATE INDEX students_cgpa_idx "
        "ON students (cgpa);"
    )

    result = db.execute(
        "SELECT * FROM students "
        "WHERE cgpa = 9.1;"
    )

    assert result.rows == (
        {
            "id": 102,
            "name": "Rahul",
            "cgpa": 9.1,
        },
    )


def test_index_scan_returns_empty_for_missing_value(tmp_path):
    db = create_database(tmp_path)

    db.execute(
        "CREATE INDEX students_id_idx "
        "ON students (id);"
    )

    result = db.execute(
        "SELECT * FROM students WHERE id = 999;"
    )

    assert result.rows == ()


def test_index_scan_preserves_projection(tmp_path):
    db = create_database(tmp_path)

    db.execute(
        "CREATE INDEX students_id_idx "
        "ON students (id);"
    )

    result = db.execute(
        "SELECT name, cgpa "
        "FROM students "
        "WHERE id = 102;"
    )

    assert result.columns == (
        "name",
        "cgpa",
    )

    assert result.rows == (
        {
            "name": "Rahul",
            "cgpa": 9.1,
        },
    )


def test_non_equality_condition_falls_back_to_table_scan(tmp_path):
    db = create_database(tmp_path)

    db.execute(
        "CREATE INDEX students_id_idx "
        "ON students (id);"
    )

    result = db.execute(
        "SELECT * FROM students WHERE id > 101;"
    )

    assert result.rows == (
        {
            "id": 102,
            "name": "Rahul",
            "cgpa": 9.1,
        },
        {
            "id": 103,
            "name": "Aman",
            "cgpa": 8.4,
        },
    )


def test_logical_condition_falls_back_to_table_scan(tmp_path):
    db = create_database(tmp_path)

    db.execute(
        "CREATE INDEX students_id_idx "
        "ON students (id);"
    )

    result = db.execute(
        "SELECT * FROM students "
        "WHERE id = 102 AND cgpa = 9.1;"
    )

    assert result.rows == (
        {
            "id": 102,
            "name": "Rahul",
            "cgpa": 9.1,
        },
    )


def test_indexed_null_value_returns_no_index_match(tmp_path):
    db = create_database(tmp_path)

    db.execute(
        "CREATE INDEX students_cgpa_idx "
        "ON students (cgpa);"
    )

    result = db.execute(
        "SELECT * FROM students "
        "WHERE cgpa = NULL;"
    )

    assert result.rows == ()