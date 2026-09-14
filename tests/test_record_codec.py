import pytest

from jugaaddb.core.schema import Column, Schema
from jugaaddb.storage.record_codec import RecordCodec


def make_schema():
    return Schema([
        Column(
            "id",
            "INTEGER",
            primary_key=True,
            nullable=False
        ),
        Column(
            "name",
            "TEXT",
            nullable=False
        ),
        Column(
            "score",
            "FLOAT"
        ),
        Column(
            "active",
            "BOOLEAN"
        ),
    ])


def test_encode_and_decode_row():
    codec = RecordCodec(make_schema())

    row = {
        "id": 1,
        "name": "Ayush",
        "score": 95.5,
        "active": True
    }

    encoded = codec.encode(row)
    decoded = codec.decode(encoded)

    assert decoded == row


def test_schema_controls_column_order():
    codec = RecordCodec(make_schema())

    row = {
        "active": True,
        "name": "Ayush",
        "score": 95.5,
        "id": 1
    }

    decoded = codec.decode(
        codec.encode(row)
    )

    assert list(decoded.keys()) == [
        "id",
        "name",
        "score",
        "active"
    ]


def test_nullable_values():
    codec = RecordCodec(make_schema())

    row = {
        "id": 1,
        "name": "Ayush",
        "score": None,
        "active": None
    }

    assert codec.decode(
        codec.encode(row)
    ) == row


def test_invalid_row_rejected():
    codec = RecordCodec(make_schema())

    with pytest.raises(TypeError):
        codec.encode({
            "id": "wrong",
            "name": "Ayush",
            "score": 95.5,
            "active": True
        })


def test_unknown_column_rejected():
    codec = RecordCodec(make_schema())

    with pytest.raises(ValueError):
        codec.encode({
            "id": 1,
            "name": "Ayush",
            "score": 95.5,
            "active": True,
            "unknown": "value"
        })


def test_missing_non_nullable_column_rejected():
    codec = RecordCodec(make_schema())

    with pytest.raises(ValueError):
        codec.encode({
            "id": 1,
            "score": 95.5,
            "active": True
        })


def test_record_field_count_mismatch_rejected():
    codec = RecordCodec(make_schema())

    from jugaaddb.storage.record import RecordSerializer

    encoded = RecordSerializer.serialize([
        1,
        "Ayush"
    ])

    with pytest.raises(ValueError):
        codec.decode(encoded)