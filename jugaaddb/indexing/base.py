from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

RecordID = tuple[int, int]


@dataclass(frozen=True)
class IndexEntry:
    key: Any
    record_id: RecordID


class Index(ABC):
    def __init__(self, name: str, column: str):
        if not isinstance(name, str) or not name.strip():
            raise ValueError("Index name must be a non-empty string.")
        if not isinstance(column, str) or not column.strip():
            raise ValueError("Index column must be a non-empty string.")
        self.name = name
        self.column = column

    @abstractmethod
    def insert(self, key: Any, record_id: RecordID) -> None:
        raise NotImplementedError

    @abstractmethod
    def delete(self, key: Any, record_id: RecordID) -> None:
        raise NotImplementedError

    @abstractmethod
    def search(self, key: Any) -> list[RecordID]:
        raise NotImplementedError

    @abstractmethod
    def scan(self) -> list[IndexEntry]:
        raise NotImplementedError