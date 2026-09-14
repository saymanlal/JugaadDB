from dataclasses import dataclass
from typing import Any, Iterator


@dataclass(frozen=True)
class QueryResult:
    columns: tuple[str, ...]
    rows: tuple[dict[str, Any], ...]
    query_type: str = "SELECT"

    @property
    def row_count(self) -> int:
        return len(self.rows)

    def __iter__(self) -> Iterator[dict[str, Any]]:
        return iter(self.rows)

    def __len__(self) -> int:
        return len(self.rows)

    def __getitem__(self, index):
        return self.rows[index]

    def __eq__(self, other):
        if isinstance(other, QueryResult):
            return (
                self.columns == other.columns
                and self.rows == other.rows
                and self.query_type == other.query_type
            )

        if isinstance(other, list):
            return list(self.rows) == other

        return NotImplemented

    def to_list(self) -> list[dict[str, Any]]:
        return [row.copy() for row in self.rows]


@dataclass(frozen=True)
class CommandResult:
    affected_rows: int
    query_type: str

    def __int__(self) -> int:
        return self.affected_rows

    def __index__(self) -> int:
        return self.affected_rows

    def __eq__(self, other):
        if isinstance(other, CommandResult):
            return (
                self.affected_rows == other.affected_rows
                and self.query_type == other.query_type
            )

        if isinstance(other, int):
            return self.affected_rows == other

        return NotImplemented

    def __bool__(self) -> bool:
        return self.affected_rows != 0