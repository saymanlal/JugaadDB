from jugaaddb.sql.ast import (
    BinaryExpression,
    CreateTableStatement,
    Identifier,
    InsertStatement,
    Literal,
    SelectStatement,
)
from jugaaddb.sql.lexer import Lexer
from jugaaddb.sql.parser import Parser


def parse(sql):
    return Parser(Lexer(sql).tokenize()).parse()


def test_select():
    statement = parse(
        "SELECT name, cgpa FROM students WHERE cgpa > 8.0;"
    )

    assert isinstance(statement, SelectStatement)
    assert statement.columns == (
        Identifier("name"),
        Identifier("cgpa"),
    )
    assert statement.table == Identifier("students")
    assert statement.where == BinaryExpression(
        left=Identifier("cgpa"),
        operator=">",
        right=Literal(8.0),
    )


def test_select_without_where():
    statement = parse("SELECT name FROM students;")

    assert statement == SelectStatement(
        columns=(Identifier("name"),),
        table=Identifier("students"),
        where=None,
    )


def test_select_all():
    statement = parse("SELECT * FROM students;")

    assert statement.columns == (Identifier("*"),)


def test_select_multiple_columns():
    statement = parse(
        "SELECT name, department, cgpa FROM students"
    )

    assert statement.columns == (
        Identifier("name"),
        Identifier("department"),
        Identifier("cgpa"),
    )


def test_select_integer_condition():
    statement = parse(
        "SELECT name FROM students WHERE cgpa >= 8;"
    )

    assert statement.where.operator == ">="
    assert statement.where.right == Literal(8)


def test_select_string_condition():
    statement = parse(
        "SELECT name FROM students WHERE department = 'CSE';"
    )

    assert statement.where == BinaryExpression(
        left=Identifier("department"),
        operator="=",
        right=Literal("CSE"),
    )


def test_select_null_condition():
    statement = parse(
        "SELECT name FROM students WHERE department = NULL;"
    )

    assert statement.where.right == Literal(None)


def test_insert():
    statement = parse(
        "INSERT INTO students (name, cgpa) VALUES ('Sayman', 8.5);"
    )

    assert isinstance(statement, InsertStatement)
    assert statement.table == Identifier("students")
    assert statement.columns == (
        Identifier("name"),
        Identifier("cgpa"),
    )
    assert statement.values == (
        Literal("Sayman"),
        Literal(8.5),
    )


def test_insert_integer():
    statement = parse(
        "INSERT INTO students (id, name) VALUES (1, 'Rahul')"
    )

    assert statement.values == (
        Literal(1),
        Literal("Rahul"),
    )


def test_insert_column_value_mismatch():
    try:
        parse(
            "INSERT INTO students (id, name) VALUES (1);"
        )
        assert False
    except SyntaxError as error:
        assert "columns" in str(error)


def test_create_table():
    statement = parse(
        """
        CREATE TABLE students (
            id INTEGER,
            name TEXT,
            cgpa FLOAT
        );
        """
    )

    assert isinstance(statement, CreateTableStatement)
    assert statement.table == Identifier("students")
    assert len(statement.columns) == 3
    assert statement.columns[0].name == Identifier("id")
    assert statement.columns[0].data_type == Identifier("INTEGER")
    assert statement.columns[1].data_type == Identifier("TEXT")
    assert statement.columns[2].data_type == Identifier("FLOAT")


def test_create_table_primary_key():
    statement = parse(
        """
        CREATE TABLE students (
            id INTEGER PRIMARY KEY,
            name TEXT
        )
        """
    )

    assert statement.columns[0].primary_key is True
    assert statement.columns[1].primary_key is False


def test_create_table_unique():
    statement = parse(
        """
        CREATE TABLE students (
            id INTEGER,
            email TEXT UNIQUE
        )
        """
    )

    assert statement.columns[1].unique is True


def test_missing_from():
    try:
        parse("SELECT name students")
        assert False
    except SyntaxError:
        pass


def test_missing_condition_operator():
    try:
        parse("SELECT name FROM students WHERE cgpa 8.0")
        assert False
    except SyntaxError:
        pass


def test_unsupported_statement():
    try:
        parse("DROP TABLE students")
        assert False
    except SyntaxError:
        pass