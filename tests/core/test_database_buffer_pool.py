from pathlib import Path

from jugaaddb.core.database import Database
from jugaaddb.core.schema import Column


def make_database(tmp_path: Path):
    path = tmp_path / "college.jdb"

    db = Database.create(
        str(path)
    )

    db.create_table(
        "students",
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
        ],
    )

    return db, path


def test_database_creates_buffer_pool_for_physical_table(
    tmp_path,
):
    db, _ = make_database(
        tmp_path
    )

    assert "students" in (
        db._buffer_pools
    )

    assert db._buffer_pools[
        "students"
    ] is not None

    db.close()


def test_database_table_reuses_buffer_pool(
    tmp_path,
):
    db, _ = make_database(
        tmp_path
    )

    first = db.table(
        "students"
    )

    second = db.table(
        "students"
    )

    assert first.physical_table is (
        second.physical_table
    )

    assert (
        first.physical_table.buffer_pool
        is db._buffer_pools["students"]
    )

    db.close()


def test_database_insert_uses_managed_buffer_pool(
    tmp_path,
):
    db, _ = make_database(
        tmp_path
    )

    table = db.table(
        "students"
    )

    table.insert(
        {
            "id": 1,
            "name": "Sayman",
        }
    )

    record_id = table.record_ids[0]

    buffer_pool = (
        db._buffer_pools["students"]
    )

    assert buffer_pool.contains(
        record_id[0]
    )

    db.close()


def test_database_managed_cache_records_hits(
    tmp_path,
):
    db, _ = make_database(
        tmp_path
    )

    table = db.table(
        "students"
    )

    table.insert(
        {
            "id": 1,
            "name": "Sayman",
        }
    )

    record_id = table.record_ids[0]

    buffer_pool = (
        db._buffer_pools["students"]
    )

    buffer_pool.clear()

    first = table.physical_table.read(
        record_id
    )

    second = table.physical_table.read(
        record_id
    )

    assert first == second

    assert buffer_pool.misses == 1
    assert buffer_pool.hits == 1

    db.close()


def test_database_flush_flushes_all_managed_pools(
    tmp_path,
):
    db, _ = make_database(
        tmp_path
    )

    table = db.table(
        "students"
    )

    table.insert(
        {
            "id": 1,
            "name": "Sayman",
        }
    )

    table.update(
        {
            "id": 1,
        },
        {
            "name": "Updated",
        },
    )

    buffer_pool = (
        db._buffer_pools["students"]
    )

    assert any(
        frame.dirty
        for frame in buffer_pool._frames.values()
    )

    db.flush()

    assert all(
        not frame.dirty
        for frame in buffer_pool._frames.values()
    )

    db.close()


def test_database_reopen_recreates_buffer_pool(
    tmp_path,
):
    db, path = make_database(
        tmp_path
    )

    table = db.table(
        "students"
    )

    table.insert(
        {
            "id": 1,
            "name": "Sayman",
        }
    )

    db.close()

    reopened = Database.open(
        str(path)
    )

    assert "students" in (
        reopened._buffer_pools
    )

    assert reopened._buffer_pools[
        "students"
    ] is not None

    reopened_table = reopened.table(
        "students"
    )

    assert reopened_table.select_all() == [
        {
            "id": 1,
            "name": "Sayman",
        }
    ]

    reopened.close()


def test_database_close_clears_managed_storage(
    tmp_path,
):
    db, _ = make_database(
        tmp_path
    )

    db.table(
        "students"
    )

    assert db._physical_tables
    assert db._buffer_pools

    db.close()

    assert db._physical_tables == {}
    assert db._buffer_pools == {}


def test_database_supports_multiple_managed_buffer_pools(
    tmp_path,
):
    path = tmp_path / "college.jdb"

    db = Database.create(
        str(path)
    )

    schema = [
        Column(
            "id",
            "INTEGER",
            primary_key=True,
            nullable=False,
        )
    ]

    db.create_table(
        "students",
        schema,
    )

    db.create_table(
        "teachers",
        schema,
    )

    assert set(
        db._buffer_pools.keys()
    ) == {
        "students",
        "teachers",
    }

    assert (
        db._buffer_pools["students"]
        is not db._buffer_pools["teachers"]
    )

    db.close()


def test_database_managed_buffer_pool_belongs_to_correct_file(
    tmp_path,
):
    db, _ = make_database(
        tmp_path
    )

    buffer_pool = (
        db._buffer_pools["students"]
    )

    physical_table = (
        db._physical_tables["students"]
    )

    assert (
        buffer_pool.file_manager.path
        == physical_table.file_manager.path
    )

    db.close()


def test_database_close_flushes_dirty_pages(
    tmp_path,
):
    db, path = make_database(
        tmp_path
    )

    table = db.table(
        "students"
    )

    table.insert(
        {
            "id": 1,
            "name": "BeforeClose",
        }
    )

    table.update(
        {
            "id": 1,
        },
        {
            "name": "AfterClose",
        },
    )

    db.close()

    reopened = Database.open(
        str(path)
    )

    table = reopened.table(
        "students"
    )

    assert table.select_all() == [
        {
            "id": 1,
            "name": "AfterClose",
        }
    ]

    reopened.close()