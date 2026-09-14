import struct

import pytest

from jugaaddb.indexing.btree import BPlusTreeIndex
from jugaaddb.indexing.metadata import IndexMetadata
from jugaaddb.indexing.persistence import (
    HEADER_FORMAT,
    HEADER_SIZE,
    MAGIC,
    VERSION,
    BTreePersistence,
)


def build_index():
    index = BPlusTreeIndex(
        name="students_id",
        column="id",
        order=4,
    )

    for value in range(1, 30):
        index.insert(
            value,
            (value, value % 3),
        )

    return index


def build_metadata():
    return IndexMetadata(
        table_name="students",
        index_name="students_id",
        column="id",
        index_type="btree",
        order=4,
        unique=True,
    )


def test_save_creates_file(tmp_path):
    index = build_index()
    metadata = build_metadata()

    path = tmp_path / "students_id.jidx"

    BTreePersistence.save(
        index,
        path,
        metadata,
    )

    assert path.exists()


def test_load_returns_index_and_metadata(tmp_path):
    index = build_index()
    metadata = build_metadata()

    path = tmp_path / "students_id.jidx"

    BTreePersistence.save(
        index,
        path,
        metadata,
    )

    restored, restored_metadata = BTreePersistence.load(
        path
    )

    assert isinstance(restored, BPlusTreeIndex)
    assert isinstance(
        restored_metadata,
        IndexMetadata,
    )


def test_metadata_round_trip(tmp_path):
    index = build_index()
    metadata = build_metadata()

    path = tmp_path / "students_id.jidx"

    BTreePersistence.save(
        index,
        path,
        metadata,
    )

    _, restored_metadata = BTreePersistence.load(
        path
    )

    assert restored_metadata == metadata


def test_index_name_is_restored(tmp_path):
    index = build_index()
    metadata = build_metadata()

    path = tmp_path / "students_id.jidx"

    BTreePersistence.save(
        index,
        path,
        metadata,
    )

    restored, _ = BTreePersistence.load(
        path
    )

    assert restored.name == "students_id"


def test_index_column_is_restored(tmp_path):
    index = build_index()
    metadata = build_metadata()

    path = tmp_path / "students_id.jidx"

    BTreePersistence.save(
        index,
        path,
        metadata,
    )

    restored, _ = BTreePersistence.load(
        path
    )

    assert restored.column == "id"


def test_table_name_is_restored(tmp_path):
    index = build_index()
    metadata = build_metadata()

    path = tmp_path / "students_id.jidx"

    BTreePersistence.save(
        index,
        path,
        metadata,
    )

    restored, _ = BTreePersistence.load(
        path
    )

    assert restored.table_name == "students"


def test_unique_flag_is_restored(tmp_path):
    index = build_index()
    metadata = build_metadata()

    path = tmp_path / "students_id.jidx"

    BTreePersistence.save(
        index,
        path,
        metadata,
    )

    restored, _ = BTreePersistence.load(
        path
    )

    assert restored.unique is True


def test_order_is_restored(tmp_path):
    index = BPlusTreeIndex(
        name="students_id",
        column="id",
        order=7,
    )

    for value in range(100):
        index.insert(
            value,
            (value + 1, 0),
        )

    metadata = IndexMetadata(
        table_name="students",
        index_name="students_id",
        column="id",
        order=7,
    )

    path = tmp_path / "students_id.jidx"

    BTreePersistence.save(
        index,
        path,
        metadata,
    )

    restored, restored_metadata = (
        BTreePersistence.load(path)
    )

    assert restored.order == 7
    assert restored_metadata.order == 7


def test_search_survives_persistence(tmp_path):
    index = build_index()
    metadata = build_metadata()

    path = tmp_path / "students_id.jidx"

    BTreePersistence.save(
        index,
        path,
        metadata,
    )

    restored, _ = BTreePersistence.load(
        path
    )

    for value in range(1, 30):
        assert restored.search(value) == [
            (value, value % 3)
        ]


