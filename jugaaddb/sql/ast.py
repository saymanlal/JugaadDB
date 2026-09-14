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
class LogicalExpression:
    left: Any
    operator: str
    right: Any


@dataclass(frozen=True)
class Assignment:
    column: Identifier
    value: Literal


@dataclass(frozen=True)
class SelectStatement:
    columns: tuple[Identifier, ...]
    table: Identifier
    where: Any = None


@dataclass(frozen=True)
class InsertStatement:
    table: Identifier
    columns: tuple[Identifier, ...]
    values: tuple[Literal, ...]


@dataclass(frozen=True)
class UpdateStatement:
    table: Identifier
    assignments: tuple[Assignment, ...]
    where: Any = None


@dataclass(frozen=True)
class DeleteStatement:
    table: Identifier
    where: Any = None


@dataclass(frozen=True)
class CreateTableStatement:
    table: Identifier
    columns: tuple[Any, ...]


@dataclass(frozen=True)
class CreateIndexStatement:
    index: Identifier
    table: Identifier
    column: Identifier


@dataclass(frozen=True)
class ColumnDefinition:
    name: Identifier
    data_type: Identifier
    primary_key: bool = False
    unique: bool = False
    nullable: bool = True