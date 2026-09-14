import struct

from .metadata import IndexMetadata


MAGIC = b"JIDX"
VERSION = 1
HEADER_FORMAT = ">4sBI"
HEADER_SIZE = struct.calcsize(HEADER_FORMAT)


class IndexSerializer:
    @staticmethod
    def serialize(metadata: IndexMetadata) -> bytes:
        if not isinstance(metadata, IndexMetadata):
            raise TypeError("Expected IndexMetadata.")

        table_name = metadata.table_name.encode("utf-8")
        index_name = metadata.index_name.encode("utf-8")
        column = metadata.column.encode("utf-8")
        index_type = metadata.index_type.encode("utf-8")

        fields = [
            table_name,
            index_name,
            column,
            index_type,
        ]

        payload = bytearray()

        for field in fields:
            if len(field) > 65535:
                raise ValueError("Index metadata field is too large.")

            payload.extend(struct.pack(">H", len(field)))
            payload.extend(field)

        payload.extend(struct.pack(">I", metadata.order))
        payload.extend(struct.pack(">?", metadata.unique))

        header = struct.pack(
            HEADER_FORMAT,
            MAGIC,
            VERSION,
            len(payload),
        )

        return header + bytes(payload)

    @staticmethod
    def deserialize(data: bytes) -> IndexMetadata:
        if not isinstance(data, bytes):
            raise TypeError("Serialized index metadata must be bytes.")

        if len(data) < HEADER_SIZE:
            raise ValueError("Serialized index metadata is too short.")

        magic, version, payload_length = struct.unpack_from(
            HEADER_FORMAT,
            data,
            0,
        )

        if magic != MAGIC:
            raise ValueError("Invalid index metadata magic.")

        if version != VERSION:
            raise ValueError(
                f"Unsupported index metadata version: {version}"
            )

        expected_length = HEADER_SIZE + payload_length

        if len(data) != expected_length:
            raise ValueError("Invalid index metadata payload length.")

        offset = HEADER_SIZE
        fields = []

        for _ in range(4):
            if offset + 2 > len(data):
                raise ValueError("Corrupted index metadata.")

            field_length = struct.unpack_from(
                ">H",
                data,
                offset,
            )[0]

            offset += 2

            if offset + field_length > len(data):
                raise ValueError("Corrupted index metadata field.")

            field = data[offset:offset + field_length]

            try:
                decoded = field.decode("utf-8")
            except UnicodeDecodeError as exc:
                raise ValueError(
                    "Index metadata contains invalid UTF-8."
                ) from exc

            fields.append(decoded)
            offset += field_length

        if offset + 5 != len(data):
            raise ValueError("Corrupted index metadata payload.")

        order = struct.unpack_from(
            ">I",
            data,
            offset,
        )[0]

        offset += 4

        unique = struct.unpack_from(
            ">?",
            data,
            offset,
        )[0]

        return IndexMetadata(
            table_name=fields[0],
            index_name=fields[1],
            column=fields[2],
            index_type=fields[3],
            order=order,
            unique=unique,
        )