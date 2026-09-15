from pathlib import Path

from jugaaddb.core.database import Database
from jugaaddb.core.schema import Column, Schema
from jugaaddb.indexing.btree import BPlusTreeIndex
from jugaaddb.storage.buffer_pool import BufferPool
from jugaaddb.storage.file_manager import FileManager
from jugaaddb.storage.physical_table import PhysicalTable


def student_schema():
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
    path = tmp_path / "regression.jdb"
    database = Database.create(str(path))
    database.create_table(
        "students",
        student_schema(),
    )
    return database, path


def insert_students(database, count=25):
    table = database.table("students")

    for student_id in range(1, count + 1):
        table.insert(
            {
                "id": student_id,
                "name": f"Student {student_id}",
                "marks": float(student_id) + 50.0,
            }
        )


def test_database_create_and_reopen_preserves_physical_rows(
    tmp_path,
):
    database, path = create_database(tmp_path)

    insert_students(database, 20)
    database.close()

    reopened = Database.open(str(path))

    rows = reopened.table(
        "students"
    ).select_all()

    assert len(rows) == 20
    assert rows[0]["id"] == 1
    assert rows[-1]["id"] == 20

    reopened.close()


def test_record_ids_survive_database_reopen(
    tmp_path,
):
    database, path = create_database(tmp_path)

    insert_students(database, 15)

    original_ids = list(
        database.table(
            "students"
        ).record_ids
    )

    database.close()

    reopened = Database.open(str(path))

    reopened_ids = list(
        reopened.table(
            "students"
        ).record_ids
    )

    assert reopened_ids == original_ids

    reopened.close()


def test_update_survives_database_reopen(
    tmp_path,
):
    database, path = create_database(tmp_path)

    insert_students(database, 10)

    database.execute(
        "UPDATE students "
        "SET name = 'Updated Student', marks = 99.5 "
        "WHERE id = 5"
    )

    database.close()

    reopened = Database.open(str(path))

    rows = reopened.table(
        "students"
    ).select_all()

    updated = [
        row
        for row in rows
        if row["id"] == 5
    ]

    assert len(updated) == 1
    assert updated[0]["name"] == "Updated Student"
    assert updated[0]["marks"] == 99.5

    reopened.close()


def test_delete_survives_database_reopen(
    tmp_path,
):
    database, path = create_database(tmp_path)

    insert_students(database, 10)

    database.execute(
        "DELETE FROM students "
        "WHERE id = 5"
    )

    database.close()

    reopened = Database.open(str(path))

    rows = reopened.table(
        "students"
    ).select_all()

    ids = [
        row["id"]
        for row in rows
    ]

    assert 5 not in ids
    assert len(rows) == 9

    reopened.close()