def test_scan_survives_persistence(tmp_path):
    index = build_index()
    metadata = build_metadata()

    path = tmp_path / "students_id.jidx"

    BTreePersistence.save(
        index,
        path,
        metadata,
    )

    restored, _ = BTreePersistence.load(
        path
    )

    assert restored.scan() == index.scan()


def test_range_search_survives_persistence(tmp_path):
    index = build_index()
    metadata = build_metadata()

    path = tmp_path / "students_id.jidx"

    BTreePersistence.save(
        index,
        path,
        metadata,
    )

    restored, _ = BTreePersistence.load(
        path
    )

    assert restored.search_range(
        5,
        20,
        include_start=True,
        include_end=False,
    ) == index.search_range(
        5,
        20,
        include_start=True,
        include_end=False,
    )


def test_duplicate_keys_survive_persistence(tmp_path):
    index = BPlusTreeIndex(
        name="students_score",
        column="score",
        order=4,
    )

    index.insert(90, (1, 0))
    index.insert(90, (1, 1))
    index.insert(90, (2, 0))

    metadata = IndexMetadata(
        table_name="students",
        index_name="students_score",
        column="score",
        order=4,
    )

    path = tmp_path / "students_score.jidx"

    BTreePersistence.save(
        index,
        path,
        metadata,
    )

    restored, _ = BTreePersistence.load(
        path
    )

    assert restored.search(90) == [
        (1, 0),
        (1, 1),
        (2, 0),
    ]


def test_leaf_chain_survives_persistence(tmp_path):
    index = build_index()
    metadata = build_metadata()

    path = tmp_path / "students_id.jidx"

    BTreePersistence.save(
        index,
        path,
        metadata,
    )

    restored, _ = BTreePersistence.load(
        path
    )

    original_leaf = index._leftmost_leaf()
    restored_leaf = restored._leftmost_leaf()

    while original_leaf is not None:
        assert restored_leaf is not None
        assert (
            restored_leaf.keys
            == original_leaf.keys
        )

        original_leaf = original_leaf.next_leaf
        restored_leaf = restored_leaf.next_leaf

    assert restored_leaf is None


def test_tree_validation_survives_persistence(tmp_path):
    index = build_index()
    metadata = build_metadata()

    path = tmp_path / "students_id.jidx"

    BTreePersistence.save(
        index,
        path,
        metadata,
    )

    restored, _ = BTreePersistence.load(
        path
    )

    restored.validate()


def test_save_requires_index(tmp_path):
    metadata = build_metadata()

    with pytest.raises(TypeError):
        BTreePersistence.save(
            object(),
            tmp_path / "test.jidx",
            metadata,
        )


def test_save_requires_metadata(tmp_path):
    index = build_index()

    with pytest.raises(TypeError):
        BTreePersistence.save(
            index,
            tmp_path / "test.jidx",
            object(),
        )


def test_save_rejects_non_btree_metadata(tmp_path):
    index = build_index()

    metadata = IndexMetadata(
        table_name="students",
        index_name="students_id",
        column="id",
        index_type="hash",
        order=4,
    )

    with pytest.raises(ValueError):
        BTreePersistence.save(
            index,
            tmp_path / "test.jidx",
            metadata,
        )


def test_save_rejects_order_mismatch(tmp_path):
    index = BPlusTreeIndex(
        name="students_id",
        column="id",
        order=5,
    )

    metadata = IndexMetadata(
        table_name="students",
        index_name="students_id",
        column="id",
        order=4,
    )

    with pytest.raises(ValueError):
        BTreePersistence.save(
            index,
            tmp_path / "test.jidx",
            metadata,
        )


def test_save_rejects_name_mismatch(tmp_path):
    index = BPlusTreeIndex(
        name="actual_index",
        column="id",
        order=4,
    )

    metadata = IndexMetadata(
        table_name="students",
        index_name="different_index",
        column="id",
        order=4,
    )

    with pytest.raises(ValueError):
        BTreePersistence.save(
            index,
            tmp_path / "test.jidx",
            metadata,
        )


def test_save_rejects_column_mismatch(tmp_path):
    index = BPlusTreeIndex(
        name="students_id",
        column="actual_id",
        order=4,
    )

    metadata = IndexMetadata(
        table_name="students",
        index_name="students_id",
        column="id",
        order=4,
    )

    with pytest.raises(ValueError):
        BTreePersistence.save(
            index,
            tmp_path / "test.jidx",
            metadata,
        )


