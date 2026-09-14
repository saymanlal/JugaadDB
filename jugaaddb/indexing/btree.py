from dataclasses import dataclass, field
from typing import Any

from .base import Index, IndexEntry, RecordID


@dataclass
class BTreeNode:
    leaf: bool
    keys: list[Any] = field(default_factory=list)
    values: list[list[RecordID]] = field(default_factory=list)
    children: list["BTreeNode"] = field(default_factory=list)
    next_leaf: "BTreeNode | None" = None

    def __post_init__(self):
        if not isinstance(self.leaf, bool):
            raise TypeError("Leaf flag must be a boolean.")

        if self.leaf:
            if self.children:
                raise ValueError("Leaf nodes cannot have children.")
            if len(self.keys) != len(self.values):
                raise ValueError("Leaf keys and values must have equal length.")
        else:
            if self.values:
                raise ValueError("Internal nodes cannot contain record values.")
            if len(self.children) != len(self.keys) + 1:
                raise ValueError(
                    "Internal node must have exactly len(keys) + 1 children."
                )

    def is_leaf(self) -> bool:
        return self.leaf

    def key_count(self) -> int:
        return len(self.keys)

    def child_count(self) -> int:
        return len(self.children)

    def validate(self) -> None:
        if self.keys != sorted(self.keys):
            raise ValueError("Node keys must be sorted.")

        if self.leaf:
            if self.children:
                raise ValueError("Leaf nodes cannot have children.")
            if len(self.keys) != len(self.values):
                raise ValueError("Leaf keys and values must have equal length.")
        else:
            if self.values:
                raise ValueError("Internal nodes cannot contain record values.")
            if len(self.children) != len(self.keys) + 1:
                raise ValueError(
                    "Internal node must have exactly len(keys) + 1 children."
                )


@dataclass(frozen=True)
class _SplitResult:
    separator: Any
    right: BTreeNode


