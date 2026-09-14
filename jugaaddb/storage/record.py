import struct
from typing import Any


class RecordSerializer:
    """
    Serializes typed Python values into a compact binary record.

    Field format:

        1 byte  -> type
        4 bytes -> payload length
        N bytes -> payload

    Supported types:

        INTEGER
        FLOAT
        TEXT
        BOOLEAN
        NULL
    """

    TYPE_NULL = 0
    TYPE_INTEGER = 1
    TYPE_FLOAT = 2
    TYPE_TEXT = 3
    TYPE_BOOLEAN = 4

    HEADER_FORMAT = ">H"
    HEADER_SIZE = struct.calcsize(HEADER_FORMAT)

    FIELD_HEADER_FORMAT = ">BI"
    FIELD_HEADER_SIZE = struct.calcsize(
        FIELD_HEADER_FORMAT
    )

    @classmethod
    def serialize(
        cls,
        values: list[Any]
    ) -> bytes:

        output = bytearray()

        output.extend(
            struct.pack(
                cls.HEADER_FORMAT,
                len(values)
            )
        )

        for value in values:
            type_code, payload = cls._encode_value(value)

            output.extend(
                struct.pack(
                    cls.FIELD_HEADER_FORMAT,
                    type_code,
                    len(payload)
                )
            )

            output.extend(payload)

        return bytes(output)

    @classmethod
    def deserialize(
        cls,
        data: bytes
    ) -> list[Any]:

        if len(data) < cls.HEADER_SIZE:
            raise ValueError(
                "Record is too small."
            )

        field_count = struct.unpack_from(
            cls.HEADER_FORMAT,
            data,
            0
        )[0]

        offset = cls.HEADER_SIZE
        values = []

        for _ in range(field_count):

            if (
                offset + cls.FIELD_HEADER_SIZE
                > len(data)
            ):
                raise ValueError(
                    "Corrupted record field header."
                )

            type_code, length = struct.unpack_from(
                cls.FIELD_HEADER_FORMAT,
                data,
                offset
            )

            offset += cls.FIELD_HEADER_SIZE

            end = offset + length

            if end > len(data):
                raise ValueError(
                    "Corrupted record field payload."
                )

            payload = data[offset:end]

            values.append(
                cls._decode_value(
                    type_code,
                    payload
                )
            )

            offset = end

        if offset != len(data):
            raise ValueError(
                "Record contains unexpected trailing data."
            )

        return values

    @classmethod
    def _encode_value(
        cls,
        value: Any
    ) -> tuple[int, bytes]:

        if value is None:
            return cls.TYPE_NULL, b""

        if type(value) is bool:
            return (
                cls.TYPE_BOOLEAN,
                b"\x01" if value else b"\x00"
            )

        if type(value) is int:
            return (
                cls.TYPE_INTEGER,
                struct.pack(">q", value)
            )

        if type(value) is float:
            return (
                cls.TYPE_FLOAT,
                struct.pack(">d", value)
            )

        if type(value) is str:
            return (
                cls.TYPE_TEXT,
                value.encode("utf-8")
            )

        raise TypeError(
            f"Unsupported value type: "
            f"{type(value).__name__}"
        )

    @classmethod
    def _decode_value(
        cls,
        type_code: int,
        payload: bytes
    ) -> Any:

        if type_code == cls.TYPE_NULL:

            if payload:
                raise ValueError(
                    "NULL field cannot contain payload."
                )

            return None

        if type_code == cls.TYPE_BOOLEAN:

            if len(payload) != 1:
                raise ValueError(
                    "Invalid BOOLEAN payload."
                )

            if payload not in (b"\x00", b"\x01"):
                raise ValueError(
                    "Invalid BOOLEAN value."
                )

            return payload == b"\x01"

        if type_code == cls.TYPE_INTEGER:

            if len(payload) != 8:
                raise ValueError(
                    "Invalid INTEGER payload."
                )

            return struct.unpack(
                ">q",
                payload
            )[0]

        if type_code == cls.TYPE_FLOAT:

            if len(payload) != 8:
                raise ValueError(
                    "Invalid FLOAT payload."
                )

            return struct.unpack(
                ">d",
                payload
            )[0]

        if type_code == cls.TYPE_TEXT:

            try:
                return payload.decode("utf-8")
            except UnicodeDecodeError as exc:
                raise ValueError(
                    "Invalid TEXT payload."
                ) from exc

        raise ValueError(
            f"Unknown record type code: {type_code}"
        )