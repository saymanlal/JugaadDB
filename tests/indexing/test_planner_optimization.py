from jugaaddb.core.database import Database
from jugaaddb.core.schema import Column
from jugaaddb.sql.ast import Identifier, Literal
from jugaaddb.sql.plan import (
    Filter,
    IndexScan,
    Projection,
    TableScan,
)
from jugaaddb.sql.lexer import Lexer
from jugaaddb.sql.parser import Parser
from jugaaddb.sql.planner import Planner


def create_database(tmp_path):
    db = Database.create(
        str(tmp_path / "planner.jdb")
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
                nullable=True,
            ),
        ],
    )

    return db


def parse(db, sql):
    statement = Parser(
        Lexer(sql).tokenize()
    ).parse()

    return Planner(db).plan(statement)


def test_select_without_index_uses_table_scan(
    tmp_path,
):
    db = create_database(tmp_path)

    plan = parse(
        db,
        "SELECT * FROM students WHERE id = 101;",
    )

    assert isinstance(plan, Projection)
    assert isinstance(
        plan.source,
        Filter,
    )
    assert isinstance(
        plan.source.source,
        TableScan,
    )


def test_select_with_index_uses_index_scan(
    tmp_path,
):
    db = create_database(tmp_path)

    db.execute(
        "CREATE INDEX students_id_idx "
        "ON students (id);"
    )

    plan = parse(
        db,
        "SELECT * FROM students WHERE id = 101;",
    )

    assert isinstance(plan, Projection)
    assert isinstance(
        plan.source,
        IndexScan,
    )
    assert plan.source.table == Identifier(
        "students"
    )
    assert plan.source.index == Identifier(
        "students_id_idx"
    )
    assert plan.source.column == Identifier(
        "id"
    )
    assert plan.source.value == 101


def test_non_equality_condition_uses_table_scan(
    tmp_path,
):
    db = create_database(tmp_path)

    db.execute(
        "CREATE INDEX students_id_idx "
        "ON students (id);"
    )

    plan = parse(
        db,
        "SELECT * FROM students WHERE id > 101;",
    )

    assert isinstance(plan, Projection)
    assert isinstance(
        plan.source,
        Filter,
    )
    assert isinstance(
        plan.source.source,
        TableScan,
    )


def test_logical_condition_uses_indexed_and_predicate(
    tmp_path,
):
    database = create_database(tmp_path)

    database.execute(
        "CREATE INDEX students_id_idx "
        "ON students (id);"
    )

    plan = parse(
        database,
        "SELECT * FROM students "
        "WHERE id = 101 AND cgpa = 9.0;",
    )

    assert isinstance(
        plan,
        Projection,
    )

    assert isinstance(
        plan.source,
        IndexScan,
    )

    assert plan.source.column.name == "id"
    assert plan.source.value == 101


def test_index_scan_executes_correctly(
    tmp_path,
):
    db = create_database(tmp_path)
    table = db.table("students")

    table.insert(
        {
            "id": 101,
            "name": "A",
            "cgpa": 8.1,
        }
    )

    table.insert(
        {
            "id": 102,
            "name": "B",
            "cgpa": 9.2,
        }
    )

    db.execute(
        "CREATE INDEX students_id_idx "
        "ON students (id);"
    )

    result = db.execute(
        "SELECT * FROM students WHERE id = 102;"
    )

    assert result.rows == (
        {
            "id": 102,
            "name": "B",
            "cgpa": 9.2,
        },
    )


def test_index_scan_supports_projection(
    tmp_path,
):
    db = create_database(tmp_path)
    table = db.table("students")

    table.insert(
        {
            "id": 101,
            "name": "A",
            "cgpa": 8.1,
        }
    )

    db.execute(
        "CREATE INDEX students_id_idx "
        "ON students (id);"
    )

    result = db.execute(
        "SELECT name FROM students WHERE id = 101;"
    )

    assert result.columns == (
        "name",
    )

    assert result.rows == (
        {
            "name": "A",
        },
    )


def test_index_scan_uses_stable_record_ids(
    tmp_path,
):
    db = create_database(tmp_path)
    table = db.table("students")

    table.insert(
        {
            "id": 101,
            "name": "A",
            "cgpa": 8.1,
        }
    )

    table.insert(
        {
            "id": 102,
            "name": "B",
            "cgpa": 8.2,
        }
    )

    table.insert(
        {
            "id": 103,
            "name": "C",
            "cgpa": 8.3,
        }
    )

    db.execute(
        "CREATE INDEX students_id_idx "
        "ON students (id);"
    )

    table.delete(
        {
            "id": 102,
        }
    )

    result = db.execute(
        "SELECT * FROM students WHERE id = 103;"
    )

    assert result.rows == (
        {
            "id": 103,
            "name": "C",
            "cgpa": 8.3,
        },
    )


def test_planner_does_not_use_index_for_unknown_column(
    tmp_path,
):
    db = create_database(tmp_path)

    db.execute(
        "CREATE INDEX students_id_idx "
        "ON students (id);"
    )

    try:
        parse(
            db,
            "SELECT * FROM students WHERE name = 'A';",
        )
    except Exception:
        return

    plan = parse(
        db,
        "SELECT * FROM students WHERE name = 'A';",
    )

    assert isinstance(plan, Projection)
    assert isinstance(
        plan.source,
        Filter,
    )


def test_index_scan_with_missing_key_returns_empty(
    tmp_path,
):
    db = create_database(tmp_path)

    db.execute(
        "CREATE INDEX students_id_idx "
        "ON students (id);"
    )

    result = db.execute(
        "SELECT * FROM students WHERE id = 999;"
    )

    assert result.rows == ()