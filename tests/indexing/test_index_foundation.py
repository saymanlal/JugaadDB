import pytest

from jugaaddb.indexing import (
    IndexManager,
    MemoryIndex,
)


def test_memory_index_insert_and_search():
    index = MemoryIndex("idx_students_id", "id")

    index.insert(101, (1, 0))
    index.insert(102, (1, 1))

    assert index.search(101) == [(1, 0)]
    assert index.search(102) == [(1, 1)]
    assert index.search(999) == []


def test_memory_index_supports_duplicate_keys():
    index = MemoryIndex("idx_students_department", "department")

    index.insert("CSE", (1, 0))
    index.insert("CSE", (1, 1))

    assert index.search("CSE") == [(1, 0), (1, 1)]


def test_memory_index_rejects_duplicate_record_id():
    index = MemoryIndex("idx_students_id", "id")

    index.insert(101, (1, 0))

    with pytest.raises(ValueError):
        index.insert(101, (1, 0))


def test_memory_index_delete():
    index = MemoryIndex("idx_students_id", "id")

    index.insert(101, (1, 0))
    index.insert(102, (1, 1))

    index.delete(101, (1, 0))

    assert index.search(101) == []
    assert index.search(102) == [(1, 1)]


def test_memory_index_delete_one_duplicate_key():
    index = MemoryIndex("idx_students_department", "department")

    index.insert("CSE", (1, 0))
    index.insert("CSE", (1, 1))

    index.delete("CSE", (1, 0))

    assert index.search("CSE") == [(1, 1)]


def test_memory_index_scan():
    index = MemoryIndex("idx_students_id", "id")

    index.insert(103, (2, 0))
    index.insert(101, (1, 0))
    index.insert(102, (1, 1))

    entries = index.scan()

    assert [(entry.key, entry.record_id) for entry in entries] == [
        (101, (1, 0)),
        (102, (1, 1)),
        (103, (2, 0)),
    ]


def test_index_manager_create_and_get():
    manager = IndexManager()

    index = manager.create_index(
        "students",
        "idx_students_id",
        "id",
    )

    assert manager.get_index(
        "students",
        "idx_students_id",
    ) is index


def test_index_manager_lists_indexes():
    manager = IndexManager()

    manager.create_index(
        "students",
        "idx_students_name",
        "name",
    )

    manager.create_index(
        "students",
        "idx_students_id",
        "id",
    )

    assert manager.list_indexes("students") == [
        "idx_students_id",
        "idx_students_name",
    ]


def test_index_manager_filters_by_column():
    manager = IndexManager()

    manager.create_index(
        "students",
        "idx_students_id",
        "id",
    )

    manager.create_index(
        "students",
        "idx_students_name",
        "name",
    )

    indexes = manager.indexes_for_column(
        "students",
        "id",
    )

    assert len(indexes) == 1
    assert indexes[0].name == "idx_students_id"


def test_index_manager_rejects_duplicate_index_name():
    manager = IndexManager()

    manager.create_index(
        "students",
        "idx_students_id",
        "id",
    )

    with pytest.raises(ValueError):
        manager.create_index(
            "students",
            "idx_students_id",
            "id",
        )


def test_index_manager_drop():
    manager = IndexManager()

    manager.create_index(
        "students",
        "idx_students_id",
        "id",
    )

    manager.drop_index(
        "students",
        "idx_students_id",
    )

    assert manager.list_indexes("students") == []


def test_index_manager_missing_index():
    manager = IndexManager()

    with pytest.raises(ValueError):
        manager.get_index(
            "students",
            "missing",
        )


def test_memory_index_rejects_invalid_record_id():
    index = MemoryIndex("idx_students_id", "id")

    with pytest.raises(TypeError):
        index.insert(101, (1,))

    with pytest.raises(ValueError):
        index.insert(101, (0, 1))

    with pytest.raises(TypeError):
        index.insert(101, ("1", 1))