import pytest

from jugaaddb.core.database import Database
from jugaaddb.core.schema import Column


def create_database(tmp_path):
    db = Database.create(
        str(tmp_path / "maintenance.jdb")
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
            Column(
                "cgpa",
                "FLOAT",
            ),
        ],
    )

    return db


def create_index(db):
    db.execute(
        "CREATE INDEX students_id_idx "
        "ON students (id);"
    )

    return db.index_manager.get_index(
        "students",
        "students_id_idx",
    )


def test_insert_automatically_updates_index(
    tmp_path,
):
    db = create_database(tmp_path)
    index = create_index(db)
    table = db.table("students")

    table.insert({
        "id": 101,
        "name": "Sayman",
        "cgpa": 8.7,
    })

    assert index.search(101) == [(1, 0)]


def test_multiple_inserts_update_index(
    tmp_path,
):
    db = create_database(tmp_path)
    index = create_index(db)
    table = db.table("students")

    table.insert({
        "id": 101,
        "name": "Sayman",
        "cgpa": 8.7,
    })

    table.insert({
        "id": 102,
        "name": "Rahul",
        "cgpa": 9.1,
    })

    table.insert({
        "id": 103,
        "name": "Aman",
        "cgpa": 8.4,
    })

    assert index.search(101) == [(1, 0)]
    assert index.search(102) == [(1, 1)]
    assert index.search(103) == [(1, 2)]


def test_delete_automatically_updates_index(
    tmp_path,
):
    db = create_database(tmp_path)
    index = create_index(db)
    table = db.table("students")

    table.insert({
        "id": 101,
        "name": "Sayman",
        "cgpa": 8.7,
    })

    table.insert({
        "id": 102,
        "name": "Rahul",
        "cgpa": 9.1,
    })

    deleted = table.delete({
        "id": 101,
    })

    assert deleted == 1
    assert index.search(101) == []
    assert index.search(102) == [(1, 1)]


def test_update_indexed_column_moves_index_entry(
    tmp_path,
):
    db = create_database(tmp_path)
    index = create_index(db)
    table = db.table("students")

    table.insert({
        "id": 101,
        "name": "Sayman",
        "cgpa": 8.7,
    })

    updated = table.update(
        {"id": 101},
        {"id": 201},
    )

    assert updated == 1
    assert index.search(101) == []
    assert index.search(201) == [(1, 0)]


def test_update_non_indexed_column_keeps_index(
    tmp_path,
):
    db = create_database(tmp_path)
    index = create_index(db)
    table = db.table("students")

    table.insert({
        "id": 101,
        "name": "Sayman",
        "cgpa": 8.7,
    })

    updated = table.update(
        {"id": 101},
        {"name": "Krushn"},
    )

    assert updated == 1
    assert index.search(101) == [(1, 0)]


def test_nullable_indexed_column_to_null_removes_index_entry(
    tmp_path,
):
    db = Database.create(
        str(tmp_path / "nullable_index.jdb")
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
            Column(
                "cgpa",
                "FLOAT",
            ),
        ],
    )

    db.execute(
        "CREATE INDEX students_cgpa_idx "
        "ON students (cgpa);"
    )

    index = db.index_manager.get_index(
        "students",
        "students_cgpa_idx",
    )

    table = db.table("students")

    table.insert({
        "id": 101,
        "name": "Sayman",
        "cgpa": 8.7,
    })

    updated = table.update(
        {"id": 101},
        {"cgpa": None},
    )

    assert updated == 1
    assert index.search(8.7) == []


def test_nullable_indexed_column_from_null_creates_index_entry(
    tmp_path,
):
    db = Database.create(
        str(tmp_path / "nullable_index_insert.jdb")
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
            Column(
                "cgpa",
                "FLOAT",
            ),
        ],
    )

    db.execute(
        "CREATE INDEX students_cgpa_idx "
        "ON students (cgpa);"
    )

    index = db.index_manager.get_index(
        "students",
        "students_cgpa_idx",
    )

    table = db.table("students")

    table.insert({
        "id": 101,
        "name": "Sayman",
        "cgpa": None,
    })

    assert index.search(8.7) == []

    updated = table.update(
        {"id": 101},
        {"cgpa": 8.7},
    )

    assert updated == 1
    assert index.search(8.7) == [(1, 0)]