class BPlusTreeIndex(Index):
    def __init__(
        self,
        name: str,
        column: str,
        order: int = 4,
    ):
        super().__init__(name, column)

        if type(order) is not int:
            raise TypeError("B+Tree order must be an integer.")

        if order < 3:
            raise ValueError("B+Tree order must be at least 3.")

        self.order = order
        self.root = BTreeNode(leaf=True)

    def insert(
        self,
        key: Any,
        record_id: RecordID,
    ) -> None:
        self._validate_record_id(record_id)

        split = self._insert_recursive(
            self.root,
            key,
            record_id,
        )

        if split is None:
            return

        old_root = self.root

        self.root = BTreeNode(
            leaf=False,
            keys=[split.separator],
            children=[
                old_root,
                split.right,
            ],
        )

    def delete(
        self,
        key: Any,
        record_id: RecordID,
    ) -> None:
        self._validate_record_id(record_id)

        deleted = self._delete_recursive(
            self.root,
            key,
            record_id,
            is_root=True,
        )

        if not deleted:
            raise ValueError(
                f"Record ID does not exist in index: {record_id}"
            )

        if not self.root.leaf and len(self.root.children) == 1:
            self.root = self.root.children[0]

        if not self.root.leaf and not self.root.children:
            self.root = BTreeNode(leaf=True)

        self._refresh_separators(self.root)

    def search(
        self,
        key: Any,
    ) -> list[RecordID]:
        node = self.root

        while not node.leaf:
            child_index = self._find_child_index(
                node,
                key,
            )
            node = node.children[child_index]

        for index, existing_key in enumerate(node.keys):
            if existing_key == key:
                return list(node.values[index])

        return []

    def search_range(
        self,
        start_key: Any | None = None,
        end_key: Any | None = None,
        include_start: bool = True,
        include_end: bool = True,
    ) -> list[IndexEntry]:
        if start_key is not None and end_key is not None:
            if start_key > end_key:
                return []

        node = self._find_start_leaf(start_key)
        entries = []

        while node is not None:
            for key, record_ids in zip(
                node.keys,
                node.values,
            ):
                if start_key is not None:
                    if include_start:
                        if key < start_key:
                            continue
                    else:
                        if key <= start_key:
                            continue

                if end_key is not None:
                    if include_end:
                        if key > end_key:
                            return entries
                    else:
                        if key >= end_key:
                            return entries

                for record_id in record_ids:
                    entries.append(
                        IndexEntry(
                            key,
                            record_id,
                        )
                    )

            node = node.next_leaf

        return entries

    def scan(self) -> list[IndexEntry]:
        entries = []
        leaf = self._leftmost_leaf()

        while leaf is not None:
            for key, record_ids in zip(
                leaf.keys,
                leaf.values,
            ):
                for record_id in record_ids:
                    entries.append(
                        IndexEntry(
                            key,
                            record_id,
                        )
                    )

            leaf = leaf.next_leaf

        return entries

    def validate(self) -> None:
        leaves = []

        self._validate_structure(
            self.root,
            minimum_key=None,
            maximum_key=None,
            expected_leaf_depth=None,
            depth=0,
            leaves=leaves,
        )

        if not leaves:
            raise ValueError(
                "B+Tree must contain at least one leaf."
            )

        for index in range(len(leaves) - 1):
            if leaves[index].next_leaf is not leaves[index + 1]:
                raise ValueError(
                    "Leaf linkage is invalid."
                )

        if leaves[-1].next_leaf is not None:
            raise ValueError(
                "Last leaf must not point to another leaf."
            )

        chained = []
        current = leaves[0]

        while current is not None:
            chained.append(current)
            current = current.next_leaf

        if chained != leaves:
            raise ValueError(
                "Leaf chain does not match tree traversal."
            )

        self._validate_separators(
            self.root
        )

    def _insert_recursive(
        self,
        node: BTreeNode,
        key: Any,
        record_id: RecordID,
    ) -> _SplitResult | None:
        if node.leaf:
            self._insert_into_leaf(
                node,
                key,
                record_id,
            )

            if node.key_count() < self.order:
                return None

            return self._split_leaf(node)

        child_index = self._find_child_index(
            node,
            key,
        )

        child = node.children[child_index]

        split = self._insert_recursive(
            child,
            key,
            record_id,
        )

        if split is None:
            return None

        node.keys.insert(
            child_index,
            split.separator,
        )

        node.children.insert(
            child_index + 1,
            split.right,
        )

        if node.key_count() < self.order:
            return None

        return self._split_internal(node)

    def _insert_into_leaf(
        self,
        leaf: BTreeNode,
        key: Any,
        record_id: RecordID,
    ) -> None:
        for index, existing_key in enumerate(
            leaf.keys
        ):
            if existing_key == key:
                if record_id in leaf.values[index]:
                    raise ValueError(
                        f"Record ID already exists in index: "
                        f"{record_id}"
                    )

                leaf.values[index].append(
                    record_id
                )
                return

            if key < existing_key:
                leaf.keys.insert(
                    index,
                    key,
                )

                leaf.values.insert(
                    index,
                    [record_id],
                )

                return

        leaf.keys.append(key)
        leaf.values.append([record_id])

    def _split_leaf(
        self,
        leaf: BTreeNode,
    ) -> _SplitResult:
        split_point = len(leaf.keys) // 2

        left_keys = leaf.keys[:split_point]
        left_values = leaf.values[:split_point]

        right_keys = leaf.keys[split_point:]
        right_values = leaf.values[split_point:]

        if not right_keys:
            raise ValueError(
                "Cannot split leaf without a right-side key."
            )

        right = BTreeNode(
            leaf=True,
            keys=right_keys,
            values=right_values,
        )

        old_next = leaf.next_leaf

        leaf.keys = left_keys
        leaf.values = left_values
        leaf.next_leaf = right

        right.next_leaf = old_next

        return _SplitResult(
            separator=right.keys[0],
            right=right,
        )

    def _split_internal(
        self,
        node: BTreeNode,
    ) -> _SplitResult:
        middle_index = len(node.keys) // 2
        separator = node.keys[middle_index]

        left_keys = node.keys[:middle_index]
        right_keys = node.keys[middle_index + 1:]

        left_children = node.children[
            :middle_index + 1
        ]

        right_children = node.children[
            middle_index + 1:
        ]

        right = BTreeNode(
            leaf=False,
            keys=right_keys,
            children=right_children,
        )

        node.keys = left_keys
        node.children = left_children

        return _SplitResult(
            separator=separator,
            right=right,
        )

    def _delete_recursive(
        self,
        node: BTreeNode,
        key: Any,
        record_id: RecordID,
        is_root: bool,
    ) -> bool:
        if node.leaf:
            return self._delete_from_leaf(
                node,
                key,
                record_id,
            )

        child_index = self._find_child_index(
            node,
            key,
        )

        child = node.children[child_index]

        deleted = self._delete_recursive(
            child,
            key,
            record_id,
            is_root=False,
        )

        if not deleted:
            return False

        minimum_keys = self._minimum_keys()

        if (
            len(child.keys) < minimum_keys
            and len(node.children) > 1
        ):
            self._rebalance_child(
                node,
                child_index,
            )

        self._refresh_node_separators(node)

        return True

    def _delete_from_leaf(
        self,
        leaf: BTreeNode,
        key: Any,
        record_id: RecordID,
    ) -> bool:
        for index, existing_key in enumerate(
            leaf.keys
        ):
            if existing_key != key:
                continue

            if record_id not in leaf.values[index]:
                return False

            leaf.values[index].remove(
                record_id
            )

            if leaf.values[index]:
                return True

            del leaf.keys[index]
            del leaf.values[index]

            return True

        return False

    def _rebalance_child(
        self,
        parent: BTreeNode,
        child_index: int,
    ) -> None:
        child = parent.children[child_index]

        if child_index > 0:
            left = parent.children[
                child_index - 1
            ]

            if len(left.keys) > self._minimum_keys():
                self._borrow_from_left(
                    parent,
                    child_index,
                )
                return

        if child_index < len(parent.children) - 1:
            right = parent.children[
                child_index + 1
            ]

            if len(right.keys) > self._minimum_keys():
                self._borrow_from_right(
                    parent,
                    child_index,
                )
                return

        if child_index > 0:
            self._merge_children(
                parent,
                child_index - 1,
            )
            return

        if child_index < len(parent.children) - 1:
            self._merge_children(
                parent,
                child_index,
            )

    def _borrow_from_left(
        self,
        parent: BTreeNode,
        child_index: int,
    ) -> None:
        left = parent.children[
            child_index - 1
        ]

        child = parent.children[
            child_index
        ]

        if child.leaf:
            key = left.keys.pop()
            values = left.values.pop()

            child.keys.insert(
                0,
                key,
            )

            child.values.insert(
                0,
                values,
            )

        else:
            separator = parent.keys[
                child_index - 1
            ]

            borrowed_key = left.keys.pop()
            borrowed_child = left.children.pop()

            child.keys.insert(
                0,
                separator,
            )

            child.children.insert(
                0,
                borrowed_child,
            )

            parent.keys[
                child_index - 1
            ] = borrowed_key

        self._refresh_node_separators(
            parent
        )

    def _borrow_from_right(
        self,
        parent: BTreeNode,
        child_index: int,
    ) -> None:
        child = parent.children[
            child_index
        ]

        right = parent.children[
            child_index + 1
        ]

        if child.leaf:
            key = right.keys.pop(0)
            values = right.values.pop(0)

            child.keys.append(key)
            child.values.append(values)

        else:
            separator = parent.keys[
                child_index
            ]

            borrowed_key = right.keys.pop(0)
            borrowed_child = right.children.pop(0)

            child.keys.append(
                separator
            )

            child.children.append(
                borrowed_child
            )

            parent.keys[
                child_index
            ] = borrowed_key

        self._refresh_node_separators(
            parent
        )

    def _merge_children(
        self,
        parent: BTreeNode,
        left_index: int,
    ) -> None:
        left = parent.children[
            left_index
        ]

        right = parent.children[
            left_index + 1
        ]

        if left.leaf:
            left.keys.extend(
                right.keys
            )

            left.values.extend(
                right.values
            )

            left.next_leaf = right.next_leaf

        else:
            separator = parent.keys[
                left_index
            ]

            left.keys.append(
                separator
            )

            left.keys.extend(
                right.keys
            )

            left.children.extend(
                right.children
            )

        del parent.children[
            left_index + 1
        ]

        if parent.keys:
            del parent.keys[
                left_index
            ]

        self._refresh_node_separators(
            parent
        )

    def _refresh_separators(
        self,
        node: BTreeNode,
    ) -> None:
        if node.leaf:
            return

        for child in node.children:
            self._refresh_separators(
                child
            )

        self._refresh_node_separators(
            node
        )

    def _refresh_node_separators(
        self,
        node: BTreeNode,
    ) -> None:
        if node.leaf:
            return

        node.keys = [
            self._first_key(
                node.children[index + 1]
            )
            for index in range(
                len(node.children) - 1
            )
        ]

    def _first_key(
        self,
        node: BTreeNode,
    ):
        current = node

        while not current.leaf:
            current = current.children[0]

        if not current.keys:
            raise ValueError(
                "Cannot derive separator from empty subtree."
            )

        return current.keys[0]

    def _minimum_keys(self) -> int:
        return max(
            1,
            (self.order + 1) // 2,
        )

    def _find_child_index(
        self,
        node: BTreeNode,
        key: Any,
    ) -> int:
        for index, existing_key in enumerate(
            node.keys
        ):
            if key < existing_key:
                return index

        return len(node.keys)

    def _find_start_leaf(
        self,
        key: Any | None,
    ) -> BTreeNode:
        if key is None:
            return self._leftmost_leaf()

        node = self.root

        while not node.leaf:
            child_index = self._find_child_index(
                node,
                key,
            )

            node = node.children[
                child_index
            ]

        return node

    def _leftmost_leaf(self) -> BTreeNode:
        node = self.root

        while not node.leaf:
            node = node.children[0]

        return node

    def _validate_structure(
        self,
        node: BTreeNode,
        minimum_key: Any,
        maximum_key: Any,
        expected_leaf_depth: int | None,
        depth: int,
        leaves: list[BTreeNode],
    ) -> int:
        node.validate()

        if node.leaf:
            if (
                minimum_key is not None
                and node.keys
            ):
                if node.keys[0] < minimum_key:
                    raise ValueError(
                        "Leaf contains key below its allowed range."
                    )

            if (
                maximum_key is not None
                and node.keys
            ):
                if node.keys[-1] >= maximum_key:
                    raise ValueError(
                        "Leaf contains key above its allowed range."
                    )

            leaves.append(node)

            if expected_leaf_depth is None:
                return depth

            if depth != expected_leaf_depth:
                raise ValueError(
                    "All leaves must exist at the same depth."
                )

            return expected_leaf_depth

        if not node.children:
            raise ValueError(
                "Internal node must contain children."
            )

        for index in range(
            len(node.children)
        ):
            child_minimum = minimum_key
            child_maximum = maximum_key

            if index > 0:
                child_minimum = node.keys[
                    index - 1
                ]

            if index < len(node.keys):
                child_maximum = node.keys[
                    index
                ]

            expected_leaf_depth = (
                self._validate_structure(
                    node.children[index],
                    child_minimum,
                    child_maximum,
                    expected_leaf_depth,
                    depth + 1,
                    leaves,
                )
            )

        return expected_leaf_depth

    def _validate_separators(
        self,
        node: BTreeNode,
    ) -> tuple[Any, Any] | None:
        if node.leaf:
            if not node.keys:
                return None

            return (
                node.keys[0],
                node.keys[-1],
            )

        child_ranges = []

        for child in node.children:
            child_range = (
                self._validate_separators(
                    child
                )
            )

            if child_range is None:
                raise ValueError(
                    "Internal node contains an empty child."
                )

            child_ranges.append(
                child_range
            )

        for index, separator in enumerate(
            node.keys
        ):
            right_minimum = child_ranges[
                index + 1
            ][0]

            if separator != right_minimum:
                raise ValueError(
                    "Internal separator must equal "
                    "first key of right child."
                )

            left_maximum = child_ranges[
                index
            ][1]

            if left_maximum >= separator:
                raise ValueError(
                    "Left child contains key greater than "
                    "or equal to separator."
                )

        return (
            child_ranges[0][0],
            child_ranges[-1][1],
        )

    def _validate_record_id(
        self,
        record_id: RecordID,
    ) -> None:
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