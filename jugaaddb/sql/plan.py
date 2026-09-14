from dataclasses import dataclass
from typing import Any

from .ast import Identifier


@dataclass(frozen=True)
class TableScan:
    table: Identifier


@dataclass(frozen=True)
class Filter:
    source: Any
    condition: Any


@dataclass(frozen=True)
class Projection:
    source: Any
    columns: tuple[Identifier, ...]


@dataclass(frozen=True)
class InsertPlan:
    table: Identifier
    columns: tuple[Identifier, ...]
    values: tuple[Any, ...]


@dataclass(frozen=True)
class UpdatePlan:
    source: Any
    assignments: tuple[Any, ...]


@dataclass(frozen=True)
class DeletePlan:
    source: Any


@dataclass(frozen=True)
class CreateTablePlan:
    table: Identifier
    columns: tuple[Any, ...]