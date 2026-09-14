from typing import Any

from ..core.schema import Schema
from .record import RecordSerializer


class RecordCodec:
    """
    Converts schema-aware table rows to and from
    binary records.
    """

    def __init__(self, schema: Schema):
        self.schema = schema

    def encode(self, row: dict[str, Any]) -> bytes:
        """
        Convert a validated row into a binary record.
        """

        self.schema.validate_row(row)

        values = [
            row.get(column.name)
            for column in self.schema.columns
        ]

        return RecordSerializer.serialize(values)

    def decode(self, data: bytes) -> dict[str, Any]:
        """
        Convert a binary record back into a row.
        """

        values = RecordSerializer.deserialize(data)

        if len(values) != len(self.schema.columns):
            raise ValueError(
                "Record field count does not match schema."
            )

        return {
            column.name: value
            for column, value
            in zip(self.schema.columns, values)
        }