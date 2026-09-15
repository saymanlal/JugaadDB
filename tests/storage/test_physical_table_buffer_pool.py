from pathlib import Path

import pytest

from jugaaddb.core.schema import Column, Schema
from jugaaddb.storage.buffer_pool import BufferPool
from jugaaddb.storage.file_manager import FileManager
from jugaaddb.storage.physical_table import PhysicalTable


def make_table(
    tmp_path: Path,
    capacity: int = 4,
):
    path = tmp_path / "students.tbl"

    file_manager = FileManager(
        str(path)
    )

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
                nullable=False,
            ),
        ]
    )

    buffer_pool = BufferPool(
        file_manager,
        capacity=capacity,
    )

    table = PhysicalTable(
        "students",
        schema,
        file_manager,
        buffer_pool=buffer_pool,
    )

    table.create()

    return (
        table,
        file_manager,
        buffer_pool,
    )


def test_physical_table_accepts_buffer_pool(
    tmp_path,
):
    table, _, buffer_pool = make_table(
        tmp_path
    )

    assert table.buffer_pool is buffer_pool

    assert (
        table.record_manager.buffer_pool
        is buffer_pool
    )


def test_insert_uses_physical_table_buffer_pool(
    tmp_path,
):
    table, _, buffer_pool = make_table(
        tmp_path
    )

    record_id = table.insert(
        {
            "id": 1,
            "name": "Sayman",
        }
    )

    assert buffer_pool.contains(
        record_id[0]
    )

    assert table.read(
        record_id
    ) == {
        "id": 1,
        "name": "Sayman",
    }


def test_repeated_reads_hit_physical_table_cache(
    tmp_path,
):
    table, _, buffer_pool = make_table(
        tmp_path
    )

    record_id = table.insert(
        {
            "id": 1,
            "name": "Sayman",
        }
    )

    buffer_pool.clear()

    first = table.read(
        record_id
    )

    second = table.read(
        record_id
    )

    assert first == second

    assert buffer_pool.misses == 1
    assert buffer_pool.hits == 1


def test_physical_table_update_uses_cache(
    tmp_path,
):
    table, _, buffer_pool = make_table(
        tmp_path
    )

    record_id = table.insert(
        {
            "id": 1,
            "name": "Sayman",
        }
    )

    table.update(
        record_id,
        {
            "id": 1,
            "name": "Updated",
        },
    )

    assert table.read(
        record_id
    ) == {
        "id": 1,
        "name": "Updated",
    }

    assert buffer_pool.contains(
        record_id[0]
    )


def test_physical_table_delete_uses_cache(
    tmp_path,
):
    table, _, buffer_pool = make_table(
        tmp_path
    )

    record_id = table.insert(
        {
            "id": 1,
            "name": "Sayman",
        }
    )

    table.delete(
        record_id
    )

    assert buffer_pool.contains(
        record_id[0]
    )

    with pytest.raises(ValueError):
        table.read(
            record_id
        )


def test_physical_table_restore_uses_cache(
    tmp_path,
):
    table, _, buffer_pool = make_table(
        tmp_path
    )

    record_id = table.insert(
        {
            "id": 1,
            "name": "Sayman",
        }
    )

    table.delete(
        record_id
    )

    table.restore(
        record_id,
        {
            "id": 1,
            "name": "Restored",
        },
    )

    assert table.read(
        record_id
    ) == {
        "id": 1,
        "name": "Restored",
    }

    assert buffer_pool.contains(
        record_id[0]
    )


def test_physical_table_scan_uses_cache(
    tmp_path,
):
    table, _, buffer_pool = make_table(
        tmp_path
    )

    table.insert(
        {
            "id": 1,
            "name": "Sayman",
        }
    )

    table.insert(
        {
            "id": 2,
            "name": "Rahul",
        }
    )

    buffer_pool.clear()

    first = table.scan()

    misses = buffer_pool.misses

    second = table.scan()

    assert first == second

    assert buffer_pool.misses == misses

    assert buffer_pool.hits >= 1


def test_physical_table_flush_persists_dirty_pages(
    tmp_path,
):
    table, file_manager, buffer_pool = (
        make_table(tmp_path)
    )

    record_id = table.insert(
        {
            "id": 1,
            "name": "Sayman",
        }
    )

    page_id = record_id[0]

    table.update(
        record_id,
        {
            "id": 1,
            "name": "Persisted",
        },
    )

    assert buffer_pool._frames[
        page_id
    ].dirty is True

    table.flush()

    assert buffer_pool._frames[
        page_id
    ].dirty is False

    page = file_manager.read_page(
        page_id
    )

    assert b"Persisted" in page.read()


def test_physical_table_rejects_wrong_buffer_pool(
    tmp_path,
):
    table_path = tmp_path / "students.tbl"
    other_path = tmp_path / "other.tbl"

    table_file_manager = FileManager(
        str(table_path)
    )

    other_file_manager = FileManager(
        str(other_path)
    )

    schema = Schema(
        [
            Column(
                "id",
                "INTEGER",
            )
        ]
    )

    buffer_pool = BufferPool(
        other_file_manager
    )

    with pytest.raises(ValueError):
        PhysicalTable(
            "students",
            schema,
            table_file_manager,
            buffer_pool=buffer_pool,
        )


def test_physical_table_rejects_invalid_buffer_pool(
    tmp_path,
):
    path = tmp_path / "students.tbl"

    file_manager = FileManager(
        str(path)
    )

    schema = Schema(
        [
            Column(
                "id",
                "INTEGER",
            )
        ]
    )

    with pytest.raises(TypeError):
        PhysicalTable(
            "students",
            schema,
            file_manager,
            buffer_pool="invalid",
        )