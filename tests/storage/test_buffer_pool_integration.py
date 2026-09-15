from pathlib import Path

import pytest

from jugaaddb.core.schema import Column, Schema
from jugaaddb.storage.buffer_pool import BufferPool
from jugaaddb.storage.file_manager import FileManager
from jugaaddb.storage.record_manager import RecordManager


def create_manager(
    tmp_path: Path,
    capacity: int = 4,
):
    path = tmp_path / "records.jdb"

    file_manager = FileManager(
        str(path)
    )

    file_manager.create()

    schema = Schema(
        [
            Column(
                "id",
                "INTEGER",
                primary_key=True,
                nullable=False,
            ),
            Column(
                "name",
                "TEXT",
            ),
        ]
    )

    buffer_pool = BufferPool(
        file_manager,
        capacity=capacity,
    )

    record_manager = RecordManager(
        schema,
        file_manager,
        buffer_pool=buffer_pool,
    )

    return (
        file_manager,
        buffer_pool,
        record_manager,
    )


def test_record_manager_accepts_buffer_pool(
    tmp_path,
):
    _, buffer_pool, record_manager = (
        create_manager(tmp_path)
    )

    assert record_manager.buffer_pool is (
        buffer_pool
    )


def test_insert_uses_buffer_pool(
    tmp_path,
):
    _, buffer_pool, record_manager = (
        create_manager(tmp_path)
    )

    record_id = record_manager.insert(
        {
            "id": 1,
            "name": "Sayman",
        }
    )

    page_id, _ = record_id

    assert buffer_pool.contains(
        page_id
    )

    assert buffer_pool.size == 1


def test_repeated_read_hits_cache(
    tmp_path,
):
    _, buffer_pool, record_manager = (
        create_manager(tmp_path)
    )

    record_id = record_manager.insert(
        {
            "id": 1,
            "name": "Sayman",
        }
    )

    buffer_pool.clear()

    first = record_manager.read(
        record_id
    )

    second = record_manager.read(
        record_id
    )

    assert first == second
    assert buffer_pool.misses == 1
    assert buffer_pool.hits == 1


def test_update_marks_page_dirty(
    tmp_path,
):
    file_manager, buffer_pool, record_manager = (
        create_manager(tmp_path)
    )

    record_id = record_manager.insert(
        {
            "id": 1,
            "name": "Sayman",
        }
    )

    page_id, _ = record_id

    record_manager.update(
        record_id,
        {
            "id": 1,
            "name": "Updated",
        },
    )

    frame = buffer_pool._frames[
        page_id
    ]

    assert frame.dirty is True

    buffer_pool.flush_all()

    direct = file_manager.read_page(
        page_id
    )

    assert b"Updated" in direct.read()


def test_delete_uses_cached_page(
    tmp_path,
):
    _, buffer_pool, record_manager = (
        create_manager(tmp_path)
    )

    record_id = record_manager.insert(
        {
            "id": 1,
            "name": "Sayman",
        }
    )

    record_manager.read(
        record_id
    )

    misses_before = buffer_pool.misses

    record_manager.delete(
        record_id
    )

    assert buffer_pool.misses == (
        misses_before
    )

    with pytest.raises(ValueError):
        record_manager.read(
            record_id
        )


def test_restore_uses_cached_page(
    tmp_path,
):
    _, buffer_pool, record_manager = (
        create_manager(tmp_path)
    )

    record_id = record_manager.insert(
        {
            "id": 1,
            "name": "Sayman",
        }
    )

    record_manager.delete(
        record_id
    )

    record_manager.restore(
        record_id,
        {
            "id": 1,
            "name": "Restored",
        },
    )

    assert record_manager.read(
        record_id
    ) == {
        "id": 1,
        "name": "Restored",
    }

    assert buffer_pool.contains(
        record_id[0]
    )


def test_scan_reuses_cached_pages(
    tmp_path,
):
    _, buffer_pool, record_manager = (
        create_manager(tmp_path)
    )

    record_manager.insert(
        {
            "id": 1,
            "name": "One",
        }
    )

    record_manager.insert(
        {
            "id": 2,
            "name": "Two",
        }
    )

    buffer_pool.clear()

    first = record_manager.scan()

    misses_after_first = (
        buffer_pool.misses
    )

    second = record_manager.scan()

    assert first == second

    assert buffer_pool.misses == (
        misses_after_first
    )

    assert buffer_pool.hits >= 1


def test_buffer_pool_eviction_flushes_record_changes(
    tmp_path,
):
    _, buffer_pool, record_manager = (
        create_manager(
            tmp_path,
            capacity=1,
        )
    )

    record_ids = []

    for index in range(1, 10):
        record_id = record_manager.insert(
            {
                "id": index,
                "name": "x" * 1200,
            }
        )

        record_ids.append(
            record_id
        )

        if record_id[0] > 1:
            break

    assert len(record_ids) >= 4

    first_id = record_ids[0]
    first_page_id = first_id[0]

    second_page_record = next(
        record_id
        for record_id in record_ids
        if record_id[0] > 1
    )

    second_page_id = second_page_record[0]

    assert first_page_id != second_page_id

    assert buffer_pool.contains(
        first_page_id
    ) is False

    assert buffer_pool.contains(
        second_page_id
    ) is True

    assert record_manager.read(
        first_id
    ) == {
        "id": 1,
        "name": "x" * 1200,
    }


def test_wrong_file_manager_is_rejected(
    tmp_path,
):
    first_path = tmp_path / "first.jdb"
    second_path = tmp_path / "second.jdb"

    first_manager = FileManager(
        str(first_path)
    )

    second_manager = FileManager(
        str(second_path)
    )

    first_manager.create()
    second_manager.create()

    schema = Schema(
        [
            Column(
                "id",
                "INTEGER",
            )
        ]
    )

    buffer_pool = BufferPool(
        first_manager
    )

    with pytest.raises(ValueError):
        RecordManager(
            schema,
            second_manager,
            buffer_pool=buffer_pool,
        )


def test_non_buffer_pool_is_rejected(
    tmp_path,
):
    path = tmp_path / "records.jdb"

    file_manager = FileManager(
        str(path)
    )

    file_manager.create()

    schema = Schema(
        [
            Column(
                "id",
                "INTEGER",
            )
        ]
    )

    with pytest.raises(TypeError):
        RecordManager(
            schema,
            file_manager,
            buffer_pool="invalid",
        )