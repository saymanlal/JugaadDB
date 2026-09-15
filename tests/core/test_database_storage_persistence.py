from jugaaddb.core.database import Database
from jugaaddb.core.schema import Column


def student_columns():
    return [
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
        Column(
            "marks",
            "FLOAT",
            nullable=False,
        ),
    ]


def create_database(tmp_path):
    path = tmp_path / "college.jdb"

    database = Database.create(
        str(path)
    )

    return database, path


def test_database_reopen_preserves_table(
    tmp_path,
):
    database, path = create_database(
        tmp_path
    )

    database.create_table(
        "students",
        student_columns(),
    )

    database.close()

    reopened = Database.open(
        str(path)
    )

    assert reopened.tables() == [
        "students"
    ]


def test_database_reopen_preserves_rows(
    tmp_path,
):
    database, path = create_database(
        tmp_path
    )

    table = database.create_table(
        "students",
        student_columns(),
    )

    table.insert(
        {
            "id": 1,
            "name": "Sayman",
            "marks": 91.5,
        }
    )

    table.insert(
        {
            "id": 2,
            "name": "Rahul",
            "marks": 88.0,
        }
    )

    database.close()

    reopened = Database.open(
        str(path)
    )

    table = reopened.table(
        "students"
    )

    assert table.select_all() == [
        {
            "id": 1,
            "name": "Sayman",
            "marks": 91.5,
        },
        {
            "id": 2,
            "name": "Rahul",
            "marks": 88.0,
        },
    ]


def test_database_reopen_preserves_record_ids(
    tmp_path,
):
    database, path = create_database(
        tmp_path
    )

    table = database.create_table(
        "students",
        student_columns(),
    )

    table.insert(
        {
            "id": 1,
            "name": "A",
            "marks": 90.0,
        }
    )

    table.insert(
        {
            "id": 2,
            "name": "B",
            "marks": 80.0,
        }
    )

    original_ids = list(
        table.record_ids
    )

    database.close()

    reopened = Database.open(
        str(path)
    )

    reopened_table = reopened.table(
        "students"
    )

    assert reopened_table.record_ids == (
        original_ids
    )


def test_database_reopen_preserves_update(
    tmp_path,
):
    database, path = create_database(
        tmp_path
    )

    table = database.create_table(
        "students",
        student_columns(),
    )

    table.insert(
        {
            "id": 1,
            "name": "Before",
            "marks": 70.0,
        }
    )

    table.update(
        {
            "id": 1,
        },
        {
            "name": "After",
            "marks": 95.0,
        },
    )

    database.close()

    reopened = Database.open(
        str(path)
    )

    assert reopened.table(
        "students"
    ).select_all() == [
        {
            "id": 1,
            "name": "After",
            "marks": 95.0,
        }
    ]


def test_database_reopen_preserves_delete(
    tmp_path,
):
    database, path = create_database(
        tmp_path
    )

    table = database.create_table(
        "students",
        student_columns(),
    )

    table.insert(
        {
            "id": 1,
            "name": "A",
            "marks": 90.0,
        }
    )

    table.insert(
        {
            "id": 2,
            "name": "B",
            "marks": 80.0,
        }
    )

    table.delete(
        {
            "id": 1,
        }
    )

    database.close()

    reopened = Database.open(
        str(path)
    )

    assert reopened.table(
        "students"
    ).select_all() == [
        {
            "id": 2,
            "name": "B",
            "marks": 80.0,
        }
    ]


def test_database_reopen_preserves_delete_without_id_shift(
    tmp_path,
):
    database, path = create_database(
        tmp_path
    )

    table = database.create_table(
        "students",
        student_columns(),
    )

    for index in range(1, 6):
        table.insert(
            {
                "id": index,
                "name": f"S-{index}",
                "marks": float(index),
            }
        )

    original_ids = list(
        table.record_ids
    )

    table.delete(
        {
            "id": 3,
        }
    )

    expected_ids = [
        original_ids[0],
        original_ids[1],
        original_ids[3],
        original_ids[4],
    ]

    database.close()

    reopened = Database.open(
        str(path)
    )

    reopened_table = reopened.table(
        "students"
    )

    assert reopened_table.record_ids == (
        expected_ids
    )


