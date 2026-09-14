from jugaaddb.sql.ast import (
    Assignment,
    BinaryExpression,
    ColumnDefinition,
    CreateTableStatement,
    DeleteStatement,
    Identifier,
    InsertStatement,
    Literal,
    SelectStatement,
    UpdateStatement,
)
from jugaaddb.sql.plan import (
    CreateTablePlan,
    DeletePlan,
    Filter,
    InsertPlan,
    Projection,
    TableScan,
    UpdatePlan,
)
from jugaaddb.sql.planner import Planner


def test_select_plan():
    statement = SelectStatement(
        columns=(
            Identifier("name"),
            Identifier("cgpa"),
        ),
        table=Identifier("students"),
    )

    plan = Planner().plan(statement)

    assert plan == Projection(
        source=TableScan(
            table=Identifier("students"),
        ),
        columns=(
            Identifier("name"),
            Identifier("cgpa"),
        ),
    )


def test_select_plan_with_filter():
    condition = BinaryExpression(
        left=Identifier("cgpa"),
        operator=">",
        right=Literal(8.0),
    )

    statement = SelectStatement(
        columns=(Identifier("name"),),
        table=Identifier("students"),
        where=condition,
    )

    plan = Planner().plan(statement)

    assert plan == Projection(
        source=Filter(
            source=TableScan(
                table=Identifier("students"),
            ),
            condition=condition,
        ),
        columns=(Identifier("name"),),
    )


def test_select_all_plan():
    statement = SelectStatement(
        columns=(Identifier("*"),),
        table=Identifier("students"),
    )

    plan = Planner().plan(statement)

    assert isinstance(plan, Projection)
    assert plan.columns == (Identifier("*"),)
    assert isinstance(plan.source, TableScan)


def test_insert_plan():
    statement = InsertStatement(
        table=Identifier("students"),
        columns=(
            Identifier("name"),
            Identifier("cgpa"),
        ),
        values=(
            Literal("Sayman"),
            Literal(8.5),
        ),
    )

    plan = Planner().plan(statement)

    assert plan == InsertPlan(
        table=Identifier("students"),
        columns=(
            Identifier("name"),
            Identifier("cgpa"),
        ),
        values=(
            Literal("Sayman"),
            Literal(8.5),
        ),
    )


def test_update_plan():
    assignment = Assignment(
        column=Identifier("cgpa"),
        value=Literal(9.5),
    )

    condition = BinaryExpression(
        left=Identifier("id"),
        operator="=",
        right=Literal(1),
    )

    statement = UpdateStatement(
        table=Identifier("students"),
        assignments=(assignment,),
        where=condition,
    )

    plan = Planner().plan(statement)

    assert plan == UpdatePlan(
        source=Filter(
            source=TableScan(
                table=Identifier("students"),
            ),
            condition=condition,
        ),
        assignments=(assignment,),
    )


def test_update_without_filter():
    assignment = Assignment(
        column=Identifier("cgpa"),
        value=Literal(9.5),
    )

    statement = UpdateStatement(
        table=Identifier("students"),
        assignments=(assignment,),
    )

    plan = Planner().plan(statement)

    assert plan == UpdatePlan(
        source=TableScan(
            table=Identifier("students"),
        ),
        assignments=(assignment,),
    )


def test_delete_plan():
    condition = BinaryExpression(
        left=Identifier("id"),
        operator="=",
        right=Literal(1),
    )

    statement = DeleteStatement(
        table=Identifier("students"),
        where=condition,
    )

    plan = Planner().plan(statement)

    assert plan == DeletePlan(
        source=Filter(
            source=TableScan(
                table=Identifier("students"),
            ),
            condition=condition,
        )
    )


def test_delete_without_filter():
    statement = DeleteStatement(
        table=Identifier("students"),
    )

    plan = Planner().plan(statement)

    assert plan == DeletePlan(
        source=TableScan(
            table=Identifier("students"),
        )
    )


def test_create_table_plan():
    columns = (
        ColumnDefinition(
            name=Identifier("id"),
            data_type=Identifier("INTEGER"),
            primary_key=True,
        ),
        ColumnDefinition(
            name=Identifier("name"),
            data_type=Identifier("TEXT"),
        ),
    )

    statement = CreateTableStatement(
        table=Identifier("students"),
        columns=columns,
    )

    plan = Planner().plan(statement)

    assert plan == CreateTablePlan(
        table=Identifier("students"),
        columns=columns,
    )


def test_unsupported_ast_node():
    try:
        Planner().plan(object())
        assert False
    except TypeError as error:
        assert "Unsupported AST node" in str(error)