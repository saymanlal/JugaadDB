import struct
from pathlib import Path

from .btree import BPlusTreeIndex
from .index_file import IndexFile
from .metadata import IndexMetadata
from .serializer import IndexSerializer
from .tree_serializer import BTreeSerializer


MAGIC = b"JBP1"
VERSION = 1

HEADER_FORMAT = ">4sBII"
HEADER_SIZE = struct.calcsize(HEADER_FORMAT)


class BTreePersistence:
    @staticmethod
    def save(
        index: BPlusTreeIndex,
        path: str | Path,
        metadata: IndexMetadata,
    ) -> None:
        if not isinstance(index, BPlusTreeIndex):
            raise TypeError("Expected BPlusTreeIndex.")

        if not isinstance(metadata, IndexMetadata):
            raise TypeError("Expected IndexMetadata.")

        if metadata.index_type != "btree":
            raise ValueError(
                "BTreePersistence only supports btree indexes."
            )

        if metadata.order != index.order:
            raise ValueError(
                "Index metadata order does not match B+Tree order."
            )

        if metadata.index_name != index.name:
            raise ValueError(
                "Index metadata name does not match B+Tree name."
            )

        if metadata.column != index.column:
            raise ValueError(
                "Index metadata column does not match B+Tree column."
            )

        metadata_data = IndexSerializer.serialize(metadata)
        tree_data = BTreeSerializer.serialize(index)

        payload = bytearray()

        payload.extend(
            struct.pack(
                HEADER_FORMAT,
                MAGIC,
                VERSION,
                len(metadata_data),
                len(tree_data),
            )
        )

        payload.extend(metadata_data)
        payload.extend(tree_data)

        index_file = IndexFile(path)

        if index_file.exists():
            index_file.write(bytes(payload))
        else:
            index_file.create(bytes(payload))

    @staticmethod
    def load(
        path: str | Path,
    ) -> tuple[BPlusTreeIndex, IndexMetadata]:
        index_file = IndexFile(path)

        data = index_file.read()

        if len(data) < HEADER_SIZE:
            raise ValueError(
                "Persistent B+Tree payload is too short."
            )

        magic, version, metadata_length, tree_length = (
            struct.unpack_from(
                HEADER_FORMAT,
                data,
                0,
            )
        )

        if magic != MAGIC:
            raise ValueError(
                "Invalid persistent B+Tree magic."
            )

        if version != VERSION:
            raise ValueError(
                f"Unsupported persistent B+Tree version: {version}"
            )

        expected_length = (
            HEADER_SIZE
            + metadata_length
            + tree_length
        )

        if len(data) != expected_length:
            raise ValueError(
                "Invalid persistent B+Tree payload length."
            )

        offset = HEADER_SIZE

        metadata_end = offset + metadata_length

        metadata_data = data[
            offset:metadata_end
        ]

        offset = metadata_end

        tree_end = offset + tree_length

        tree_data = data[
            offset:tree_end
        ]

        metadata = IndexSerializer.deserialize(
            metadata_data
        )

        if metadata.index_type != "btree":
            raise ValueError(
                "Persistent file does not contain a B+Tree index."
            )

        index = BTreeSerializer.deserialize(
            tree_data
        )

        index.name = metadata.index_name
        index.column = metadata.column
        index.unique = metadata.unique
        index.table_name = metadata.table_name
        index.index_type = metadata.index_type

        if index.order != metadata.order:
            raise ValueError(
                "Persisted B+Tree order does not match metadata."
            )

        index.validate()

        return index, metadata