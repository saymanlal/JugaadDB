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
        "NOT": TokenType.NOT,
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
            raise TypeError("SQL must be a string.")

        self.sql = sql
        self.position = 0

    def tokenize(self) -> list[Token]:
        tokens = []

        while self.position < len(self.sql):
            char = self.sql[self.position]

            if char.isspace():
                self.position += 1
                continue

            if char.isalpha() or char == "_":
                tokens.append(
                    self._read_identifier_or_keyword()
                )
                continue

            if char.isdigit():
                tokens.append(
                    self._read_number()
                )
                continue

            if char in ("'", '"'):
                tokens.append(
                    self._read_string(char)
                )
                continue

            token = self._read_operator_or_symbol()

            if token is not None:
                tokens.append(token)
                continue

            raise SyntaxError(
                f"Unexpected character '{char}' "
                f"at position {self.position}."
            )

        tokens.append(
            Token(
                TokenType.EOF,
                "",
                self.position,
            )
        )

        return tokens

    def _read_identifier_or_keyword(self) -> Token:
        start = self.position

        while self.position < len(self.sql):
            char = self.sql[self.position]

            if not (
                char.isalnum()
                or char == "_"
            ):
                break

            self.position += 1

        value = self.sql[start:self.position]

        token_type = self.KEYWORDS.get(
            value.upper(),
            TokenType.IDENTIFIER,
        )

        return Token(
            token_type,
            value,
            start,
        )

    def _read_number(self) -> Token:
        start = self.position
        has_decimal = False

        while self.position < len(self.sql):
            char = self.sql[self.position]

            if char.isdigit():
                self.position += 1
                continue

            if char == ".":
                if has_decimal:
                    raise SyntaxError(
                        f"Invalid number at position {start}."
                    )

                has_decimal = True
                self.position += 1

                if (
                    self.position >= len(self.sql)
                    or not self.sql[self.position].isdigit()
                ):
                    raise SyntaxError(
                        f"Invalid number at position {start}."
                    )

                continue

            break

        value = self.sql[start:self.position]

        return Token(
            TokenType.FLOAT if has_decimal else TokenType.INTEGER,
            value,
            start,
        )

    def _read_string(self, quote: str) -> Token:
        start = self.position
        self.position += 1

        characters = []

        escape_sequences = {
            "n": "\n",
            "t": "\t",
            "r": "\r",
            "\\": "\\",
            "'": "'",
            '"': '"',
        }

        while self.position < len(self.sql):
            char = self.sql[self.position]

            if char == quote:
                self.position += 1

                return Token(
                    TokenType.STRING,
                    "".join(characters),
                    start,
                )

            if char == "\\":
                self.position += 1

                if self.position >= len(self.sql):
                    raise SyntaxError(
                        f"Unterminated string starting "
                        f"at position {start}."
                    )

                escaped = self.sql[self.position]

                if escaped not in escape_sequences:
                    raise SyntaxError(
                        f"Unsupported escape sequence "
                        f"\\{escaped} at position "
                        f"{self.position - 1}."
                    )

                characters.append(
                    escape_sequences[escaped]
                )

                self.position += 1
                continue

            characters.append(char)
            self.position += 1

        raise SyntaxError(
            f"Unterminated string starting "
            f"at position {start}."
        )

    def _read_operator_or_symbol(self):
        start = self.position

        if self.sql.startswith(
            "!=",
            self.position
        ):
            self.position += 2

            return Token(
                TokenType.NOT_EQUAL,
                "!=",
                start,
            )

        if self.sql.startswith(
            "<=",
            self.position
        ):
            self.position += 2

            return Token(
                TokenType.LESS_EQUAL,
                "<=",
                start,
            )

        if self.sql.startswith(
            ">=",
            self.position
        ):
            self.position += 2

            return Token(
                TokenType.GREATER_EQUAL,
                ">=",
                start,
            )

        char = self.sql[self.position]

        token_type = self.SINGLE_CHAR_TOKENS.get(
            char
        )

        if token_type is None:
            return None

        self.position += 1

        return Token(
            token_type,
            char,
            start,
        )