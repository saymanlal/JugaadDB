import struct

import pytest

from jugaaddb.indexing.btree import BPlusTreeIndex
from jugaaddb.indexing.tree_serializer import (
    HEADER_FORMAT,
    HEADER_SIZE,
    MAGIC,
    VERSION,
    BTreeSerializer,
)


def build_index(order=4):
    index = BPlusTreeIndex(
        name="students_id",
        column="id",
        order=order,
    )

    for value in range(1, 20):
        index.insert(value, (value, 0))

    return index


def test_serialize_requires_btree():
    with pytest.raises(TypeError):
        BTreeSerializer.serialize(object())


def test_serialize_produces_bytes():
    index = build_index()

    data = BTreeSerializer.serialize(index)

    assert isinstance(data, bytes)
    assert len(data) > HEADER_SIZE


def test_serialized_data_has_magic():
    index = build_index()

    data = BTreeSerializer.serialize(index)

    assert data[:4] == MAGIC


def test_round_trip_preserves_order():
    index = build_index(order=5)

    restored = BTreeSerializer.deserialize(
        BTreeSerializer.serialize(index)
    )

    assert restored.order == 5


def test_round_trip_preserves_search():
    index = build_index()

    restored = BTreeSerializer.deserialize(
        BTreeSerializer.serialize(index)
    )

    for value in range(1, 20):
        assert restored.search(value) == [(value, 0)]


def test_round_trip_preserves_scan():
    index = build_index()

    restored = BTreeSerializer.deserialize(
        BTreeSerializer.serialize(index)
    )

    assert restored.scan() == index.scan()


def test_round_trip_preserves_range_search():
    index = build_index()

    restored = BTreeSerializer.deserialize(
        BTreeSerializer.serialize(index)
    )

    expected = index.search_range(
        5,
        12,
        include_start=True,
        include_end=False,
    )

    actual = restored.search_range(
        5,
        12,
        include_start=True,
        include_end=False,
    )

    assert actual == expected


def test_round_trip_preserves_duplicate_keys():
    index = BPlusTreeIndex(
        name="students_score",
        column="score",
        order=4,
    )

    index.insert(90, (1, 0))
    index.insert(90, (1, 1))
    index.insert(90, (2, 0))

    restored = BTreeSerializer.deserialize(
        BTreeSerializer.serialize(index)
    )

    assert restored.search(90) == [
        (1, 0),
        (1, 1),
        (2, 0),
    ]


def test_round_trip_preserves_leaf_chain():
    index = build_index()

    restored = BTreeSerializer.deserialize(
        BTreeSerializer.serialize(index)
    )

    original_leaf = index._leftmost_leaf()
    restored_leaf = restored._leftmost_leaf()

    while original_leaf is not None:
        assert restored_leaf is not None
        assert restored_leaf.keys == original_leaf.keys

        original_leaf = original_leaf.next_leaf
        restored_leaf = restored_leaf.next_leaf

    assert restored_leaf is None


def test_round_trip_tree_validates():
    index = build_index()

    restored = BTreeSerializer.deserialize(
        BTreeSerializer.serialize(index)
    )

    restored.validate()


def test_none_key_round_trip():
    index = BPlusTreeIndex(
        name="test",
        column="value",
    )

    index.insert(None, (1, 0))

    restored = BTreeSerializer.deserialize(
        BTreeSerializer.serialize(index)
    )

    assert restored.search(None) == [(1, 0)]


def test_boolean_key_round_trip():
    index = BPlusTreeIndex(
        name="test",
        column="value",
    )

    index.insert(False, (1, 0))
    index.insert(True, (1, 1))

    restored = BTreeSerializer.deserialize(
        BTreeSerializer.serialize(index)
    )

    assert restored.search(False) == [(1, 0)]
    assert restored.search(True) == [(1, 1)]


def test_integer_key_round_trip():
    index = BPlusTreeIndex(
        name="test",
        column="value",
    )

    index.insert(-100, (1, 0))
    index.insert(0, (1, 1))
    index.insert(100, (1, 2))

    restored = BTreeSerializer.deserialize(
        BTreeSerializer.serialize(index)
    )

    assert restored.search(-100) == [(1, 0)]
    assert restored.search(0) == [(1, 1)]
    assert restored.search(100) == [(1, 2)]


