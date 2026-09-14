import pytest

from jugaaddb.core.database import Database
from jugaaddb.sql.errors import SQLExecutionError


def test_unknown_table_becomes_sql_execution_error(tmp_path):
    db = Database.create(str(tmp_path / "errors.jdb"))

    with pytest.raises(SQLExecutionError):
        db.execute("SELECT * FROM missing")


def test_invalid_update_condition_becomes_sql_execution_error(tmp_path):
    db = Database.create(str(tmp_path / "errors.jdb"))

    db.execute(
        "CREATE TABLE students ("
        "id INTEGER PRIMARY KEY, "
        "name TEXT)"
    )

    with pytest.raises(SQLExecutionError):
        db.execute(
            "UPDATE students SET name = 'Test' "
            "WHERE id > 1"
        )


def test_invalid_delete_condition_becomes_sql_execution_error(tmp_path):
    db = Database.create(str(tmp_path / "errors.jdb"))

    db.execute(
        "CREATE TABLE students ("
        "id INTEGER PRIMARY KEY, "
        "name TEXT)"
    )

    with pytest.raises(SQLExecutionError):
        db.execute(
            "DELETE FROM students WHERE id > 1"
        )