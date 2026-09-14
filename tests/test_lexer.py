import pytest

from jugaaddb.sql.lexer import Lexer
from jugaaddb.sql.tokens import TokenType


def types(tokens):
    return [token.type for token in tokens]


def values(tokens):
    return [token.value for token in tokens]


def test_select_query():
    tokens = Lexer(
        "SELECT name, cgpa FROM students WHERE cgpa > 8.0;"
    ).tokenize()

    assert types(tokens) == [
        TokenType.SELECT,
        TokenType.IDENTIFIER,
        TokenType.COMMA,
        TokenType.IDENTIFIER,
        TokenType.FROM,
        TokenType.IDENTIFIER,
        TokenType.WHERE,
        TokenType.IDENTIFIER,
        TokenType.GREATER_THAN,
        TokenType.FLOAT,
        TokenType.SEMICOLON,
        TokenType.EOF,
    ]


def test_keywords_are_case_insensitive():
    tokens = Lexer("select FROM WhErE").tokenize()

    assert types(tokens) == [
        TokenType.SELECT,
        TokenType.FROM,
        TokenType.WHERE,
        TokenType.EOF,
    ]


def test_identifier_preserves_value():
    tokens = Lexer("student_name").tokenize()

    assert tokens[0].type == TokenType.IDENTIFIER
    assert tokens[0].value == "student_name"


def test_integer():
    tokens = Lexer("123 4567").tokenize()

    assert types(tokens) == [
        TokenType.INTEGER,
        TokenType.INTEGER,
        TokenType.EOF,
    ]

    assert values(tokens) == ["123", "4567", ""]


def test_float():
    tokens = Lexer("8.5 10.25").tokenize()

    assert types(tokens) == [
        TokenType.FLOAT,
        TokenType.FLOAT,
        TokenType.EOF,
    ]


def test_strings():
    tokens = Lexer("'Sayman' \"GGITS\"").tokenize()

    assert types(tokens) == [
        TokenType.STRING,
        TokenType.STRING,
        TokenType.EOF,
    ]

    assert values(tokens) == ["Sayman", "GGITS", ""]


def test_string_escape():
    tokens = Lexer(r"'hello\nworld'").tokenize()

    assert tokens[0].type == TokenType.STRING
    assert tokens[0].value == "hello\nworld"


def test_comparison_operators():
    tokens = Lexer("= != < <= > >=").tokenize()

    assert types(tokens) == [
        TokenType.EQUAL,
        TokenType.NOT_EQUAL,
        TokenType.LESS_THAN,
        TokenType.LESS_EQUAL,
        TokenType.GREATER_THAN,
        TokenType.GREATER_EQUAL,
        TokenType.EOF,
    ]


def test_arithmetic_operators():
    tokens = Lexer("+ - * /").tokenize()

    assert types(tokens) == [
        TokenType.PLUS,
        TokenType.MINUS,
        TokenType.MULTIPLY,
        TokenType.DIVIDE,
        TokenType.EOF,
    ]


def test_punctuation():
    tokens = Lexer("(name, cgpa);").tokenize()

    assert types(tokens) == [
        TokenType.LEFT_PAREN,
        TokenType.IDENTIFIER,
        TokenType.COMMA,
        TokenType.IDENTIFIER,
        TokenType.RIGHT_PAREN,
        TokenType.SEMICOLON,
        TokenType.EOF,
    ]


def test_whitespace_is_ignored():
    tokens = Lexer("  SELECT   name \n FROM\tstudents  ").tokenize()

    assert types(tokens) == [
        TokenType.SELECT,
        TokenType.IDENTIFIER,
        TokenType.FROM,
        TokenType.IDENTIFIER,
        TokenType.EOF,
    ]


def test_all_phase_two_keywords():
    sql = """
    SELECT FROM WHERE INSERT INTO VALUES
    CREATE TABLE UPDATE SET DELETE AND OR
    ORDER BY LIMIT PRIMARY KEY UNIQUE NULL
    """

    tokens = Lexer(sql).tokenize()

    assert all(
        token.type != TokenType.IDENTIFIER
        for token in tokens[:-1]
    )


def test_invalid_character():
    with pytest.raises(SyntaxError):
        Lexer("SELECT @name").tokenize()


def test_invalid_exclamation():
    with pytest.raises(SyntaxError):
        Lexer("SELECT ! name").tokenize()


def test_invalid_float():
    with pytest.raises(SyntaxError):
        Lexer("12.34.56").tokenize()


def test_trailing_dot():
    with pytest.raises(SyntaxError):
        Lexer("12.").tokenize()


def test_unterminated_string():
    with pytest.raises(SyntaxError):
        Lexer("'Sayman").tokenize()


def test_non_string_input():
    with pytest.raises(TypeError):
        Lexer(123).tokenize()