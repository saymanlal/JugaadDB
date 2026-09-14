from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Identifier:
    name: str


@dataclass(frozen=True)
class Literal:
    value: Any


@dataclass(frozen=True)
class BinaryExpression:
    left: Any
    operator: str
    right: Any


@dataclass(frozen=True)
class SelectStatement:
    columns: tuple[Identifier, ...]
    table: Identifier
    where: BinaryExpression | None = None


@dataclass(frozen=True)
class InsertStatement:
    table: Identifier
    columns: tuple[Identifier, ...]
    values: tuple[Literal, ...]


@dataclass(frozen=True)
class CreateTableStatement:
    table: Identifier
    columns: tuple[Any, ...]


@dataclass(frozen=True)
class ColumnDefinition:
    name: Identifier
    data_type: Identifier
    primary_key: bool = False
    unique: bool = False