from jugaaddb.core.database import Database
from jugaaddb.core.schema import Column


def create_database(tmp_path):
    path = tmp_path / "college.jdb"

    database = Database.create(
        str(path)
    )

    database.create_table(
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
            Column(
                "marks",
                "FLOAT",
                nullable=False,
            ),
        ],
    )

    return database, path


def insert_students(
    database,
    count=10,
):
    table = database.table(
        "students"
    )

    for index in range(1, count + 1):
        table.insert(
            {
                "id": index,
                "name": f"Student-{index}",
                "marks": float(index * 10),
            }
        )


def test_sql_select_reads_physical_rows(
    tmp_path,
):
    database, _ = create_database(
        tmp_path
    )

    database.execute(
        "INSERT INTO students "
        "(id, name, marks) "
        "VALUES (1, 'Sayman', 95.0)"
    )

    result = database.execute(
        "SELECT * FROM students"
    )

    assert result.rows == (
        {
            "id": 1,
            "name": "Sayman",
            "marks": 95.0,
        },
    )


def test_sql_insert_creates_physical_record(
    tmp_path,
):
    database, _ = create_database(
        tmp_path
    )

    database.execute(
        "INSERT INTO students "
        "(id, name, marks) "
        "VALUES (1, 'A', 90.0)"
    )

    physical = (
        database._physical_tables[
            "students"
        ]
    )

    assert physical.count() == 1

    assert physical.scan()[0][1] == {
        "id": 1,
        "name": "A",
        "marks": 90.0,
    }


def test_sql_update_reaches_physical_storage(
    tmp_path,
):
    database, _ = create_database(
        tmp_path
    )

    database.execute(
        "INSERT INTO students "
        "(id, name, marks) "
        "VALUES (1, 'Before', 70.0)"
    )

    database.execute(
        "UPDATE students "
        "SET name = 'After', marks = 99.0 "
        "WHERE id = 1"
    )

    physical = (
        database._physical_tables[
            "students"
        ]
    )

    records = physical.scan()

    assert len(records) == 1

    assert records[0][1] == {
        "id": 1,
        "name": "After",
        "marks": 99.0,
    }


def test_sql_delete_reaches_physical_storage(
    tmp_path,
):
    database, _ = create_database(
        tmp_path
    )

    database.execute(
        "INSERT INTO students "
        "(id, name, marks) "
        "VALUES (1, 'A', 90.0)"
    )

    database.execute(
        "INSERT INTO students "
        "(id, name, marks) "
        "VALUES (2, 'B', 80.0)"
    )

    database.execute(
        "DELETE FROM students "
        "WHERE id = 1"
    )

    physical = (
        database._physical_tables[
            "students"
        ]
    )

    assert [
        row
        for _, row in physical.scan()
    ] == [
        {
            "id": 2,
            "name": "B",
            "marks": 80.0,
        }
    ]


def test_create_index_uses_physical_records(
    tmp_path,
):
    database, _ = create_database(
        tmp_path
    )

    insert_students(
        database,
        count=10,
    )

    result = database.execute(
        "CREATE INDEX idx_students_id "
        "ON students (id)"
    )

    assert result is not None

    index = database.index_manager.get_index(
        "students",
        "idx_students_id",
    )

    entries = index.scan()

    assert len(entries) == 10


def test_index_scan_resolves_physical_record(
    tmp_path,
):
    database, _ = create_database(
        tmp_path
    )

    insert_students(
        database,
        count=10,
    )

    database.execute(
        "CREATE INDEX idx_students_id "
        "ON students (id)"
    )

    result = database.execute(
        "SELECT * FROM students "
        "WHERE id = 7"
    )

    assert result.rows == (
        {
            "id": 7,
            "name": "Student-7",
            "marks": 70.0,
        },
    )


def test_index_scan_returns_correct_physical_record_id(
    tmp_path,
):
    database, _ = create_database(
        tmp_path
    )

    insert_students(
        database,
        count=10,
    )

    database.execute(
        "CREATE INDEX idx_students_id "
        "ON students (id)"
    )

    index = database.index_manager.get_index(
        "students",
        "idx_students_id",
    )

    record_ids = index.search(
        7
    )

    assert len(record_ids) == 1

    record_id = record_ids[0]

    physical = (
        database._physical_tables[
            "students"
        ]
    )

    assert physical.read(
        record_id
    ) == {
        "id": 7,
        "name": "Student-7",
        "marks": 70.0,
    }


