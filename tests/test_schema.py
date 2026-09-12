import pytest

from jugaaddb.core.schema import Column, Schema


def test_valid_schema():
    schema = Schema([
        Column(
            "id",
            "INTEGER",
            primary_key=True,
            nullable=False
        ),
        Column("name", "TEXT")
    ])

    assert len(schema.columns) == 2


def test_empty_schema_rejected():
    with pytest.raises(ValueError):
        Schema([])


def test_duplicate_columns_rejected():
    with pytest.raises(ValueError):
        Schema([
            Column("id", "INTEGER"),
            Column("id", "TEXT")
        ])


def test_multiple_primary_keys_rejected():
    with pytest.raises(ValueError):
        Schema([
            Column("id", "INTEGER", primary_key=True),
            Column("id2", "INTEGER", primary_key=True)
        ])


def test_invalid_data_type_rejected():
    with pytest.raises(ValueError):
        Column("name", "UNKNOWN")


def test_invalid_row_type_rejected():
    schema = Schema([
        Column("id", "INTEGER", nullable=False)
    ])

    with pytest.raises(TypeError):
        schema.validate_row({
            "id": "wrong"
        })


def test_unknown_column_rejected():
    schema = Schema([
        Column("id", "INTEGER")
    ])

    with pytest.raises(ValueError):
        schema.validate_row({
            "unknown": 123
        })


def test_nullable_constraint():
    schema = Schema([
        Column(
            "name",
            "TEXT",
            nullable=False
        )
    ])

    with pytest.raises(ValueError):
        schema.validate_row({
            "name": None
        })