def test_load_missing_file_is_rejected(tmp_path):
    with pytest.raises(FileNotFoundError):
        BTreePersistence.load(
            tmp_path / "missing.jidx"
        )


def test_invalid_magic_is_rejected(tmp_path):
    index = build_index()
    metadata = build_metadata()

    path = tmp_path / "students_id.jidx"

    BTreePersistence.save(
        index,
        path,
        metadata,
    )

    data = bytearray(path.read_bytes())

    data[0:4] = b"XXXX"

    path.write_bytes(bytes(data))

    with pytest.raises(ValueError):
        BTreePersistence.load(path)


def test_invalid_version_is_rejected(tmp_path):
    index = build_index()
    metadata = build_metadata()

    path = tmp_path / "students_id.jidx"

    BTreePersistence.save(
        index,
        path,
        metadata,
    )

    data = bytearray(path.read_bytes())

    data[4] = VERSION + 1

    path.write_bytes(bytes(data))

    with pytest.raises(ValueError):
        BTreePersistence.load(path)


def test_truncated_persistent_payload_is_rejected(tmp_path):
    index = build_index()
    metadata = build_metadata()

    path = tmp_path / "students_id.jidx"

    BTreePersistence.save(
        index,
        path,
        metadata,
    )

    data = path.read_bytes()

    path.write_bytes(data[:-1])

    with pytest.raises(ValueError):
        BTreePersistence.load(path)


def test_corrupted_metadata_length_is_rejected(tmp_path):
    index = build_index()
    metadata = build_metadata()

    path = tmp_path / "students_id.jidx"

    BTreePersistence.save(
        index,
        path,
        metadata,
    )

    data = bytearray(path.read_bytes())

    struct.pack_into(
        HEADER_FORMAT,
        data,
        0,
        MAGIC,
        VERSION,
        999999,
        1,
    )

    path.write_bytes(bytes(data))

    with pytest.raises(ValueError):
        BTreePersistence.load(path)


def test_corrupted_tree_length_is_rejected(tmp_path):
    index = build_index()
    metadata = build_metadata()

    path = tmp_path / "students_id.jidx"

    BTreePersistence.save(
        index,
        path,
        metadata,
    )

    data = bytearray(path.read_bytes())

    metadata_length = struct.unpack_from(
        ">I",
        data,
        5,
    )[0]

    struct.pack_into(
        HEADER_FORMAT,
        data,
        0,
        MAGIC,
        VERSION,
        metadata_length,
        999999,
    )

    path.write_bytes(bytes(data))

    with pytest.raises(ValueError):
        BTreePersistence.load(path)


def test_existing_file_is_overwritten(tmp_path):
    index = build_index()
    metadata = build_metadata()

    path = tmp_path / "students_id.jidx"

    BTreePersistence.save(
        index,
        path,
        metadata,
    )

    first_size = path.stat().st_size

    index.insert(
        1000,
        (1000, 0),
    )

    BTreePersistence.save(
        index,
        path,
        metadata,
    )

    second_size = path.stat().st_size

    assert second_size > first_size

    restored, _ = BTreePersistence.load(
        path
    )

    assert restored.search(1000) == [
        (1000, 0)
    ]


def test_large_tree_survives_persistence(tmp_path):
    index = BPlusTreeIndex(
        name="large_index",
        column="id",
        order=4,
    )

    for value in range(1000):
        index.insert(
            value,
            (value + 1, value % 10),
        )

    metadata = IndexMetadata(
        table_name="large_table",
        index_name="large_index",
        column="id",
        order=4,
    )

    path = tmp_path / "large_index.jidx"

    BTreePersistence.save(
        index,
        path,
        metadata,
    )

    restored, restored_metadata = (
        BTreePersistence.load(path)
    )

    assert restored_metadata == metadata

    restored.validate()

    for value in range(1000):
        assert restored.search(value) == [
            (value + 1, value % 10)
        ]