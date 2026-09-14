from jugaaddb.core.database import Database
from jugaaddb.core.schema import Column
from jugaaddb.sql.lexer import Lexer
from jugaaddb.sql.parser import Parser
from jugaaddb.sql.plan import Filter, IndexScan, Projection, TableScan
from jugaaddb.sql.planner import Planner


def build_database(tmp_path):
    database = Database.create(
        str(tmp_path / "smart_optimizer.jdb")
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
                "cgpa",
                "FLOAT",
                nullable=False,
            ),
        ],
    )

    table = database.table("students")

    table.insert(
        {
            "id": 1,
            "name": "A",
            "cgpa": 8.5,
        }
    )

    table.insert(
        {
            "id": 2,
            "name": "B",
            "cgpa": 9.1,
        }
    )

    table.insert(
        {
            "id": 3,
            "name": "C",
            "cgpa": 9.1,
        }
    )

    return database


def plan(database, sql):
    statement = Parser(
        Lexer(sql).tokenize()
    ).parse()

    return Planner(database).plan(statement)


def test_and_condition_uses_available_index(tmp_path):
    database = build_database(tmp_path)

    database.execute(
        "CREATE INDEX students_id_idx "
        "ON students (id);"
    )

    query_plan = plan(
        database,
        "SELECT * FROM students "
        "WHERE id = 2 AND cgpa = 9.1;",
    )

    assert isinstance(query_plan, Projection)
    assert isinstance(
        query_plan.source,
        IndexScan,
    )
    assert query_plan.source.column.name == "id"
    assert query_plan.source.value == 2


def test_and_condition_uses_cgpa_index_when_id_is_not_indexed(
    tmp_path,
):
    database = build_database(tmp_path)

    database.execute(
        "CREATE INDEX students_cgpa_idx "
        "ON students (cgpa);"
    )

    query_plan = plan(
        database,
        "SELECT * FROM students "
        "WHERE id = 2 AND cgpa = 9.1;",
    )

    assert isinstance(query_plan, Projection)
    assert isinstance(
        query_plan.source,
        IndexScan,
    )
    assert query_plan.source.column.name == "cgpa"
    assert query_plan.source.value == 9.1


def test_and_condition_without_indexes_uses_filter(
    tmp_path,
):
    database = build_database(tmp_path)

    query_plan = plan(
        database,
        "SELECT * FROM students "
        "WHERE id = 2 AND cgpa = 9.1;",
    )

    assert isinstance(query_plan, Projection)
    assert isinstance(
        query_plan.source,
        Filter,
    )
    assert isinstance(
        query_plan.source.source,
        TableScan,
    )


def test_or_condition_does_not_use_single_index(
    tmp_path,
):
    database = build_database(tmp_path)

    database.execute(
        "CREATE INDEX students_id_idx "
        "ON students (id);"
    )

    query_plan = plan(
        database,
        "SELECT * FROM students "
        "WHERE id = 2 OR cgpa = 9.1;",
    )

    assert isinstance(query_plan, Projection)
    assert isinstance(
        query_plan.source,
        Filter,
    )
    assert isinstance(
        query_plan.source.source,
        TableScan,
    )


def test_index_scan_rechecks_full_and_condition(
    tmp_path,
):
    database = build_database(tmp_path)

    database.execute(
        "CREATE INDEX students_cgpa_idx "
        "ON students (cgpa);"
    )

    result = database.execute(
        "SELECT * FROM students "
        "WHERE id = 2 AND cgpa = 9.1;"
    )

    assert result.rows == (
        {
            "id": 2,
            "name": "B",
            "cgpa": 9.1,
        },
    )


def test_index_scan_does_not_return_false_matches(
    tmp_path,
):
    database = build_database(tmp_path)

    database.execute(
        "CREATE INDEX students_cgpa_idx "
        "ON students (cgpa);"
    )

    result = database.execute(
        "SELECT * FROM students "
        "WHERE id = 1 AND cgpa = 9.1;"
    )

    assert result.rows == ()