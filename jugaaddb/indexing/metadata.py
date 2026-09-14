from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class IndexMetadata:
    table_name: str
    index_name: str
    column: str
    index_type: str = "btree"
    order: int = 4
    unique: bool = False

    def __post_init__(self):
        if not isinstance(self.table_name, str) or not self.table_name.strip():
            raise ValueError("Table name must be a non-empty string.")

        if not isinstance(self.index_name, str) or not self.index_name.strip():
            raise ValueError("Index name must be a non-empty string.")

        if not isinstance(self.column, str) or not self.column.strip():
            raise ValueError("Index column must be a non-empty string.")

        if not isinstance(self.index_type, str) or not self.index_type.strip():
            raise ValueError("Index type must be a non-empty string.")

        normalized_type = self.index_type.lower()

        if normalized_type not in {"btree", "hash"}:
            raise ValueError(f"Unsupported index type: {self.index_type}")

        object.__setattr__(self, "index_type", normalized_type)

        if type(self.order) is not int:
            raise TypeError("Index order must be an integer.")

        if self.order < 3:
            raise ValueError("Index order must be at least 3.")

        if type(self.unique) is not bool:
            raise TypeError("Index unique flag must be a boolean.")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "IndexMetadata":
        if not isinstance(data, dict):
            raise TypeError("Index metadata must be a dictionary.")

        required_fields = {
            "table_name",
            "index_name",
            "column",
        }

        missing = required_fields - set(data.keys())

        if missing:
            raise ValueError(
                f"Missing index metadata fields: {sorted(missing)}"
            )

        return cls(
            table_name=data["table_name"],
            index_name=data["index_name"],
            column=data["column"],
            index_type=data.get("index_type", "btree"),
            order=data.get("order", 4),
            unique=data.get("unique", False),
        )