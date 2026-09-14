import struct
from typing import Any

from .base import RecordID
from .btree import BTreeNode, BPlusTreeIndex


MAGIC = b"JBT1"
VERSION = 1

HEADER_FORMAT = ">4sBI"
HEADER_SIZE = struct.calcsize(HEADER_FORMAT)

NODE_HEADER_FORMAT = ">BII"
NODE_HEADER_SIZE = struct.calcsize(NODE_HEADER_FORMAT)

LEAF_NODE = 1
INTERNAL_NODE = 2

KEY_NONE = 0
KEY_BOOL = 1
KEY_INT = 2
KEY_FLOAT = 3
KEY_TEXT = 4


class BTreeSerializer:
    @staticmethod
    def serialize(index: BPlusTreeIndex) -> bytes:
        if not isinstance(index, BPlusTreeIndex):
            raise TypeError("Expected BPlusTreeIndex.")

        nodes = []
        node_ids = {}
        visiting = set()

        def collect(node: BTreeNode) -> int:
            identity = id(node)

            if identity in node_ids:
                return node_ids[identity]

            if identity in visiting:
                raise ValueError("Cycle detected in B+Tree.")

            visiting.add(identity)

            node_id = len(nodes)
            node_ids[identity] = node_id

            nodes.append(None)

            if node.leaf:
                next_id = None

                if node.next_leaf is not None:
                    next_id = collect(node.next_leaf)

                encoded_keys = [
                    BTreeSerializer._encode_key(key)
                    for key in node.keys
                ]

                values = [
                    [
                        BTreeSerializer._encode_record_id(record_id)
                        for record_id in record_ids
                    ]
                    for record_ids in node.values
                ]

                nodes[node_id] = {
                    "type": LEAF_NODE,
                    "keys": encoded_keys,
                    "values": values,
                    "next": next_id,
                }

            else:
                children = [
                    collect(child)
                    for child in node.children
                ]

                encoded_keys = [
                    BTreeSerializer._encode_key(key)
                    for key in node.keys
                ]

                nodes[node_id] = {
                    "type": INTERNAL_NODE,
                    "keys": encoded_keys,
                    "children": children,
                }

            visiting.remove(identity)

            return node_id

        root_id = collect(index.root)

        payload = bytearray()

        payload.extend(
            struct.pack(
                ">I",
                index.order,
            )
        )

        payload.extend(
            struct.pack(
                ">I",
                root_id,
            )
        )

        payload.extend(
            struct.pack(
                ">I",
                len(nodes),
            )
        )

        for node in nodes:
            node_type = node["type"]
            keys = node["keys"]

            next_id = node.get("next")

            if next_id is None:
                next_id = 0xFFFFFFFF

            payload.extend(
                struct.pack(
                    NODE_HEADER_FORMAT,
                    node_type,
                    len(keys),
                    next_id,
                )
            )

            for key in keys:
                payload.extend(key)

            if node_type == LEAF_NODE:
                values = node["values"]

                if len(values) != len(keys):
                    raise ValueError(
                        "Leaf keys and values must have equal length."
                    )

                for record_ids in values:
                    payload.extend(
                        struct.pack(
                            ">I",
                            len(record_ids),
                        )
                    )

                    for record_id in record_ids:
                        payload.extend(record_id)

            elif node_type == INTERNAL_NODE:
                children = node["children"]

                if len(children) != len(keys) + 1:
                    raise ValueError(
                        "Internal node must contain len(keys) + 1 children."
                    )

                for child_id in children:
                    payload.extend(
                        struct.pack(
                            ">I",
                            child_id,
                        )
                    )

            else:
                raise ValueError(
                    "Unsupported B+Tree node type."
                )

        header = struct.pack(
            HEADER_FORMAT,
            MAGIC,
            VERSION,
            len(payload),
        )

        return header + bytes(payload)

    @staticmethod
    def deserialize(data: bytes) -> BPlusTreeIndex:
        if not isinstance(data, bytes):
            raise TypeError(
                "Serialized B+Tree must be bytes."
            )

        if len(data) < HEADER_SIZE:
            raise ValueError(
                "Serialized B+Tree is too short."
            )

        magic, version, payload_length = struct.unpack_from(
            HEADER_FORMAT,
            data,
            0,
        )

        if magic != MAGIC:
            raise ValueError(
                "Invalid B+Tree magic."
            )

        if version != VERSION:
            raise ValueError(
                f"Unsupported B+Tree version: {version}"
            )

        if len(data) != HEADER_SIZE + payload_length:
            raise ValueError(
                "Invalid B+Tree payload length."
            )

        offset = HEADER_SIZE

        if offset + 12 > len(data):
            raise ValueError(
                "Corrupted B+Tree payload."
            )

        order, root_id, node_count = struct.unpack_from(
            ">III",
            data,
            offset,
        )

        offset += 12

        if order < 3:
            raise ValueError(
                "Invalid B+Tree order."
            )

        if node_count == 0:
            raise ValueError(
                "B+Tree must contain at least one node."
            )

        if root_id >= node_count:
            raise ValueError(
                "Invalid B+Tree root ID."
            )

        raw_nodes = []

        for _ in range(node_count):
            if offset + NODE_HEADER_SIZE > len(data):
                raise ValueError(
                    "Corrupted B+Tree node header."
                )

            node_type, key_count, next_id = struct.unpack_from(
                NODE_HEADER_FORMAT,
                data,
                offset,
            )

            offset += NODE_HEADER_SIZE

            keys = []

            for _ in range(key_count):
                key, offset = BTreeSerializer._decode_key(
                    data,
                    offset,
                )

                keys.append(key)

            if keys != sorted(keys):
                raise ValueError(
                    "B+Tree node keys are not sorted."
                )

            if node_type == LEAF_NODE:
                values = []

                for _ in range(key_count):
                    if offset + 4 > len(data):
                        raise ValueError(
                            "Corrupted B+Tree leaf values."
                        )

                    record_count = struct.unpack_from(
                        ">I",
                        data,
                        offset,
                    )[0]

                    offset += 4

                    record_ids = []

                    for _ in range(record_count):
                        if offset + 8 > len(data):
                            raise ValueError(
                                "Corrupted B+Tree record ID."
                            )

                        record_id = struct.unpack_from(
                            ">II",
                            data,
                            offset,
                        )

                        offset += 8

                        record_ids.append(record_id)

                    values.append(record_ids)

                if (
                    next_id != 0xFFFFFFFF
                    and next_id >= node_count
                ):
                    raise ValueError(
                        "Invalid B+Tree leaf link."
                    )

                raw_nodes.append(
                    {
                        "type": LEAF_NODE,
                        "keys": keys,
                        "values": values,
                        "next": (
                            None
                            if next_id == 0xFFFFFFFF
                            else next_id
                        ),
                    }
                )

            elif node_type == INTERNAL_NODE:
                child_count = key_count + 1

                if (
                    offset + (child_count * 4)
                    > len(data)
                ):
                    raise ValueError(
                        "Corrupted B+Tree child list."
                    )

                children = list(
                    struct.unpack_from(
                        f">{child_count}I",
                        data,
                        offset,
                    )
                )

                offset += child_count * 4

                for child_id in children:
                    if child_id >= node_count:
                        raise ValueError(
                            "Invalid B+Tree child ID."
                        )

                if next_id != 0xFFFFFFFF:
                    raise ValueError(
                        "Internal node cannot contain leaf link."
                    )

                raw_nodes.append(
                    {
                        "type": INTERNAL_NODE,
                        "keys": keys,
                        "children": children,
                    }
                )

            else:
                raise ValueError(
                    f"Unsupported B+Tree node type: {node_type}"
                )

        if offset != len(data):
            raise ValueError(
                "Trailing bytes in B+Tree payload."
            )

        nodes = []

        for raw_node in raw_nodes:
            node = BTreeNode.__new__(BTreeNode)

            node.leaf = (
                raw_node["type"] == LEAF_NODE
            )

            node.keys = list(
                raw_node["keys"]
            )

            node.values = []
            node.children = []
            node.next_leaf = None

            if node.leaf:
                node.values = [
                    list(record_ids)
                    for record_ids in raw_node["values"]
                ]

            nodes.append(node)

        for index, raw_node in enumerate(raw_nodes):
            if raw_node["type"] == INTERNAL_NODE:
                nodes[index].children = [
                    nodes[child_id]
                    for child_id in raw_node["children"]
                ]

        for index, raw_node in enumerate(raw_nodes):
            if raw_node["type"] == LEAF_NODE:
                next_id = raw_node["next"]

                if next_id is not None:
                    nodes[index].next_leaf = nodes[next_id]

        for node in nodes:
            node.validate()

        tree = BPlusTreeIndex(
            name="loaded_index",
            column="loaded_column",
            order=order,
        )

        tree.root = nodes[root_id]

        tree.validate()

        return tree

    @staticmethod
    def _encode_key(key: Any) -> bytes:
        if key is None:
            return struct.pack(
                ">B",
                KEY_NONE,
            )

        if type(key) is bool:
            return struct.pack(
                ">BB",
                KEY_BOOL,
                1 if key else 0,
            )

        if type(key) is int:
            return struct.pack(
                ">Bq",
                KEY_INT,
                key,
            )

        if type(key) is float:
            return struct.pack(
                ">Bd",
                KEY_FLOAT,
                key,
            )

        if type(key) is str:
            encoded = key.encode("utf-8")

            if len(encoded) > 0xFFFFFFFF:
                raise ValueError(
                    "Index key is too large."
                )

            return (
                struct.pack(
                    ">BI",
                    KEY_TEXT,
                    len(encoded),
                )
                + encoded
            )

        raise TypeError(
            f"Unsupported index key type: {type(key).__name__}"
        )

    @staticmethod
    def _decode_key(
        data: bytes,
        offset: int,
    ) -> tuple[Any, int]:
        if offset + 1 > len(data):
            raise ValueError(
                "Corrupted index key."
            )

        key_type = data[offset]

        offset += 1

        if key_type == KEY_NONE:
            return None, offset

        if key_type == KEY_BOOL:
            if offset + 1 > len(data):
                raise ValueError(
                    "Corrupted BOOLEAN index key."
                )

            value = data[offset] != 0

            return value, offset + 1

        if key_type == KEY_INT:
            if offset + 8 > len(data):
                raise ValueError(
                    "Corrupted INTEGER index key."
                )

            value = struct.unpack_from(
                ">q",
                data,
                offset,
            )[0]

            return value, offset + 8

        if key_type == KEY_FLOAT:
            if offset + 8 > len(data):
                raise ValueError(
                    "Corrupted FLOAT index key."
                )

            value = struct.unpack_from(
                ">d",
                data,
                offset,
            )[0]

            return value, offset + 8

        if key_type == KEY_TEXT:
            if offset + 4 > len(data):
                raise ValueError(
                    "Corrupted TEXT index key."
                )

            length = struct.unpack_from(
                ">I",
                data,
                offset,
            )[0]

            offset += 4

            if offset + length > len(data):
                raise ValueError(
                    "Corrupted TEXT index key."
                )

            raw = data[
                offset:offset + length
            ]

            try:
                value = raw.decode("utf-8")
            except UnicodeDecodeError as exc:
                raise ValueError(
                    "Index key contains invalid UTF-8."
                ) from exc

            return value, offset + length

        raise ValueError(
            f"Unsupported index key type: {key_type}"
        )

    @staticmethod
    def _encode_record_id(
        record_id: RecordID,
    ) -> bytes:
        if (
            not isinstance(record_id, tuple)
            or len(record_id) != 2
        ):
            raise TypeError(
                "Record ID must be a (page_id, slot_id) tuple."
            )

        page_id, slot_id = record_id

        if type(page_id) is not int:
            raise TypeError(
                "Page ID must be an integer."
            )

        if type(slot_id) is not int:
            raise TypeError(
                "Slot ID must be an integer."
            )

        if page_id <= 0:
            raise ValueError(
                "Record page ID must be greater than zero."
            )

        if slot_id < 0:
            raise ValueError(
                "Record slot ID cannot be negative."
            )

        if (
            page_id > 0xFFFFFFFF
            or slot_id > 0xFFFFFFFF
        ):
            raise ValueError(
                "Record ID value is too large."
            )

        return struct.pack(
            ">II",
            page_id,
            slot_id,
        )