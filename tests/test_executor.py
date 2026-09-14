from jugaaddb.core.database import Database
from jugaaddb.sql.ast import (
    BinaryExpression,
    Identifier,
    Literal,
)
from jugaaddb.sql.executor import Executor
from jugaaddb.sql.plan import (
    Filter,
    Projection,
    TableScan,
)


def create_database(tmp_path):
    return Database.create(str(tmp_path / "executor.jdb"))


def test_select_all(tmp_path):
    db = create_database(tmp_path)

    db.execute(
        "CREATE TABLE students ("
        "id INTEGER PRIMARY KEY, "
        "name TEXT, "
        "cgpa FLOAT)"
    )

    db.execute(
        "INSERT INTO students (id, name, cgpa) "
        "VALUES (1, 'Sayman', 8.5)"
    )

    result = db.execute(
        "SELECT * FROM students"
    )

    assert result == [
        {
            "id": 1,
            "name": "Sayman",
            "cgpa": 8.5,
        }
    ]


def test_insert_and_select_projection(tmp_path):
    db = create_database(tmp_path)

    db.execute(
        "CREATE TABLE students ("
        "id INTEGER PRIMARY KEY, "
        "name TEXT, "
        "cgpa FLOAT)"
    )

    db.execute(
        "INSERT INTO students (id, name, cgpa) "
        "VALUES (1, 'Sayman', 8.5)"
    )

    db.execute(
        "INSERT INTO students (id, name, cgpa) "
        "VALUES (2, 'Rahul', 9.1)"
    )

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


def test_select_with_greater_than(tmp_path):
    db = create_database(tmp_path)

    db.execute(
        "CREATE TABLE students ("
        "id INTEGER PRIMARY KEY, "
        "name TEXT, "
        "cgpa FLOAT)"
    )

    db.execute(
        "INSERT INTO students (id, name, cgpa) "
        "VALUES (1, 'Sayman', 8.5)"
    )

    db.execute(
        "INSERT INTO students (id, name, cgpa) "
        "VALUES (2, 'Rahul', 7.2)"
    )

    result = db.execute(
        "SELECT name FROM students WHERE cgpa > 8.0"
    )

    assert result == [
        {
            "name": "Sayman",
        }
    ]


def test_select_with_and(tmp_path):
    db = create_database(tmp_path)

    db.execute(
        "CREATE TABLE students ("
        "id INTEGER PRIMARY KEY, "
        "name TEXT, "
        "cgpa FLOAT)"
    )

    db.execute(
        "INSERT INTO students (id, name, cgpa) "
        "VALUES (1, 'Sayman', 8.5)"
    )

    db.execute(
        "INSERT INTO students (id, name, cgpa) "
        "VALUES (2, 'Rahul', 9.1)"
    )

    result = db.execute(
        "SELECT name FROM students "
        "WHERE cgpa > 8.0 AND id = 1"
    )

    assert result == [
        {
            "name": "Sayman",
        }
    ]


def test_select_with_or(tmp_path):
    db = create_database(tmp_path)

    db.execute(
        "CREATE TABLE students ("
        "id INTEGER PRIMARY KEY, "
        "name TEXT, "
        "cgpa FLOAT)"
    )

    db.execute(
        "INSERT INTO students (id, name, cgpa) "
        "VALUES (1, 'Sayman', 8.5)"
    )

    db.execute(
        "INSERT INTO students (id, name, cgpa) "
        "VALUES (2, 'Rahul', 7.2)"
    )

    result = db.execute(
        "SELECT name FROM students "
        "WHERE cgpa > 9.0 OR id = 1"
    )

    assert result == [
        {
            "name": "Sayman",
        }
    ]


def test_update(tmp_path):
    db = create_database(tmp_path)

    db.execute(
        "CREATE TABLE students ("
        "id INTEGER PRIMARY KEY, "
        "name TEXT, "
        "cgpa FLOAT)"
    )

    db.execute(
        "INSERT INTO students (id, name, cgpa) "
        "VALUES (1, 'Sayman', 8.5)"
    )

    result = db.execute(
        "UPDATE students SET cgpa = 9.5 WHERE id = 1"
    )

    assert result == 1

    rows = db.execute(
        "SELECT * FROM students"
    )

    assert rows[0]["cgpa"] == 9.5


def test_delete(tmp_path):
    db = create_database(tmp_path)

    db.execute(
        "CREATE TABLE students ("
        "id INTEGER PRIMARY KEY, "
        "name TEXT)"
    )

    db.execute(
        "INSERT INTO students (id, name) "
        "VALUES (1, 'Sayman')"
    )

    result = db.execute(
        "DELETE FROM students WHERE id = 1"
    )

    assert result == 1
    assert db.execute("SELECT * FROM students") == []


def test_create_table(tmp_path):
    db = create_database(tmp_path)

    result = db.execute(
        "CREATE TABLE users ("
        "id INTEGER PRIMARY KEY, "
        "name TEXT UNIQUE)"
    )

    assert result == 1

    db.execute(
        "INSERT INTO users (id, name) "
        "VALUES (1, 'Sayman')"
    )

    assert db.execute("SELECT * FROM users") == [
        {
            "id": 1,
            "name": "Sayman",
        }
    ]


def test_sql_persists_after_reopen(tmp_path):
    path = str(tmp_path / "persistent.jdb")

    db = Database.create(path)

    db.execute(
        "CREATE TABLE students ("
        "id INTEGER PRIMARY KEY, "
        "name TEXT)"
    )

    db.execute(
        "INSERT INTO students (id, name) "
        "VALUES (1, 'Sayman')"
    )

    reopened = Database.open(path)

    assert reopened.execute(
        "SELECT * FROM students"
    ) == [
        {
            "id": 1,
            "name": "Sayman",
        }
    ]


def test_executor_rejects_unknown_plan(tmp_path):
    db = create_database(tmp_path)

    try:
        Executor(db).execute(object())
        assert False
    except TypeError as error:
        assert "Unsupported execution plan" in str(error)