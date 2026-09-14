from dataclasses import dataclass
from enum import Enum, auto


class TokenType(Enum):
    SELECT = auto()
    FROM = auto()
    WHERE = auto()
    INSERT = auto()
    INTO = auto()
    VALUES = auto()
    CREATE = auto()
    TABLE = auto()
    INDEX = auto()
    ON = auto()
    UPDATE = auto()
    SET = auto()
    DELETE = auto()
    AND = auto()
    OR = auto()
    ORDER = auto()
    BY = auto()
    LIMIT = auto()
    PRIMARY = auto()
    KEY = auto()
    UNIQUE = auto()
    NOT = auto()
    NULL = auto()

    IDENTIFIER = auto()
    INTEGER = auto()
    FLOAT = auto()
    STRING = auto()

    EQUAL = auto()
    NOT_EQUAL = auto()
    LESS_THAN = auto()
    LESS_EQUAL = auto()
    GREATER_THAN = auto()
    GREATER_EQUAL = auto()

    PLUS = auto()
    MINUS = auto()
    MULTIPLY = auto()
    DIVIDE = auto()

    COMMA = auto()
    LEFT_PAREN = auto()
    RIGHT_PAREN = auto()
    SEMICOLON = auto()

    EOF = auto()


@dataclass(frozen=True)
class Token:
    type: TokenType
    value: str
    position: int