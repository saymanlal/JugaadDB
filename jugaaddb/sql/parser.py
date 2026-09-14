from .ast import (
    Assignment,
    BinaryExpression,
    ColumnDefinition,
    CreateIndexStatement,
    CreateTableStatement,
    DeleteStatement,
    Identifier,
    InsertStatement,
    Literal,
    LogicalExpression,
    SelectStatement,
    UpdateStatement,
)
from .tokens import Token, TokenType


class Parser:
    COMPARISON_OPERATORS = {
        TokenType.EQUAL: "=",
        TokenType.NOT_EQUAL: "!=",
        TokenType.LESS_THAN: "<",
        TokenType.LESS_EQUAL: "<=",
        TokenType.GREATER_THAN: ">",
        TokenType.GREATER_EQUAL: ">=",
    }

    def __init__(self, tokens: list[Token]):
        if not isinstance(tokens, list):
            raise TypeError(
                "Tokens must be provided as a list."
            )

        self.tokens = tokens
        self.position = 0

    def parse(self):
        if self.current.type == TokenType.SELECT:
            statement = self._parse_select()

        elif self.current.type == TokenType.INSERT:
            statement = self._parse_insert()

        elif self.current.type == TokenType.UPDATE:
            statement = self._parse_update()

        elif self.current.type == TokenType.DELETE:
            statement = self._parse_delete()

        elif self.current.type == TokenType.CREATE:
            statement = self._parse_create()

        else:
            raise SyntaxError(
                f"Unsupported statement: "
                f"{self.current.value or self.current.type.name}"
            )

        if self.current.type == TokenType.SEMICOLON:
            self.advance()

        self.expect(TokenType.EOF)

        return statement

    @property
    def current(self) -> Token:
        return self.tokens[self.position]

    def advance(self) -> Token:
        token = self.current

        if self.position < len(self.tokens) - 1:
            self.position += 1

        return token

    def expect(self, token_type: TokenType) -> Token:
        if self.current.type != token_type:
            raise SyntaxError(
                f"Expected {token_type.name}, got "
                f"{self.current.type.name} "
                f"at position {self.current.position}."
            )

        return self.advance()

    def _parse_create(self):
        self.expect(TokenType.CREATE)

        if self.current.type == TokenType.TABLE:
            return self._parse_create_table()

        if self.current.type == TokenType.INDEX:
            return self._parse_create_index()

        raise SyntaxError(
            f"Expected TABLE or INDEX, got "
            f"{self.current.type.name} "
            f"at position {self.current.position}."
        )

    def _parse_select(self) -> SelectStatement:
        self.expect(TokenType.SELECT)

        columns = self._parse_column_list()

        self.expect(TokenType.FROM)

        table = self._parse_identifier()

        where = None

        if self.current.type == TokenType.WHERE:
            self.advance()
            where = self._parse_expression()

        return SelectStatement(
            columns=tuple(columns),
            table=table,
            where=where,
        )

    def _parse_column_list(self) -> list[Identifier]:
        columns = []

        if self.current.type == TokenType.MULTIPLY:
            self.advance()
            return [Identifier("*")]

        columns.append(
            self._parse_identifier()
        )

        while self.current.type == TokenType.COMMA:
            self.advance()

            columns.append(
                self._parse_identifier()
            )

        return columns

    def _parse_expression(self):
        expression = self._parse_comparison()

        while self.current.type == TokenType.OR:
            self.advance()

            right = self._parse_comparison()

            expression = LogicalExpression(
                left=expression,
                operator="OR",
                right=right,
            )

        return expression

    def _parse_comparison(self):
        expression = self._parse_comparison_part()

        while self.current.type == TokenType.AND:
            self.advance()

            right = self._parse_comparison_part()

            expression = LogicalExpression(
                left=expression,
                operator="AND",
                right=right,
            )

        return expression

    def _parse_comparison_part(self) -> BinaryExpression:
        left = self._parse_identifier()

        operator_token = self.current

        if operator_token.type not in self.COMPARISON_OPERATORS:
            raise SyntaxError(
                f"Expected comparison operator, got "
                f"{operator_token.type.name} "
                f"at position {operator_token.position}."
            )

        operator = self.COMPARISON_OPERATORS[
            operator_token.type
        ]

        self.advance()

        right = self._parse_literal()

        return BinaryExpression(
            left=left,
            operator=operator,
            right=right,
        )

    def _parse_insert(self) -> InsertStatement:
        self.expect(TokenType.INSERT)
        self.expect(TokenType.INTO)

        table = self._parse_identifier()

        self.expect(TokenType.LEFT_PAREN)

        columns = self._parse_identifier_list()

        self.expect(TokenType.RIGHT_PAREN)

        self.expect(TokenType.VALUES)

        self.expect(TokenType.LEFT_PAREN)

        values = self._parse_literal_list()

        self.expect(TokenType.RIGHT_PAREN)

        if len(columns) != len(values):
            raise SyntaxError(
                "Number of columns must match "
                "number of values."
            )

        return InsertStatement(
            table=table,
            columns=tuple(columns),
            values=tuple(values),
        )

    def _parse_update(self) -> UpdateStatement:
        self.expect(TokenType.UPDATE)

        table = self._parse_identifier()

        self.expect(TokenType.SET)

        assignments = []

        while True:
            column = self._parse_identifier()

            self.expect(TokenType.EQUAL)

            value = self._parse_literal()

            assignments.append(
                Assignment(
                    column=column,
                    value=value,
                )
            )

            if self.current.type != TokenType.COMMA:
                break

            self.advance()

        where = None

        if self.current.type == TokenType.WHERE:
            self.advance()
            where = self._parse_expression()

        return UpdateStatement(
            table=table,
            assignments=tuple(assignments),
            where=where,
        )

    def _parse_delete(self) -> DeleteStatement:
        self.expect(TokenType.DELETE)
        self.expect(TokenType.FROM)

        table = self._parse_identifier()

        where = None

        if self.current.type == TokenType.WHERE:
            self.advance()
            where = self._parse_expression()

        return DeleteStatement(
            table=table,
            where=where,
        )

    def _parse_create_table(self) -> CreateTableStatement:
        self.expect(TokenType.TABLE)

        table = self._parse_identifier()

        self.expect(TokenType.LEFT_PAREN)

        columns = []

        while True:
            name = self._parse_identifier()

            data_type = self._parse_identifier()

            primary_key = False
            unique = False
            nullable = True

            if self.current.type == TokenType.PRIMARY:
                self.advance()

                self.expect(TokenType.KEY)

                primary_key = True
                nullable = False

            if self.current.type == TokenType.UNIQUE:
                self.advance()

                unique = True

            if self.current.type == TokenType.NOT:
                self.advance()

                self.expect(TokenType.NULL)

                nullable = False

            elif self.current.type == TokenType.NULL:
                self.advance()

                nullable = True

            columns.append(
                ColumnDefinition(
                    name=name,
                    data_type=data_type,
                    primary_key=primary_key,
                    unique=unique,
                    nullable=nullable,
                )
            )

            if self.current.type != TokenType.COMMA:
                break

            self.advance()

        self.expect(TokenType.RIGHT_PAREN)

        return CreateTableStatement(
            table=table,
            columns=tuple(columns),
        )

    def _parse_create_index(self) -> CreateIndexStatement:
        self.expect(TokenType.INDEX)

        index = self._parse_identifier()

        self.expect(TokenType.ON)

        table = self._parse_identifier()

        self.expect(TokenType.LEFT_PAREN)

        column = self._parse_identifier()

        self.expect(TokenType.RIGHT_PAREN)

        return CreateIndexStatement(
            index=index,
            table=table,
            column=column,
        )

    def _parse_identifier_list(self) -> list[Identifier]:
        identifiers = [
            self._parse_identifier()
        ]

        while self.current.type == TokenType.COMMA:
            self.advance()

            identifiers.append(
                self._parse_identifier()
            )

        return identifiers

    def _parse_literal_list(self) -> list[Literal]:
        values = [
            self._parse_literal()
        ]

        while self.current.type == TokenType.COMMA:
            self.advance()

            values.append(
                self._parse_literal()
            )

        return values

    def _parse_identifier(self) -> Identifier:
        token = self.expect(
            TokenType.IDENTIFIER
        )

        return Identifier(token.value)

    def _parse_literal(self) -> Literal:
        token = self.current

        if token.type == TokenType.INTEGER:
            self.advance()

            return Literal(
                int(token.value)
            )

        if token.type == TokenType.FLOAT:
            self.advance()

            return Literal(
                float(token.value)
            )

        if token.type == TokenType.STRING:
            self.advance()

            return Literal(
                token.value
            )

        if token.type == TokenType.NULL:
            self.advance()

            return Literal(None)

        raise SyntaxError(
            f"Expected literal, got "
            f"{token.type.name} "
            f"at position {token.position}."
        )