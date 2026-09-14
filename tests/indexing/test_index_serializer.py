import struct

import pytest

from jugaaddb.indexing.metadata import IndexMetadata
from jugaaddb.indexing.serializer import (
    HEADER_SIZE,
    MAGIC,
    VERSION,
    IndexSerializer,
)


def test_serialize_returns_bytes():
    metadata = IndexMetadata(
        table_name="students",
        index_name="idx_students_id",
        column="id",
    )

    result = IndexSerializer.serialize(metadata)

    assert isinstance(result, bytes)


def test_serialized_data_contains_magic():
    metadata = IndexMetadata(
        table_name="students",
        index_name="idx_students_id",
        column="id",
    )

    result = IndexSerializer.serialize(metadata)

    assert result[:4] == MAGIC


def test_serialized_data_contains_version():
    metadata = IndexMetadata(
        table_name="students",
        index_name="idx_students_id",
        column="id",
    )

    result = IndexSerializer.serialize(metadata)

    version = struct.unpack_from(">B", result, 4)[0]

    assert version == VERSION


def test_serialize_deserialize_round_trip():
    metadata = IndexMetadata(
        table_name="students",
        index_name="idx_students_id",
        column="id",
        index_type="btree",
        order=8,
        unique=True,
    )

    data = IndexSerializer.serialize(metadata)
    restored = IndexSerializer.deserialize(data)

    assert restored == metadata


def test_serialization_is_deterministic():
    metadata = IndexMetadata(
        table_name="students",
        index_name="idx_students_id",
        column="id",
        order=4,
        unique=False,
    )

    first = IndexSerializer.serialize(metadata)
    second = IndexSerializer.serialize(metadata)

    assert first == second


def test_deserialize_rejects_non_bytes():
    with pytest.raises(TypeError):
        IndexSerializer.deserialize("invalid")


def test_deserialize_rejects_short_data():
    with pytest.raises(ValueError):
        IndexSerializer.deserialize(b"JIDX")


def test_deserialize_rejects_invalid_magic():
    metadata = IndexMetadata(
        table_name="students",
        index_name="idx_students_id",
        column="id",
    )

    data = bytearray(IndexSerializer.serialize(metadata))
    data[0:4] = b"XXXX"

    with pytest.raises(ValueError):
        IndexSerializer.deserialize(bytes(data))


def test_deserialize_rejects_invalid_version():
    metadata = IndexMetadata(
        table_name="students",
        index_name="idx_students_id",
        column="id",
    )

    data = bytearray(IndexSerializer.serialize(metadata))
    data[4] = VERSION + 1

    with pytest.raises(ValueError):
        IndexSerializer.deserialize(bytes(data))


def test_deserialize_rejects_invalid_payload_length():
    metadata = IndexMetadata(
        table_name="students",
        index_name="idx_students_id",
        column="id",
    )

    data = bytearray(IndexSerializer.serialize(metadata))

    struct.pack_into(
        ">I",
        data,
        5,
        999999,
    )

    with pytest.raises(ValueError):
        IndexSerializer.deserialize(bytes(data))


def test_deserialize_rejects_trailing_bytes():
    metadata = IndexMetadata(
        table_name="students",
        index_name="idx_students_id",
        column="id",
    )

    data = IndexSerializer.serialize(metadata) + b"\x00"

    with pytest.raises(ValueError):
        IndexSerializer.deserialize(data)


def test_unicode_metadata_round_trip():
    metadata = IndexMetadata(
        table_name="students_table",
        index_name="idx_name",
        column="student_name",
    )

    data = IndexSerializer.serialize(metadata)
    restored = IndexSerializer.deserialize(data)

    assert restored == metadata


def test_large_order_round_trip():
    metadata = IndexMetadata(
        table_name="students",
        index_name="idx_students_id",
        column="id",
        order=100000,
    )

    data = IndexSerializer.serialize(metadata)
    restored = IndexSerializer.deserialize(data)

    assert restored.order == 100000


def test_unique_false_round_trip():
    metadata = IndexMetadata(
        table_name="students",
        index_name="idx_students_id",
        column="id",
        unique=False,
    )

    data = IndexSerializer.serialize(metadata)
    restored = IndexSerializer.deserialize(data)

    assert restored.unique is False


def test_unique_true_round_trip():
    metadata = IndexMetadata(
        table_name="students",
        index_name="idx_students_email",
        column="email",
        unique=True,
    )

    data = IndexSerializer.serialize(metadata)
    restored = IndexSerializer.deserialize(data)

    assert restored.unique is True


def test_header_size_is_correct():
    assert HEADER_SIZE == 9