def test_float_key_round_trip():
    index = BPlusTreeIndex(
        name="test",
        column="value",
    )

    index.insert(1.5, (1, 0))
    index.insert(2.75, (1, 1))

    restored = BTreeSerializer.deserialize(
        BTreeSerializer.serialize(index)
    )

    assert restored.search(1.5) == [(1, 0)]
    assert restored.search(2.75) == [(1, 1)]


def test_text_key_round_trip():
    index = BPlusTreeIndex(
        name="test",
        column="value",
    )

    index.insert("alice", (1, 0))
    index.insert("bob", (1, 1))
    index.insert("krushn", (1, 2))

    restored = BTreeSerializer.deserialize(
        BTreeSerializer.serialize(index)
    )

    assert restored.search("alice") == [(1, 0)]
    assert restored.search("bob") == [(1, 1)]
    assert restored.search("krushn") == [(1, 2)]


def test_unicode_text_key_round_trip():
    index = BPlusTreeIndex(
        name="test",
        column="value",
    )

    index.insert("namaste", (1, 0))
    index.insert("cafe", (1, 1))

    restored = BTreeSerializer.deserialize(
        BTreeSerializer.serialize(index)
    )

    assert restored.search("namaste") == [(1, 0)]
    assert restored.search("cafe") == [(1, 1)]


def test_deserialize_requires_bytes():
    with pytest.raises(TypeError):
        BTreeSerializer.deserialize("payload")


def test_invalid_magic_is_rejected():
    index = build_index()

    data = bytearray(
        BTreeSerializer.serialize(index)
    )

    data[0:4] = b"XXXX"

    with pytest.raises(ValueError):
        BTreeSerializer.deserialize(bytes(data))


def test_invalid_version_is_rejected():
    index = build_index()

    data = bytearray(
        BTreeSerializer.serialize(index)
    )

    data[4] = VERSION + 1

    with pytest.raises(ValueError):
        BTreeSerializer.deserialize(bytes(data))


def test_truncated_header_is_rejected():
    with pytest.raises(ValueError):
        BTreeSerializer.deserialize(b"JBT")


def test_invalid_payload_length_is_rejected():
    index = build_index()

    data = bytearray(
        BTreeSerializer.serialize(index)
    )

    struct.pack_into(
        HEADER_FORMAT,
        data,
        0,
        MAGIC,
        VERSION,
        999999,
    )

    with pytest.raises(ValueError):
        BTreeSerializer.deserialize(bytes(data))


def test_trailing_bytes_are_rejected():
    index = build_index()

    data = BTreeSerializer.serialize(index)

    with pytest.raises(ValueError):
        BTreeSerializer.deserialize(data + b"\x00")


def test_invalid_root_id_is_rejected():
    index = build_index()

    data = bytearray(
        BTreeSerializer.serialize(index)
    )

    struct.pack_into(
        ">I",
        data,
        HEADER_SIZE + 4,
        999999,
    )

    with pytest.raises(ValueError):
        BTreeSerializer.deserialize(bytes(data))


def test_invalid_order_is_rejected():
    index = build_index()

    data = bytearray(
        BTreeSerializer.serialize(index)
    )

    struct.pack_into(
        ">I",
        data,
        HEADER_SIZE,
        2,
    )

    with pytest.raises(ValueError):
        BTreeSerializer.deserialize(bytes(data))


def test_large_tree_round_trip():
    index = BPlusTreeIndex(
        name="large",
        column="id",
        order=4,
    )

    for value in range(1000):
        index.insert(value, (value + 1, value % 10))

    restored = BTreeSerializer.deserialize(
        BTreeSerializer.serialize(index)
    )

    restored.validate()

    for value in range(1000):
        assert restored.search(value) == [
            (value + 1, value % 10)
        ]


def test_empty_tree_round_trip():
    index = BPlusTreeIndex(
        name="empty",
        column="id",
        order=4,
    )

    restored = BTreeSerializer.deserialize(
        BTreeSerializer.serialize(index)
    )

    assert restored.search(100) == []
    restored.validate()