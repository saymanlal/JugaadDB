from jugaaddb.core.schema import Column, Schema
from jugaaddb.storage.buffer_pool import BufferPool
from jugaaddb.storage.file_manager import FileManager
from jugaaddb.storage.physical_table import PhysicalTable


def create_table(
    tmp_path,
    name="students",
    capacity=4,
):
    path = tmp_path / f"{name}.tbl"

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
                nullable=False,
            ),
        ]
    )

    buffer_pool = BufferPool(
        file_manager,
        capacity=capacity,
    )

    table = PhysicalTable(
        name,
        schema,
        file_manager,
        buffer_pool=buffer_pool,
    )

    return (
        table,
        file_manager,
        buffer_pool,
    )


def test_insert_returns_stable_physical_record_id(
    tmp_path,
):
    table, _, _ = create_table(
        tmp_path
    )

    first_id = table.insert(
        {
            "id": 1,
            "name": "Sayman",
        }
    )

    second_id = table.insert(
        {
            "id": 2,
            "name": "Rahul",
        }
    )

    assert isinstance(
        first_id,
        tuple,
    )

    assert isinstance(
        second_id,
        tuple,
    )

    assert first_id != second_id

    assert table.read(
        first_id
    ) == {
        "id": 1,
        "name": "Sayman",
    }


def test_record_ids_returns_only_live_records(
    tmp_path,
):
    table, _, _ = create_table(
        tmp_path
    )

    first_id = table.insert(
        {
            "id": 1,
            "name": "A",
        }
    )

    second_id = table.insert(
        {
            "id": 2,
            "name": "B",
        }
    )

    table.delete(first_id)

    assert table.record_ids() == [
        second_id
    ]


def test_deleted_record_id_is_not_reused(
    tmp_path,
):
    table, _, _ = create_table(
        tmp_path
    )

    first_id = table.insert(
        {
            "id": 1,
            "name": "A",
        }
    )

    second_id = table.insert(
        {
            "id": 2,
            "name": "B",
        }
    )

    table.delete(first_id)

    third_id = table.insert(
        {
            "id": 3,
            "name": "C",
        }
    )

    assert third_id != first_id
    assert third_id != second_id

    assert table.read(
        second_id
    ) == {
        "id": 2,
        "name": "B",
    }

    assert table.read(
        third_id
    ) == {
        "id": 3,
        "name": "C",
    }


def test_update_preserves_record_id(
    tmp_path,
):
    table, _, _ = create_table(
        tmp_path
    )

    record_id = table.insert(
        {
            "id": 1,
            "name": "Before",
        }
    )

    table.update(
        record_id,
        {
            "id": 1,
            "name": "After",
        },
    )

    assert table.read(
        record_id
    ) == {
        "id": 1,
        "name": "After",
    }

    assert record_id in table.record_ids()


def test_delete_does_not_shift_other_record_ids(
    tmp_path,
):
    table, _, _ = create_table(
        tmp_path
    )

    ids = [
        table.insert(
            {
                "id": index,
                "name": f"Student-{index}",
            }
        )
        for index in range(1, 6)
    ]

    table.delete(ids[2])

    remaining = table.record_ids()

    assert remaining == [
        ids[0],
        ids[1],
        ids[3],
        ids[4],
    ]

    assert table.read(
        ids[3]
    ) == {
        "id": 4,
        "name": "Student-4",
    }

    assert table.read(
        ids[4]
    ) == {
        "id": 5,
        "name": "Student-5",
    }


def test_exists_uses_physical_record_id(
    tmp_path,
):
    table, _, _ = create_table(
        tmp_path
    )

    record_id = table.insert(
        {
            "id": 1,
            "name": "A",
        }
    )

    assert table.exists(
        record_id
    ) is True

    table.delete(record_id)

    assert table.exists(
        record_id
    ) is False


def test_scan_record_ids_match_physical_rows(
    tmp_path,
):
    table, _, _ = create_table(
        tmp_path
    )

    ids = [
        table.insert(
            {
                "id": index,
                "name": f"N-{index}",
            }
        )
        for index in range(1, 8)
    ]

    scanned_ids = [
        record_id
        for record_id, _ in table.scan()
    ]

    assert scanned_ids == ids

    assert table.record_ids() == scanned_ids


def test_record_ids_survive_flush(
    tmp_path,
):
    table, _, buffer_pool = create_table(
        tmp_path
    )

    first_id = table.insert(
        {
            "id": 1,
            "name": "A",
        }
    )

    second_id = table.insert(
        {
            "id": 2,
            "name": "B",
        }
    )

    assert buffer_pool.dirty_count > 0

    table.flush()

    assert buffer_pool.dirty_count == 0

    assert table.record_ids() == [
        first_id,
        second_id,
    ]


def test_record_ids_survive_reopen(
    tmp_path,
):
    table, file_manager, buffer_pool = create_table(
        tmp_path
    )

    first_id = table.insert(
        {
            "id": 1,
            "name": "A",
        }
    )

    second_id = table.insert(
        {
            "id": 2,
            "name": "B",
        }
    )

    table.flush()

    reopened_manager = FileManager(
        str(table.path)
    )

    reopened_manager.open()

    reopened_pool = BufferPool(
        reopened_manager
    )

    reopened = PhysicalTable(
        "students",
        table.schema,
        reopened_manager,
        buffer_pool=reopened_pool,
    )

    assert reopened.record_ids() == [
        first_id,
        second_id,
    ]

    assert reopened.read(
        first_id
    ) == {
        "id": 1,
        "name": "A",
    }

    assert reopened.read(
        second_id
    ) == {
        "id": 2,
        "name": "B",
    }


def test_invalid_record_id_is_rejected(
    tmp_path,
):
    table, _, _ = create_table(
        tmp_path
    )

    invalid_ids = [
        None,
        1,
        [],
        (1,),
        (1, 2, 3),
        ("1", 0),
        (1, "0"),
        (0, 0),
        (-1, 0),
        (1, -1),
    ]

    for record_id in invalid_ids:
        try:
            table.read(record_id)
        except (
            TypeError,
            ValueError,
        ):
            pass
        else:
            raise AssertionError(
                f"Invalid RecordID accepted: {record_id!r}"
            )