def test_database_reopen_preserves_multiple_tables(
    tmp_path,
):
    database, path = create_database(
        tmp_path
    )

    students = database.create_table(
        "students",
        student_columns(),
    )

    teachers = database.create_table(
        "teachers",
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

    students.insert(
        {
            "id": 1,
            "name": "Student",
            "marks": 90.0,
        }
    )

    teachers.insert(
        {
            "id": 1,
            "name": "Teacher",
        }
    )

    database.close()

    reopened = Database.open(
        str(path)
    )

    assert reopened.tables() == [
        "students",
        "teachers",
    ]

    assert reopened.table(
        "students"
    ).select_all() == [
        {
            "id": 1,
            "name": "Student",
            "marks": 90.0,
        }
    ]

    assert reopened.table(
        "teachers"
    ).select_all() == [
        {
            "id": 1,
            "name": "Teacher",
        }
    ]


def test_database_reopen_preserves_many_pages(
    tmp_path,
):
    database, path = create_database(
        tmp_path
    )

    table = database.create_table(
        "students",
        student_columns(),
    )

    for index in range(1, 80):
        table.insert(
            {
                "id": index,
                "name": "x" * 100,
                "marks": float(index),
            }
        )

    original_ids = list(
        table.record_ids
    )

    assert len(
        set(
            record_id[0]
            for record_id in original_ids
        )
    ) > 1

    database.close()

    reopened = Database.open(
        str(path)
    )

    reopened_table = reopened.table(
        "students"
    )

    assert len(
        reopened_table.select_all()
    ) == 79

    assert reopened_table.record_ids == (
        original_ids
    )


def test_database_reopen_after_explicit_flush(
    tmp_path,
):
    database, path = create_database(
        tmp_path
    )

    table = database.create_table(
        "students",
        student_columns(),
    )

    table.insert(
        {
            "id": 1,
            "name": "Flush",
            "marks": 99.0,
        }
    )

    database.flush()

    reopened = Database.open(
        str(path)
    )

    assert reopened.table(
        "students"
    ).select_all() == [
        {
            "id": 1,
            "name": "Flush",
            "marks": 99.0,
        }
    ]


def test_reopened_database_buffer_pools_start_clean(
    tmp_path,
):
    database, path = create_database(
        tmp_path
    )

    table = database.create_table(
        "students",
        student_columns(),
    )

    table.insert(
        {
            "id": 1,
            "name": "A",
            "marks": 90.0,
        }
    )

    database.close()

    reopened = Database.open(
        str(path)
    )

    assert len(
        reopened._buffer_pools
    ) == 1

    for buffer_pool in (
        reopened._buffer_pools.values()
    ):
        assert buffer_pool.dirty_count == 0


def test_database_reopen_preserves_physical_metadata(
    tmp_path,
):
    database, path = create_database(
        tmp_path
    )

    database.create_table(
        "students",
        student_columns(),
    )

    database.close()

    reopened = Database.open(
        str(path)
    )

    table_data = reopened.catalog.get(
        "students"
    )

    assert "physical" in table_data

    physical = table_data[
        "physical"
    ]

    assert physical[
        "format"
    ] == "slotted-page"

    assert isinstance(
        physical["path"],
        str,
    )

    assert physical["path"]


def test_database_reopen_keeps_data_after_second_close(
    tmp_path,
):
    database, path = create_database(
        tmp_path
    )

    table = database.create_table(
        "students",
        student_columns(),
    )

    table.insert(
        {
            "id": 1,
            "name": "Persistent",
            "marks": 100.0,
        }
    )

    database.close()

    reopened = Database.open(
        str(path)
    )

    assert reopened.table(
        "students"
    ).select_all() == [
        {
            "id": 1,
            "name": "Persistent",
            "marks": 100.0,
        }
    ]

    reopened.close()

    reopened_again = Database.open(
        str(path)
    )

    assert reopened_again.table(
        "students"
    ).select_all() == [
        {
            "id": 1,
            "name": "Persistent",
            "marks": 100.0,
        }
    ]


def test_database_reopen_preserves_mixed_operations(
    tmp_path,
):
    database, path = create_database(
        tmp_path
    )

    table = database.create_table(
        "students",
        student_columns(),
    )

    for index in range(1, 6):
        table.insert(
            {
                "id": index,
                "name": f"Student-{index}",
                "marks": float(index * 10),
            }
        )

    table.update(
        {
            "id": 2,
        },
        {
            "name": "Updated",
            "marks": 99.0,
        },
    )

    table.delete(
        {
            "id": 4,
        }
    )

    table.insert(
        {
            "id": 6,
            "name": "New",
            "marks": 60.0,
        }
    )

    expected = table.select_all()
    expected_ids = list(
        table.record_ids
    )

    database.close()

    reopened = Database.open(
        str(path)
    )

    reopened_table = reopened.table(
        "students"
    )

    assert reopened_table.select_all() == (
        expected
    )

    assert reopened_table.record_ids == (
        expected_ids
    )


def test_database_reopen_preserves_empty_table(
    tmp_path,
):
    database, path = create_database(
        tmp_path
    )

    database.create_table(
        "students",
        student_columns(),
    )

    database.close()

    reopened = Database.open(
        str(path)
    )

    table = reopened.table(
        "students"
    )

    assert table.select_all() == []

    assert table.record_ids == []

    assert len(
        table.select_all()
    ) == 0