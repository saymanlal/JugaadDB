from typing import Any

from .schema import Column, Schema


class Catalog:
    def __init__(
        self,
        data: dict[str, Any],
    ):
        if not isinstance(data, dict):
            raise TypeError(
                "Catalog data must be a dictionary."
            )

        tables = data.get("tables")

        if tables is None:
            data["tables"] = {}
        elif not isinstance(tables, dict):
            raise ValueError(
                "Catalog tables must be a dictionary."
            )

        self.data = data

    @property
    def tables(self) -> dict[str, Any]:
        return self.data["tables"]

    def exists(
        self,
        name: str,
    ) -> bool:
        return name in self.tables

    def get(
        self,
        name: str,
    ) -> dict[str, Any]:
        if name not in self.tables:
            raise ValueError(
                f"Table does not exist: {name}"
            )

        return self.tables[name]

    def create_table(
        self,
        name: str,
        schema: Schema,
        physical_path: str,
    ) -> dict[str, Any]:
        if not isinstance(name, str) or not name.strip():
            raise ValueError(
                "Table name must be a non-empty string."
            )

        if not isinstance(schema, Schema):
            raise TypeError(
                "Catalog requires a Schema."
            )

        if not isinstance(
            physical_path,
            str,
        ) or not physical_path.strip():
            raise ValueError(
                "Physical table path must be a non-empty string."
            )

        if self.exists(name):
            raise ValueError(
                f"Table already exists: {name}"
            )

        table_data = {
            "schema": [
                {
                    "name": column.name,
                    "data_type": column.data_type,
                    "primary_key": column.primary_key,
                    "nullable": column.nullable,
                    "unique": column.unique,
                }
                for column in schema.columns
            ],
            "rows": [],
            "record_ids": [],
            "physical": {
                "path": physical_path,
                "format": "slotted-page",
            },
        }

        self.tables[name] = table_data

        return table_data

    def schema(
        self,
        name: str,
    ) -> Schema:
        table_data = self.get(name)

        columns = table_data.get("schema")

        if not isinstance(columns, list):
            raise ValueError(
                f"Invalid schema metadata for table: {name}"
            )

        return Schema(
            [
                Column(
                    name=column["name"],
                    data_type=column["data_type"],
                    primary_key=column.get(
                        "primary_key",
                        False,
                    ),
                    nullable=column.get(
                        "nullable",
                        True,
                    ),
                    unique=column.get(
                        "unique",
                        False,
                    ),
                )
                for column in columns
            ]
        )

    def ensure_physical_metadata(
        self,
        name: str,
        physical_path: str,
    ) -> bool:
        table_data = self.get(name)

        physical = table_data.get("physical")

        if physical is None:
            table_data["physical"] = {
                "path": physical_path,
                "format": "slotted-page",
            }
            return True

        if not isinstance(physical, dict):
            raise ValueError(
                f"Invalid physical metadata for table: {name}"
            )

        stored_path = physical.get("path")

        if not isinstance(
            stored_path,
            str,
        ) or not stored_path.strip():
            physical["path"] = physical_path

        if physical.get("format") is None:
            physical["format"] = "slotted-page"

        return True