def test_multiple_tables_remain_isolated(
    tmp_path,
):
    path = tmp_path / "multi.jdb"

    database = Database.create(
        str(path)
    )

    database.create_table(
        "students",
        student_schema(),
    )

    database.create_table(
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

    database.table("students").insert(
        {
            "id": 1,
            "name": "Student",
            "marks": 88.0,
        }
    )

    database.table("teachers").insert(
        {
            "id": 1,
            "name": "Teacher",
        }
    )

    database.close()

    reopened = Database.open(
        str(path)
    )

    students = reopened.table(
        "students"
    ).select_all()

    teachers = reopened.table(
        "teachers"
    ).select_all()

    assert students == [
        {
            "id": 1,
            "name": "Student",
            "marks": 88.0,
        }
    ]

    assert teachers == [
        {
            "id": 1,
            "name": "Teacher",
        }
    ]

    reopened.close()


def test_large_table_spans_multiple_physical_pages(
    tmp_path,
):
    database, path = create_database(tmp_path)

    insert_students(database, 250)

    table = database.table(
        "students"
    )

    assert len(table.select_all()) == 250
    assert len(table.record_ids) == 250

    page_ids = {
        record_id[0]
        for record_id in table.record_ids
    }

    assert len(page_ids) > 1

    database.close()

    reopened = Database.open(
        str(path)
    )

    reopened_table = reopened.table(
        "students"
    )

    assert len(
        reopened_table.select_all()
    ) == 250

    assert len(
        reopened_table.record_ids
    ) == 250

    reopened.close()


def test_buffer_pool_dirty_pages_are_flushed_on_database_close(
    tmp_path,
):
    database, path = create_database(tmp_path)

    insert_students(database, 30)

    for buffer_pool in database._buffer_pools.values():
        assert buffer_pool.dirty_count > 0

    database.close()

    reopened = Database.open(
        str(path)
    )

    assert len(
        reopened.table(
            "students"
        ).select_all()
    ) == 30

    reopened.close()


def test_sql_insert_update_delete_survive_reopen(
    tmp_path,
):
    database, path = create_database(tmp_path)

    database.execute(
        "INSERT INTO students "
        "(id, name, marks) "
        "VALUES (1, 'Alice', 91.5)"
    )

    database.execute(
        "INSERT INTO students "
        "(id, name, marks) "
        "VALUES (2, 'Bob', 82.0)"
    )

    database.execute(
        "UPDATE students "
        "SET marks = 99.0 "
        "WHERE id = 1"
    )

    database.execute(
        "DELETE FROM students "
        "WHERE id = 2"
    )

    database.close()

    reopened = Database.open(
        str(path)
    )

    result = reopened.execute(
        "SELECT * FROM students"
    )

    assert result.rows == (
        {
            "id": 1,
            "name": "Alice",
            "marks": 99.0,
        },
    )

    reopened.close()


def test_btree_index_persists_and_restores(
    tmp_path,
):
    database, path = create_database(tmp_path)

    insert_students(database, 20)

    database.execute(
        "CREATE INDEX idx_students_id "
        "ON students (id)"
    )

    index = database.index_manager.get_index(
        "students",
        "idx_students_id",
    )

    assert isinstance(
        index,
        BPlusTreeIndex,
    )

    database.close()

    index_directory = Path(
        f"{path}.indexes"
    )

    index_path = (
        index_directory
        / "students"
        / "idx_students_id.idx"
    )

    assert index_path.exists()

    reopened = Database.open(
        str(path)
    )

    restored = (
        reopened.index_manager.get_index(
            "students",
            "idx_students_id",
        )
    )

    assert isinstance(
        restored,
        BPlusTreeIndex,
    )

    assert restored.column == "id"

    reopened.close()


def test_indexed_sql_query_survives_reopen(
    tmp_path,
):
    database, path = create_database(tmp_path)

    insert_students(database, 50)

    database.execute(
        "CREATE INDEX idx_students_id "
        "ON students (id)"
    )

    database.close()

    reopened = Database.open(
        str(path)
    )

    result = reopened.execute(
        "SELECT * FROM students "
        "WHERE id = 25"
    )

    assert result.rows == (
        {
            "id": 25,
            "name": "Student 25",
            "marks": 75.0,
        },
    )

    reopened.close()


def test_index_remains_correct_after_update_and_reopen(
    tmp_path,
):
    database, path = create_database(tmp_path)

    insert_students(database, 20)

    database.execute(
        "CREATE INDEX idx_students_id "
        "ON students (id)"
    )

    database.execute(
        "UPDATE students "
        "SET name = 'Changed' "
        "WHERE id = 10"
    )

    database.close()

    reopened = Database.open(
        str(path)
    )

    result = reopened.execute(
        "SELECT * FROM students "
        "WHERE id = 10"
    )

    assert result.rows == (
        {
            "id": 10,
            "name": "Changed",
            "marks": 60.0,
        },
    )

    reopened.close()


def test_index_remains_correct_after_delete_and_reopen(
    tmp_path,
):
    database, path = create_database(tmp_path)

    insert_students(database, 20)

    database.execute(
        "CREATE INDEX idx_students_id "
        "ON students (id)"
    )

    database.execute(
        "DELETE FROM students "
        "WHERE id = 10"
    )

    database.close()

    reopened = Database.open(
        str(path)
    )

    result = reopened.execute(
        "SELECT * FROM students "
        "WHERE id = 10"
    )

    assert result.rows == ()

    reopened.close()


def test_indexed_query_reads_current_physical_row(
    tmp_path,
):
    database, path = create_database(tmp_path)

    insert_students(database, 30)

    database.execute(
        "CREATE INDEX idx_students_id "
        "ON students (id)"
    )

    database.execute(
        "UPDATE students "
        "SET name = 'Physical Update', "
        "marks = 123.5 "
        "WHERE id = 17"
    )

    database.close()

    reopened = Database.open(
        str(path)
    )

    result = reopened.execute(
        "SELECT name, marks "
        "FROM students "
        "WHERE id = 17"
    )

    assert result.rows == (
        {
            "name": "Physical Update",
            "marks": 123.5,
        },
    )

    reopened.close()


def test_buffer_pool_reopen_keeps_physical_data_consistent(
    tmp_path,
):
    database, path = create_database(tmp_path)

    insert_students(database, 100)

    table = database.table(
        "students"
    )

    ids_before = list(
        table.record_ids
    )

    database.flush()
    database.close()

    reopened = Database.open(
        str(path)
    )

    reopened_table = reopened.table(
        "students"
    )

    ids_after = list(
        reopened_table.record_ids
    )

    assert ids_after == ids_before
    assert len(
        reopened_table.select_all()
    ) == 100

    reopened.close()


def test_physical_table_direct_lifecycle(
    tmp_path,
):
    path = tmp_path / "direct.tbl"

    file_manager = FileManager(
        str(path)
    )

    schema = Schema(
        student_schema()
    )

    physical_table = PhysicalTable(
        "students",
        schema,
        file_manager,
    )

    physical_table.create()

    record_id = physical_table.insert(
        {
            "id": 1,
            "name": "Direct",
            "marks": 77.0,
        }
    )

    assert physical_table.read(
        record_id
    ) == {
        "id": 1,
        "name": "Direct",
        "marks": 77.0,
    }

    physical_table.close()

    reopened_manager = FileManager(
        str(path)
    )

    reopened_manager.open()

    reopened_table = PhysicalTable(
        "students",
        schema,
        reopened_manager,
        buffer_pool=BufferPool(
            reopened_manager
        ),
    )

    assert reopened_table.read(
        record_id
    ) == {
        "id": 1,
        "name": "Direct",
        "marks": 77.0,
    }

    reopened_table.close()