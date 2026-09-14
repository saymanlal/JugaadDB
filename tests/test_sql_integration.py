from pathlib import Path

import pytest

from jugaaddb.core.database import Database
from jugaaddb.sql.errors import SQLExecutionError
from jugaaddb.sql.result import CommandResult, QueryResult


def create_database(tmp_path: Path) -> Database:
    return Database.create(str(tmp_path / "integration.jdb"))


def test_create_table_through_database_execute(tmp_path):
    db = create_database(tmp_path)

    result = db.execute(
        """
        CREATE TABLE students (
            id INTEGER PRIMARY KEY,
            name TEXT,
            cgpa FLOAT
        )
        """
    )

    assert isinstance(result, CommandResult)
    assert result == 1
    assert result.affected_rows == 1
    assert result.query_type == "CREATE TABLE"

    table = db.table("students")

    assert [
        column.name
        for column in table.schema.columns
    ] == ["id", "name", "cgpa"]


def test_insert_through_database_execute(tmp_path):
    db = create_database(tmp_path)

    db.execute(
        """
        CREATE TABLE students (
            id INTEGER PRIMARY KEY,
            name TEXT,
            cgpa FLOAT
        )
        """
    )

    result = db.execute(
        """
        INSERT INTO students (id, name, cgpa)
        VALUES (1, 'Sayman', 8.5)
        """
    )

    assert isinstance(result, CommandResult)
    assert result == 1
    assert result.affected_rows == 1
    assert result.query_type == "INSERT"


def test_select_through_database_execute(tmp_path):
    db = create_database(tmp_path)

    db.execute(
        """
        CREATE TABLE students (
            id INTEGER PRIMARY KEY,
            name TEXT,
            cgpa FLOAT
        )
        """
    )

    db.execute(
        """
        INSERT INTO students (id, name, cgpa)
        VALUES (1, 'Sayman', 8.5)
        """
    )

    db.execute(
        """
        INSERT INTO students (id, name, cgpa)
        VALUES (2, 'Rahul', 9.1)
        """
    )

    result = db.execute(
        "SELECT * FROM students"
    )

    assert isinstance(result, QueryResult)
    assert result.query_type == "SELECT"
    assert result.columns == ("id", "name", "cgpa")
    assert result.row_count == 2

    assert result.to_list() == [
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


def test_select_projection_through_database_execute(tmp_path):
    db = create_database(tmp_path)

    db.execute(
        """
        CREATE TABLE students (
            id INTEGER PRIMARY KEY,
            name TEXT,
            cgpa FLOAT
        )
        """
    )

    db.execute(
        """
        INSERT INTO students (id, name, cgpa)
        VALUES (1, 'Sayman', 8.5)
        """
    )

    result = db.execute(
        """
        SELECT name, cgpa
        FROM students
        """
    )

    assert result.columns == ("name", "cgpa")

    assert result.to_list() == [
        {
            "name": "Sayman",
            "cgpa": 8.5,
        }
    ]


def test_select_where_through_database_execute(tmp_path):
    db = create_database(tmp_path)

    db.execute(
        """
        CREATE TABLE students (
            id INTEGER PRIMARY KEY,
            name TEXT,
            cgpa FLOAT
        )
        """
    )

    db.execute(
        """
        INSERT INTO students (id, name, cgpa)
        VALUES (1, 'Sayman', 8.5)
        """
    )

    db.execute(
        """
        INSERT INTO students (id, name, cgpa)
        VALUES (2, 'Rahul', 9.1)
        """
    )

    result = db.execute(
        """
        SELECT name, cgpa
        FROM students
        WHERE cgpa >= 9.0
        """
    )

    assert result.to_list() == [
        {
            "name": "Rahul",
            "cgpa": 9.1,
        }
    ]


def test_update_through_database_execute(tmp_path):
    db = create_database(tmp_path)

    db.execute(
        """
        CREATE TABLE students (
            id INTEGER PRIMARY KEY,
            name TEXT,
            cgpa FLOAT
        )
        """
    )

    db.execute(
        """
        INSERT INTO students (id, name, cgpa)
        VALUES (1, 'Sayman', 8.5)
        """
    )

    result = db.execute(
        """
        UPDATE students
        SET cgpa = 9.0
        WHERE id = 1
        """
    )

    assert isinstance(result, CommandResult)
    assert result == 1
    assert result.affected_rows == 1
    assert result.query_type == "UPDATE"

    selected = db.execute(
        "SELECT * FROM students WHERE id = 1"
    )

    assert selected.to_list() == [
        {
            "id": 1,
            "name": "Sayman",
            "cgpa": 9.0,
        }
    ]


def test_delete_through_database_execute(tmp_path):
    db = create_database(tmp_path)

    db.execute(
        """
        CREATE TABLE students (
            id INTEGER PRIMARY KEY,
            name TEXT,
            cgpa FLOAT
        )
        """
    )

    db.execute(
        """
        INSERT INTO students (id, name, cgpa)
        VALUES (1, 'Sayman', 8.5)
        """
    )

    db.execute(
        """
        INSERT INTO students (id, name, cgpa)
        VALUES (2, 'Rahul', 9.1)
        """
    )

    result = db.execute(
        """
        DELETE FROM students
        WHERE id = 1
        """
    )

    assert isinstance(result, CommandResult)
    assert result == 1
    assert result.affected_rows == 1
    assert result.query_type == "DELETE"

    selected = db.execute(
        "SELECT * FROM students"
    )

    assert selected.to_list() == [
        {
            "id": 2,
            "name": "Rahul",
            "cgpa": 9.1,
        }
    ]


def test_sql_pipeline_persists_across_database_reopen(tmp_path):
    path = tmp_path / "persistent_sql.jdb"

    db = Database.create(str(path))

    db.execute(
        """
        CREATE TABLE students (
            id INTEGER PRIMARY KEY,
            name TEXT,
            cgpa FLOAT
        )
        """
    )

    db.execute(
        """
        INSERT INTO students (id, name, cgpa)
        VALUES (1, 'Sayman', 8.5)
        """
    )

    db = Database.open(str(path))

    result = db.execute(
        "SELECT * FROM students"
    )

    assert result.to_list() == [
        {
            "id": 1,
            "name": "Sayman",
            "cgpa": 8.5,
        }
    ]


def test_database_execute_rejects_non_string_sql(tmp_path):
    db = create_database(tmp_path)

    with pytest.raises(TypeError):
        db.execute(123)


def test_database_execute_rejects_empty_sql(tmp_path):
    db = create_database(tmp_path)

    with pytest.raises(ValueError):
        db.execute("")


def test_database_execute_rejects_whitespace_sql(tmp_path):
    db = create_database(tmp_path)

    with pytest.raises(ValueError):
        db.execute("   ")


def test_database_execute_reports_sql_execution_errors(tmp_path):
    db = create_database(tmp_path)

    with pytest.raises(SQLExecutionError):
        db.execute(
            """
            SELECT *
            FROM missing_table
            """
        )