def test_multiple_indexes_are_maintained(
    tmp_path,
):
    db = create_database(tmp_path)

    db.execute(
        "CREATE INDEX students_id_idx "
        "ON students (id);"
    )

    db.execute(
        "CREATE INDEX students_cgpa_idx "
        "ON students (cgpa);"
    )

    id_index = db.index_manager.get_index(
        "students",
        "students_id_idx",
    )

    cgpa_index = db.index_manager.get_index(
        "students",
        "students_cgpa_idx",
    )

    table = db.table("students")

    table.insert({
        "id": 101,
        "name": "Sayman",
        "cgpa": 8.7,
    })

    assert id_index.search(101) == [(1, 0)]
    assert cgpa_index.search(8.7) == [(1, 0)]

    table.update(
        {"id": 101},
        {"id": 202, "cgpa": 9.2},
    )

    assert id_index.search(101) == []
    assert id_index.search(202) == [(1, 0)]

    assert cgpa_index.search(8.7) == []
    assert cgpa_index.search(9.2) == [(1, 0)]


def test_delete_updates_all_indexes(
    tmp_path,
):
    db = create_database(tmp_path)

    db.execute(
        "CREATE INDEX students_id_idx "
        "ON students (id);"
    )

    db.execute(
        "CREATE INDEX students_cgpa_idx "
        "ON students (cgpa);"
    )

    id_index = db.index_manager.get_index(
        "students",
        "students_id_idx",
    )

    cgpa_index = db.index_manager.get_index(
        "students",
        "students_cgpa_idx",
    )

    table = db.table("students")

    table.insert({
        "id": 101,
        "name": "Sayman",
        "cgpa": 8.7,
    })

    table.delete({
        "id": 101,
    })

    assert id_index.search(101) == []
    assert cgpa_index.search(8.7) == []


def test_index_contains_duplicate_key_record_ids(
    tmp_path,
):
    db = Database.create(
        str(tmp_path / "duplicates.jdb")
    )

    db.create_table(
        "items",
        [
            Column(
                "id",
                "INTEGER",
                nullable=False,
            ),
            Column(
                "name",
                "TEXT",
            ),
        ],
    )

    db.execute(
        "CREATE INDEX items_id_idx "
        "ON items (id);"
    )

    index = db.index_manager.get_index(
        "items",
        "items_id_idx",
    )

    table = db.table("items")

    table.insert({
        "id": 10,
        "name": "A",
    })

    table.insert({
        "id": 10,
        "name": "B",
    })

    assert index.search(10) == [
        (1, 0),
        (1, 1),
    ]


def test_delete_one_duplicate_key_keeps_other_index_entry(
    tmp_path,
):
    db = Database.create(
        str(tmp_path / "duplicate_delete.jdb")
    )

    db.create_table(
        "items",
        [
            Column(
                "id",
                "INTEGER",
                nullable=False,
            ),
            Column(
                "name",
                "TEXT",
            ),
        ],
    )

    db.execute(
        "CREATE INDEX items_id_idx "
        "ON items (id);"
    )

    index = db.index_manager.get_index(
        "items",
        "items_id_idx",
    )

    table = db.table("items")

    table.insert({
        "id": 10,
        "name": "A",
    })

    table.insert({
        "id": 10,
        "name": "B",
    })

    table.delete({
        "name": "A",
    })

    assert index.search(10) == [(1, 1)]


def test_drop_index_stops_automatic_maintenance(
    tmp_path,
):
    db = create_database(tmp_path)

    db.execute(
        "CREATE INDEX students_id_idx "
        "ON students (id);"
    )

    index = db.index_manager.get_index(
        "students",
        "students_id_idx",
    )

    table = db.table("students")

    table.insert({
        "id": 101,
        "name": "Sayman",
        "cgpa": 8.7,
    })

    db.index_manager.drop_index(
        "students",
        "students_id_idx",
    )

    table.insert({
        "id": 102,
        "name": "Rahul",
        "cgpa": 9.1,
    })

    assert index.search(101) == [(1, 0)]
    assert index.search(102) == []


def test_no_index_does_not_change_table_behavior(
    tmp_path,
):
    db = create_database(tmp_path)
    table = db.table("students")

    table.insert({
        "id": 101,
        "name": "Sayman",
        "cgpa": 8.7,
    })

    table.update(
        {"id": 101},
        {"name": "Rahul"},
    )

    table.delete({
        "id": 101,
    })

    assert table.select_all() == []


def test_unknown_update_column_still_fails(
    tmp_path,
):
    db = create_database(tmp_path)
    create_index(db)

    table = db.table("students")

    table.insert({
        "id": 101,
        "name": "Sayman",
        "cgpa": 8.7,
    })

    with pytest.raises(ValueError):
        table.update(
            {"id": 101},
            {"unknown": "value"},
        )

    assert index_search(
        db,
        "students_id_idx",
        101,
    ) == [(1, 0)]


def index_search(
    db,
    index_name,
    key,
):
    return db.index_manager.get_index(
        "students",
        index_name,
    ).search(key)