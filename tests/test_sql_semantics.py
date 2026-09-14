from pathlib import Path

import pytest

from jugaaddb.core.database import Database
from jugaaddb.sql.errors import SQLExecutionError


def create_database(tmp_path: Path) -> Database:
    return Database.create(str(tmp_path / "semantics.jdb"))


def create_students_table(db: Database) -> None:
    db.execute(
        """
        CREATE TABLE students (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT UNIQUE,
            cgpa FLOAT
        )
        """
    )


def test_insert_rejects_unknown_column(tmp_path):
    db = create_database(tmp_path)
    create_students_table(db)

    with pytest.raises(SQLExecutionError):
        db.execute(
            """
            INSERT INTO students (id, username, cgpa)
            VALUES (1, 'Sayman', 8.5)
            """
        )


def test_insert_rejects_duplicate_columns(tmp_path):
    db = create_database(tmp_path)
    create_students_table(db)

    with pytest.raises(SQLExecutionError):
        db.execute(
            """
            INSERT INTO students (id, id, name)
            VALUES (1, 2, 'Sayman')
            """
        )


def test_insert_rejects_missing_required_column(tmp_path):
    db = create_database(tmp_path)
    create_students_table(db)

    with pytest.raises(SQLExecutionError):
        db.execute(
            """
            INSERT INTO students (id, email, cgpa)
            VALUES (1, 'sayman@example.com', 8.5)
            """
        )


def test_insert_rejects_duplicate_primary_key(tmp_path):
    db = create_database(tmp_path)
    create_students_table(db)

    db.execute(
        """
        INSERT INTO students (id, name, email, cgpa)
        VALUES (1, 'Sayman', 'sayman@example.com', 8.5)
        """
    )

    with pytest.raises(SQLExecutionError):
        db.execute(
            """
            INSERT INTO students (id, name, email, cgpa)
            VALUES (1, 'Rahul', 'rahul@example.com', 9.1)
            """
        )


def test_insert_rejects_duplicate_unique_value(tmp_path):
    db = create_database(tmp_path)
    create_students_table(db)

    db.execute(
        """
        INSERT INTO students (id, name, email, cgpa)
        VALUES (1, 'Sayman', 'sayman@example.com', 8.5)
        """
    )

    with pytest.raises(SQLExecutionError):
        db.execute(
            """
            INSERT INTO students (id, name, email, cgpa)
            VALUES (2, 'Rahul', 'sayman@example.com', 9.1)
            """
        )


def test_insert_accepts_nullable_column_omission(tmp_path):
    db = create_database(tmp_path)
    create_students_table(db)

    db.execute(
        """
        INSERT INTO students (id, name)
        VALUES (1, 'Sayman')
        """
    )

    result = db.execute(
        "SELECT * FROM students"
    )

    assert result.to_list() == [
        {
            "id": 1,
            "name": "Sayman",
            "email": None,
            "cgpa": None,
        }
    ]


def test_insert_rejects_explicit_null_for_not_null_column(tmp_path):
    db = create_database(tmp_path)
    create_students_table(db)

    with pytest.raises(SQLExecutionError):
        db.execute(
            """
            INSERT INTO students (id, name)
            VALUES (1, NULL)
            """
        )


def test_insert_rejects_wrong_data_type(tmp_path):
    db = create_database(tmp_path)
    create_students_table(db)

    with pytest.raises(SQLExecutionError):
        db.execute(
            """
            INSERT INTO students (id, name, cgpa)
            VALUES ('wrong', 'Sayman', 8.5)
            """
        )