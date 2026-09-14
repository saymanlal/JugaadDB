from .tokens import Token, TokenType


class Lexer:
    KEYWORDS = {
        "SELECT": TokenType.SELECT,
        "FROM": TokenType.FROM,
        "WHERE": TokenType.WHERE,
        "INSERT": TokenType.INSERT,
        "INTO": TokenType.INTO,
        "VALUES": TokenType.VALUES,
        "CREATE": TokenType.CREATE,
        "TABLE": TokenType.TABLE,
        "UPDATE": TokenType.UPDATE,
        "SET": TokenType.SET,
        "DELETE": TokenType.DELETE,
        "AND": TokenType.AND,
        "OR": TokenType.OR,
        "ORDER": TokenType.ORDER,
        "BY": TokenType.BY,
        "LIMIT": TokenType.LIMIT,
        "PRIMARY": TokenType.PRIMARY,
        "KEY": TokenType.KEY,
        "UNIQUE": TokenType.UNIQUE,
        "NULL": TokenType.NULL,
    }

    SINGLE_CHAR_TOKENS = {
        "=": TokenType.EQUAL,
        "<": TokenType.LESS_THAN,
        ">": TokenType.GREATER_THAN,
        "+": TokenType.PLUS,
        "-": TokenType.MINUS,
        "*": TokenType.MULTIPLY,
        "/": TokenType.DIVIDE,
        ",": TokenType.COMMA,
        "(": TokenType.LEFT_PAREN,
        ")": TokenType.RIGHT_PAREN,
        ";": TokenType.SEMICOLON,
    }

    def __init__(self, sql: str):
        if not isinstance(sql, str):
            raise TypeError("SQL query must be a string.")
        self.sql = sql
        self.position = 0
        self.length = len(sql)

    def tokenize(self) -> list[Token]:
        tokens = []

        while self.position < self.length:
            char = self.sql[self.position]

            if char.isspace():
                self.position += 1
                continue

            if char in ("'", '"'):
                tokens.append(self._read_string())
                continue

            if char.isdigit():
                tokens.append(self._read_number())
                continue

            if char.isalpha() or char == "_":
                tokens.append(self._read_identifier())
                continue

            if char in ("!", "<", ">"):
                tokens.append(self._read_comparison_operator())
                continue

            if char in self.SINGLE_CHAR_TOKENS:
                tokens.append(
                    Token(
                        self.SINGLE_CHAR_TOKENS[char],
                        char,
                        self.position,
                    )
                )
                self.position += 1
                continue

            raise SyntaxError(
                f"Unexpected character '{char}' at position {self.position}."
            )

        tokens.append(Token(TokenType.EOF, "", self.position))
        return tokens

    def _read_identifier(self) -> Token:
        start = self.position

        while self.position < self.length:
            char = self.sql[self.position]

            if char.isalnum() or char == "_":
                self.position += 1
            else:
                break

        value = self.sql[start:self.position]
        token_type = self.KEYWORDS.get(value.upper(), TokenType.IDENTIFIER)

        return Token(token_type, value, start)

    def _read_number(self) -> Token:
        start = self.position
        decimal_count = 0

        while self.position < self.length:
            char = self.sql[self.position]

            if char.isdigit():
                self.position += 1
                continue

            if char == ".":
                decimal_count += 1
                if decimal_count > 1:
                    raise SyntaxError(
                        f"Invalid number at position {start}."
                    )
                self.position += 1
                continue

            break

        value = self.sql[start:self.position]

        if value.endswith("."):
            raise SyntaxError(
                f"Invalid number at position {start}."
            )

        token_type = (
            TokenType.FLOAT
            if decimal_count == 1
            else TokenType.INTEGER
        )

        return Token(token_type, value, start)

    def _read_string(self) -> Token:
        quote = self.sql[self.position]
        start = self.position
        self.position += 1
        characters = []

        while self.position < self.length:
            char = self.sql[self.position]

            if char == "\\":
                if self.position + 1 >= self.length:
                    raise SyntaxError(
                        f"Unterminated string at position {start}."
                    )

                next_char = self.sql[self.position + 1]

                if next_char == "n":
                    characters.append("\n")
                elif next_char == "t":
                    characters.append("\t")
                else:
                    characters.append(next_char)

                self.position += 2
                continue

            if char == quote:
                self.position += 1
                return Token(
                    TokenType.STRING,
                    "".join(characters),
                    start,
                )

            characters.append(char)
            self.position += 1

        raise SyntaxError(
            f"Unterminated string at position {start}."
        )

    def _read_comparison_operator(self) -> Token:
        start = self.position
        char = self.sql[self.position]

        if char == "!":
            if self.position + 1 < self.length:
                if self.sql[self.position + 1] == "=":
                    self.position += 2
                    return Token(TokenType.NOT_EQUAL, "!=", start)

            raise SyntaxError(
                f"Unexpected character '!' at position {start}."
            )

        if char == "<":
            if self.position + 1 < self.length:
                if self.sql[self.position + 1] == "=":
                    self.position += 2
                    return Token(TokenType.LESS_EQUAL, "<=", start)

            self.position += 1
            return Token(TokenType.LESS_THAN, "<", start)

        if char == ">":
            if self.position + 1 < self.length:
                if self.sql[self.position + 1] == "=":
                    self.position += 2
                    return Token(TokenType.GREATER_EQUAL, ">=", start)

            self.position += 1
            return Token(TokenType.GREATER_THAN, ">", start)

        raise SyntaxError(
            f"Invalid comparison operator at position {start}."
        )