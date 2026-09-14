import pytest

from jugaaddb.indexing.btree import BPlusTreeIndex
from jugaaddb.indexing.memory import MemoryIndex
from jugaaddb.indexing.scan import IndexScan


def test_exact_scan_returns_matching_record_ids():
    index = BPlusTreeIndex(
        "students_id_idx",
        "id",
    )

    index.insert(
        101,
        (1, 0),
    )

    index.insert(
        102,
        (1, 1),
    )

    index.insert(
        103,
        (1, 2),
    )

    scan = IndexScan(index)

    assert scan.exact(
        102
    ) == [(1, 1)]


def test_exact_scan_returns_empty_for_missing_key():
    index = BPlusTreeIndex(
        "students_id_idx",
        "id",
    )

    index.insert(
        101,
        (1, 0),
    )

    scan = IndexScan(index)

    assert scan.exact(
        999
    ) == []


def test_exact_scan_supports_duplicate_keys():
    index = BPlusTreeIndex(
        "students_id_idx",
        "id",
    )

    index.insert(
        101,
        (1, 0),
    )

    index.insert(
        101,
        (1, 1),
    )

    index.insert(
        101,
        (1, 2),
    )

    scan = IndexScan(index)

    assert scan.exact(
        101
    ) == [
        (1, 0),
        (1, 1),
        (1, 2),
    ]


def test_range_scan_returns_record_ids():
    index = BPlusTreeIndex(
        "students_id_idx",
        "id",
    )

    for value in range(1, 11):
        index.insert(
            value,
            (1, value - 1),
        )

    scan = IndexScan(index)

    assert scan.range(
        3,
        7,
    ) == [
        (1, 2),
        (1, 3),
        (1, 4),
        (1, 5),
        (1, 6),
    ]


def test_range_scan_excludes_boundaries():
    index = BPlusTreeIndex(
        "students_id_idx",
        "id",
    )

    for value in range(1, 11):
        index.insert(
            value,
            (1, value - 1),
        )

    scan = IndexScan(index)

    assert scan.range(
        3,
        7,
        include_start=False,
        include_end=False,
    ) == [
        (1, 3),
        (1, 4),
        (1, 5),
    ]


def test_range_scan_supports_open_start():
    index = BPlusTreeIndex(
        "students_id_idx",
        "id",
    )

    for value in range(1, 6):
        index.insert(
            value,
            (1, value - 1),
        )

    scan = IndexScan(index)

    assert scan.range(
        end_key=3,
    ) == [
        (1, 0),
        (1, 1),
        (1, 2),
    ]


def test_range_scan_supports_open_end():
    index = BPlusTreeIndex(
        "students_id_idx",
        "id",
    )

    for value in range(1, 6):
        index.insert(
            value,
            (1, value - 1),
        )

    scan = IndexScan(index)

    assert scan.range(
        start_key=3,
    ) == [
        (1, 2),
        (1, 3),
        (1, 4),
    ]


def test_range_scan_reversed_bounds_returns_empty():
    index = BPlusTreeIndex(
        "students_id_idx",
        "id",
    )

    for value in range(1, 6):
        index.insert(
            value,
            (1, value - 1),
        )

    scan = IndexScan(index)

    assert scan.range(
        5,
        2,
    ) == []


def test_all_returns_record_ids_in_index_order():
    index = BPlusTreeIndex(
        "students_id_idx",
        "id",
    )

    index.insert(
        103,
        (1, 2),
    )

    index.insert(
        101,
        (1, 0),
    )

    index.insert(
        102,
        (1, 1),
    )

    scan = IndexScan(index)

    assert scan.all() == [
        (1, 0),
        (1, 1),
        (1, 2),
    ]


def test_scan_does_not_expose_internal_record_id_list():
    index = BPlusTreeIndex(
        "students_id_idx",
        "id",
    )

    index.insert(
        101,
        (1, 0),
    )

    scan = IndexScan(index)

    result = scan.exact(
        101
    )

    result.append(
        (1, 999)
    )

    assert scan.exact(
        101
    ) == [(1, 0)]


def test_scan_requires_index():
    with pytest.raises(TypeError):
        IndexScan(object())


def test_memory_index_exact_scan():
    index = MemoryIndex(
        "students_id_idx",
        "id",
    )

    index.insert(
        101,
        (1, 0),
    )

    index.insert(
        102,
        (1, 1),
    )

    scan = IndexScan(index)

    assert scan.exact(
        102
    ) == [(1, 1)]


def test_memory_index_all_scan():
    index = MemoryIndex(
        "students_id_idx",
        "id",
    )

    index.insert(
        103,
        (1, 2),
    )

    index.insert(
        101,
        (1, 0),
    )

    index.insert(
        102,
        (1, 1),
    )

    scan = IndexScan(index)

    assert scan.all() == [
        (1, 0),
        (1, 1),
        (1, 2),
    ]