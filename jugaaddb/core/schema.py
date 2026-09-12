from dataclasses import dataclass
from typing import Any


SUPPORTED_TYPES = {
    "INTEGER": int,
    "FLOAT": (int, float),
    "TEXT": str,
    "BOOLEAN": bool,
}


@dataclass(frozen=True)
class Column:
    name: str
    data_type: str
    primary_key: bool = False
    nullable: bool = True
    unique: bool = False

    def __post_init__(self):
        data_type = self.data_type.upper()

        if data_type not in SUPPORTED_TYPES:
            raise ValueError(
                f"Unsupported data type: {self.data_type}"
            )

        object.__setattr__(self, "data_type", data_type)


class Schema:
    def __init__(self, columns: list[Column]):
        if not columns:
            raise ValueError("A table must contain at least one column.")

        names = [column.name for column in columns]

        if len(names) != len(set(names)):
            raise ValueError("Duplicate column names are not allowed.")

        primary_keys = [
            column for column in columns
            if column.primary_key
        ]

        if len(primary_keys) > 1:
            raise ValueError(
                "Version 0.1 supports one primary key."
            )

        self.columns = tuple(columns)

    def validate_row(self, row: dict[str, Any]) -> None:
        expected = {column.name for column in self.columns}
        received = set(row.keys())

        unknown = received - expected

        if unknown:
            raise ValueError(
                f"Unknown columns: {sorted(unknown)}"
            )

        for column in self.columns:
            value = row.get(column.name)

            if value is None:
                if not column.nullable:
                    raise ValueError(
                        f"Column '{column.name}' cannot be NULL."
                    )
                continue

            expected_type = SUPPORTED_TYPES[column.data_type]

            if (
                column.data_type == "BOOLEAN"
                and type(value) is not bool
            ):
                raise TypeError(
                    f"Column '{column.name}' expects BOOLEAN."
                )

            elif (
                column.data_type != "BOOLEAN"
                and not isinstance(value, expected_type)
            ):
                raise TypeError(
                    f"Column '{column.name}' expects "
                    f"{column.data_type}, got {type(value).__name__}."
                )