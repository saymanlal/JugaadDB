import pytest

from jugaaddb.core.database import Database
from jugaaddb.sql.errors import SQLExecutionError


def create_database(tmp_path):
    return Database.create(
        str(tmp_path / "advanced.jdb")
    )


def create_students_table(db):
    db.execute(
        """
        CREATE TABLE students (
            id INTEGER PRIMARY KEY,
            name TEXT UNIQUE,
            department TEXT,
            cgpa FLOAT
        )
        """
    )

    db.execute(
        "INSERT INTO students "
        "(id, name, department, cgpa) "
        "VALUES (1, 'Sayman', 'AIML', 9.1)"
    )

    db.execute(
        "INSERT INTO students "
        "(id, name, department, cgpa) "
        "VALUES (2, 'Rahul', 'CSE', 8.5)"
    )

    db.execute(
        "INSERT INTO students "
        "(id, name, department, cgpa) "
        "VALUES (3, 'Aman', 'AIML', 7.8)"
    )


def test_select_rejects_unknown_column(tmp_path):
    db = create_database(tmp_path)

    create_students_table(db)

    with pytest.raises(SQLExecutionError):
        db.execute(
            "SELECT salary FROM students"
        )


def test_select_rejects_duplicate_columns(tmp_path):
    db = create_database(tmp_path)

    create_students_table(db)

    with pytest.raises(SQLExecutionError):
        db.execute(
            "SELECT id, id FROM students"
        )


def test_update_rejects_unknown_column(tmp_path):
    db = create_database(tmp_path)

    create_students_table(db)

    with pytest.raises(SQLExecutionError):
        db.execute(
            "UPDATE students "
            "SET salary = 100 "
            "WHERE id = 1"
        )


def test_update_rejects_duplicate_assignments(tmp_path):
    db = create_database(tmp_path)

    create_students_table(db)

    with pytest.raises(SQLExecutionError):
        db.execute(
            "UPDATE students "
            "SET cgpa = 9.0, cgpa = 8.0 "
            "WHERE id = 1"
        )


def test_update_with_and_condition(tmp_path):
    db = create_database(tmp_path)

    create_students_table(db)

    result = db.execute(
        "UPDATE students "
        "SET cgpa = 10.0 "
        "WHERE department = 'AIML' "
        "AND cgpa > 8.0"
    )

    assert result.affected_rows == 1

    rows = db.execute(
        "SELECT cgpa FROM students "
        "WHERE id = 1"
    )

    assert rows.rows[0]["cgpa"] == 10.0


def test_update_with_or_condition(tmp_path):
    db = create_database(tmp_path)

    create_students_table(db)

    result = db.execute(
        "UPDATE students "
        "SET department = 'TECH' "
        "WHERE id = 1 OR id = 2"
    )

    assert result.affected_rows == 2


def test_delete_with_and_condition(tmp_path):
    db = create_database(tmp_path)

    create_students_table(db)

    result = db.execute(
        "DELETE FROM students "
        "WHERE department = 'AIML' "
        "AND cgpa < 8.0"
    )

    assert result.affected_rows == 1


def test_delete_with_or_condition(tmp_path):
    db = create_database(tmp_path)

    create_students_table(db)

    result = db.execute(
        "DELETE FROM students "
        "WHERE id = 1 OR id = 2"
    )

    assert result.affected_rows == 2


def test_where_rejects_unknown_column(tmp_path):
    db = create_database(tmp_path)

    create_students_table(db)

    with pytest.raises(SQLExecutionError):
        db.execute(
            "SELECT * FROM students "
            "WHERE salary > 100"
        )