def test_index_remains_correct_after_update(
    tmp_path,
):
    database, _ = create_database(
        tmp_path
    )

    insert_students(
        database,
        count=10,
    )

    database.execute(
        "CREATE INDEX idx_students_id "
        "ON students (id)"
    )

    database.execute(
        "UPDATE students "
        "SET marks = 999.0 "
        "WHERE id = 5"
    )

    result = database.execute(
        "SELECT * FROM students "
        "WHERE id = 5"
    )

    assert result.rows == (
        {
            "id": 5,
            "name": "Student-5",
            "marks": 999.0,
        },
    )


def test_index_remains_correct_after_delete(
    tmp_path,
):
    database, _ = create_database(
        tmp_path
    )

    insert_students(
        database,
        count=10,
    )

    database.execute(
        "CREATE INDEX idx_students_id "
        "ON students (id)"
    )

    database.execute(
        "DELETE FROM students "
        "WHERE id = 5"
    )

    result = database.execute(
        "SELECT * FROM students "
        "WHERE id = 5"
    )

    assert result.rows == ()

    index = database.index_manager.get_index(
        "students",
        "idx_students_id",
    )

    assert index.search(5) == []


def test_index_lookup_after_middle_delete(
    tmp_path,
):
    database, _ = create_database(
        tmp_path
    )

    insert_students(
        database,
        count=10,
    )

    database.execute(
        "CREATE INDEX idx_students_id "
        "ON students (id)"
    )

    database.execute(
        "DELETE FROM students "
        "WHERE id = 3"
    )

    result = database.execute(
        "SELECT * FROM students "
        "WHERE id = 8"
    )

    assert result.rows == (
        {
            "id": 8,
            "name": "Student-8",
            "marks": 80.0,
        },
    )


def test_indexed_query_after_database_reopen(
    tmp_path,
):
    database, path = create_database(
        tmp_path
    )

    insert_students(
        database,
        count=10,
    )

    database.execute(
        "CREATE INDEX idx_students_id "
        "ON students (id)"
    )

    original_ids = list(
        database.table(
            "students"
        ).record_ids
    )

    database.close()

    reopened = Database.open(
        str(path)
    )

    result = reopened.execute(
        "SELECT * FROM students "
        "WHERE id = 9"
    )

    assert result.rows == (
        {
            "id": 9,
            "name": "Student-9",
            "marks": 90.0,
        },
    )

    reopened_ids = list(
        reopened.table(
            "students"
        ).record_ids
    )

    assert reopened_ids == original_ids


def test_indexed_query_reads_from_physical_storage_after_reopen(
    tmp_path,
):
    database, path = create_database(
        tmp_path
    )

    insert_students(
        database,
        count=10,
    )

    database.execute(
        "CREATE INDEX idx_students_id "
        "ON students (id)"
    )

    database.close()

    reopened = Database.open(
        str(path)
    )

    physical = (
        reopened._physical_tables[
            "students"
        ]
    )

    index = reopened.index_manager.get_index(
        "students",
        "idx_students_id",
    )

    record_ids = index.search(
        6
    )

    assert len(record_ids) == 1

    assert physical.read(
        record_ids[0]
    ) == {
        "id": 6,
        "name": "Student-6",
        "marks": 60.0,
    }


def test_indexed_query_across_multiple_pages(
    tmp_path,
):
    database, _ = create_database(
        tmp_path
    )

    table = database.table(
        "students"
    )

    for index in range(1, 80):
        table.insert(
            {
                "id": index,
                "name": "x" * 100,
                "marks": float(index),
            }
        )

    database.execute(
        "CREATE INDEX idx_students_id "
        "ON students (id)"
    )

    result = database.execute(
        "SELECT * FROM students "
        "WHERE id = 73"
    )

    assert result.rows == (
        {
            "id": 73,
            "name": "x" * 100,
            "marks": 73.0,
        },
    )


def test_indexed_query_with_and_rechecks_condition(
    tmp_path,
):
    database, _ = create_database(
        tmp_path
    )

    insert_students(
        database,
        count=10,
    )

    database.execute(
        "CREATE INDEX idx_students_id "
        "ON students (id)"
    )

    result = database.execute(
        "SELECT * FROM students "
        "WHERE id = 7 AND marks = 70.0"
    )

    assert result.rows == (
        {
            "id": 7,
            "name": "Student-7",
            "marks": 70.0,
        },
    )


def test_indexed_query_with_and_rejects_non_matching_condition(
    tmp_path,
):
    database, _ = create_database(
        tmp_path
    )

    insert_students(
        database,
        count=10,
    )

    database.execute(
        "CREATE INDEX idx_students_id "
        "ON students (id)"
    )

    result = database.execute(
        "SELECT * FROM students "
        "WHERE id = 7 AND marks = 999.0"
    )

    assert result.rows == ()