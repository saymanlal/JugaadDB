import pytest

from jugaaddb.indexing import BPlusTreeIndex, BTreeNode


def test_new_btree_has_leaf_root():
    tree = BPlusTreeIndex("idx_students_id", "id")

    assert tree.root.is_leaf()
    assert tree.root.key_count() == 0
    assert tree.root.child_count() == 0


def test_btree_default_order():
    tree = BPlusTreeIndex("idx_students_id", "id")

    assert tree.order == 4


def test_btree_custom_order():
    tree = BPlusTreeIndex(
        "idx_students_id",
        "id",
        order=8,
    )

    assert tree.order == 8


def test_btree_rejects_invalid_order():
    with pytest.raises(ValueError):
        BPlusTreeIndex(
            "idx_students_id",
            "id",
            order=2,
        )


def test_btree_rejects_non_integer_order():
    with pytest.raises(TypeError):
        BPlusTreeIndex(
            "idx_students_id",
            "id",
            order=4.5,
        )


def test_leaf_node_accepts_matching_keys_and_values():
    node = BTreeNode(
        leaf=True,
        keys=[10, 20],
        values=[
            [(1, 0)],
            [(1, 1)],
        ],
    )

    node.validate()

    assert node.key_count() == 2


def test_leaf_node_rejects_children():
    with pytest.raises(ValueError):
        BTreeNode(
            leaf=True,
            keys=[],
            values=[],
            children=[BTreeNode(leaf=True)],
        )


def test_leaf_node_rejects_mismatched_values():
    with pytest.raises(ValueError):
        BTreeNode(
            leaf=True,
            keys=[10],
            values=[],
        )


def test_internal_node_accepts_keys_and_children():
    left = BTreeNode(leaf=True)
    right = BTreeNode(leaf=True)

    node = BTreeNode(
        leaf=False,
        keys=[10],
        children=[left, right],
    )

    node.validate()

    assert node.key_count() == 1
    assert node.child_count() == 2


def test_internal_node_requires_key_count_plus_one_children():
    with pytest.raises(ValueError):
        BTreeNode(
            leaf=False,
            keys=[10, 20],
            children=[
                BTreeNode(leaf=True),
                BTreeNode(leaf=True),
            ],
        )


def test_internal_node_cannot_contain_values():
    with pytest.raises(ValueError):
        BTreeNode(
            leaf=False,
            keys=[10],
            values=[[(1, 0)]],
            children=[
                BTreeNode(leaf=True),
                BTreeNode(leaf=True),
            ],
        )


def test_node_keys_must_be_sorted():
    node = BTreeNode(
        leaf=True,
        keys=[20, 10],
        values=[
            [(1, 0)],
            [(1, 1)],
        ],
    )

    with pytest.raises(ValueError):
        node.validate()


def test_empty_tree_validates():
    tree = BPlusTreeIndex("idx_students_id", "id")

    tree.validate()
    
def test_empty_btree_search_returns_empty():
    tree = BPlusTreeIndex("idx_students_id", "id")

    assert tree.search(100) == []


def test_single_leaf_search():
    tree = BPlusTreeIndex("idx_students_id", "id")

    tree.root = BTreeNode(
        leaf=True,
        keys=[10, 20, 30],
        values=[
            [(1, 0)],
            [(1, 1)],
            [(1, 2)],
        ],
    )

    assert tree.search(10) == [(1, 0)]
    assert tree.search(20) == [(1, 1)]
    assert tree.search(30) == [(1, 2)]


def test_single_leaf_missing_key():
    tree = BPlusTreeIndex("idx_students_id", "id")

    tree.root = BTreeNode(
        leaf=True,
        keys=[10, 20, 30],
        values=[
            [(1, 0)],
            [(1, 1)],
            [(1, 2)],
        ],
    )

    assert tree.search(15) == []
    assert tree.search(99) == []


def test_internal_node_search_left_child():
    tree = BPlusTreeIndex("idx_students_id", "id")

    left = BTreeNode(
        leaf=True,
        keys=[10, 20],
        values=[
            [(1, 0)],
            [(1, 1)],
        ],
    )

    right = BTreeNode(
        leaf=True,
        keys=[30, 40],
        values=[
            [(2, 0)],
            [(2, 1)],
        ],
    )

    tree.root = BTreeNode(
        leaf=False,
        keys=[30],
        children=[left, right],
    )

    assert tree.search(10) == [(1, 0)]
    assert tree.search(20) == [(1, 1)]


def test_internal_node_search_right_child():
    tree = BPlusTreeIndex("idx_students_id", "id")

    left = BTreeNode(
        leaf=True,
        keys=[10, 20],
        values=[
            [(1, 0)],
            [(1, 1)],
        ],
    )

    right = BTreeNode(
        leaf=True,
        keys=[30, 40],
        values=[
            [(2, 0)],
            [(2, 1)],
        ],
    )

    tree.root = BTreeNode(
        leaf=False,
        keys=[30],
        children=[left, right],
    )

    assert tree.search(30) == [(2, 0)]
    assert tree.search(40) == [(2, 1)]


def test_internal_node_missing_key():
    tree = BPlusTreeIndex("idx_students_id", "id")

    left = BTreeNode(
        leaf=True,
        keys=[10, 20],
        values=[
            [(1, 0)],
            [(1, 1)],
        ],
    )

    right = BTreeNode(
        leaf=True,
        keys=[30, 40],
        values=[
            [(2, 0)],
            [(2, 1)],
        ],
    )

    tree.root = BTreeNode(
        leaf=False,
        keys=[30],
        children=[left, right],
    )

    assert tree.search(25) == []
    assert tree.search(50) == []


def test_multi_level_search():
    tree = BPlusTreeIndex("idx_students_id", "id")

    leaf1 = BTreeNode(
        leaf=True,
        keys=[10, 20],
        values=[
            [(1, 0)],
            [(1, 1)],
        ],
    )

    leaf2 = BTreeNode(
        leaf=True,
        keys=[30, 40],
        values=[
            [(2, 0)],
            [(2, 1)],
        ],
    )

    leaf3 = BTreeNode(
     leaf=True,
     keys=[50, 60],
     values=[
        [(3, 0)],
        [(3, 1)],
     ],
   )

    middle1 = BTreeNode(
        leaf=False,
        keys=[30],
        children=[leaf1, leaf2],
    )

    middle2 = BTreeNode(
     leaf=False,
     keys=[60],
     children=[
        leaf3,
        BTreeNode(
            leaf=True,
            keys=[70],
            values=[[(4, 0)]],
        ),
     ],
 )

    tree.root = BTreeNode(
    leaf=False,
    keys=[50],
    children=[middle1, middle2],
    ) 

    assert tree.search(10) == [(1, 0)]
    assert tree.search(20) == [(1, 1)]
    assert tree.search(30) == [(2, 0)]
    assert tree.search(40) == [(2, 1)]
    assert tree.search(50) == [(3, 0)]
    
def test_insert_into_empty_tree():
    tree = BPlusTreeIndex("idx_students_id", "id")

    tree.insert(10, (1, 0))

    assert tree.root.keys == [10]
    assert tree.root.values == [[(1, 0)]]
    assert tree.search(10) == [(1, 0)]


def test_insert_multiple_keys_keeps_sorted_order():
    tree = BPlusTreeIndex("idx_students_id", "id")

    tree.insert(30, (1, 2))
    tree.insert(10, (1, 0))
    tree.insert(20, (1, 1))

    assert tree.root.keys == [10, 20, 30]
    assert tree.search(10) == [(1, 0)]
    assert tree.search(20) == [(1, 1)]
    assert tree.search(30) == [(1, 2)]


def test_insert_duplicate_key_supports_multiple_records():
    tree = BPlusTreeIndex("idx_students_department", "department")

    tree.insert("CSE", (1, 0))
    tree.insert("CSE", (1, 1))
    tree.insert("CSE", (2, 0))

    assert tree.root.keys == ["CSE"]
    assert tree.search("CSE") == [
        (1, 0),
        (1, 1),
        (2, 0),
    ]


def test_duplicate_record_id_is_rejected():
    tree = BPlusTreeIndex("idx_students_id", "id")

    tree.insert(10, (1, 0))

    with pytest.raises(ValueError):
        tree.insert(10, (1, 0))


def test_insert_at_beginning():
    tree = BPlusTreeIndex("idx_students_id", "id")

    tree.insert(20, (1, 1))
    tree.insert(10, (1, 0))

    assert tree.root.keys == [10, 20]


def test_insert_at_middle():
    tree = BPlusTreeIndex("idx_students_id", "id")

    tree.insert(10, (1, 0))
    tree.insert(30, (1, 2))
    tree.insert(20, (1, 1))

    assert tree.root.keys == [10, 20, 30]


def test_insert_at_end():
    tree = BPlusTreeIndex("idx_students_id", "id")

    tree.insert(10, (1, 0))
    tree.insert(20, (1, 1))
    tree.insert(30, (1, 2))

    assert tree.root.keys == [10, 20, 30]


def test_full_leaf_splits_on_new_distinct_key():
    tree = BPlusTreeIndex(
        "idx_students_id",
        "id",
        order=4,
    )

    tree.insert(10, (1, 0))
    tree.insert(20, (1, 1))
    tree.insert(30, (1, 2))
    tree.insert(40, (1, 3))

    assert tree.root.leaf is False
    assert tree.root.keys == [30]
    assert tree.search(10) == [(1, 0)]
    assert tree.search(20) == [(1, 1)]
    assert tree.search(30) == [(1, 2)]
    assert tree.search(40) == [(1, 3)]


def test_full_leaf_still_accepts_duplicate_key():
    tree = BPlusTreeIndex(
        "idx_students_department",
        "department",
        order=4,
    )

    tree.insert("CSE", (1, 0))
    tree.insert("ECE", (1, 1))
    tree.insert("IT", (1, 2))
    tree.insert("CSE", (2, 0))

    assert tree.search("CSE") == [
        (1, 0),
        (2, 0),
    ]


def test_insert_keeps_tree_valid():
    tree = BPlusTreeIndex("idx_students_id", "id")

    tree.insert(50, (1, 0))
    tree.insert(10, (1, 1))
    tree.insert(30, (1, 2))

    tree.validate()

    assert tree.root.keys == [10, 30, 50]
    
def test_root_leaf_splits_when_full():
    tree = BPlusTreeIndex(
        "idx_students_id",
        "id",
        order=4,
    )

    tree.insert(10, (1, 0))
    tree.insert(20, (1, 1))
    tree.insert(30, (1, 2))
    tree.insert(40, (1, 3))

    assert tree.root.leaf is False
    assert tree.root.keys == [30]
    assert len(tree.root.children) == 2


def test_root_split_creates_correct_left_leaf():
    tree = BPlusTreeIndex(
        "idx_students_id",
        "id",
        order=4,
    )

    tree.insert(10, (1, 0))
    tree.insert(20, (1, 1))
    tree.insert(30, (1, 2))
    tree.insert(40, (1, 3))

    left = tree.root.children[0]

    assert left.leaf is True
    assert left.keys == [10, 20]
    assert left.values == [
        [(1, 0)],
        [(1, 1)],
    ]


def test_root_split_creates_correct_right_leaf():
    tree = BPlusTreeIndex(
        "idx_students_id",
        "id",
        order=4,
    )

    tree.insert(10, (1, 0))
    tree.insert(20, (1, 1))
    tree.insert(30, (1, 2))
    tree.insert(40, (1, 3))

    right = tree.root.children[1]

    assert right.leaf is True
    assert right.keys == [30, 40]
    assert right.values == [
        [(1, 2)],
        [(1, 3)],
    ]


def test_root_split_preserves_search():
    tree = BPlusTreeIndex(
        "idx_students_id",
        "id",
        order=4,
    )

    tree.insert(10, (1, 0))
    tree.insert(20, (1, 1))
    tree.insert(30, (1, 2))
    tree.insert(40, (1, 3))

    assert tree.search(10) == [(1, 0)]
    assert tree.search(20) == [(1, 1)]
    assert tree.search(30) == [(1, 2)]
    assert tree.search(40) == [(1, 3)]
    assert tree.search(99) == []


def test_root_split_creates_leaf_link():
    tree = BPlusTreeIndex(
        "idx_students_id",
        "id",
        order=4,
    )

    tree.insert(10, (1, 0))
    tree.insert(20, (1, 1))
    tree.insert(30, (1, 2))
    tree.insert(40, (1, 3))

    left = tree.root.children[0]
    right = tree.root.children[1]

    assert left.next_leaf is right
    assert right.next_leaf is None


def test_root_split_preserves_duplicate_keys():
    tree = BPlusTreeIndex(
        "idx_students_department",
        "department",
        order=4,
    )

    tree.insert("CSE", (1, 0))
    tree.insert("ECE", (1, 1))
    tree.insert("IT", (1, 2))
    tree.insert("CSE", (2, 0))

    assert tree.search("CSE") == [
        (1, 0),
        (2, 0),
    ]


def test_root_split_with_reverse_insertion():
    tree = BPlusTreeIndex(
        "idx_students_id",
        "id",
        order=4,
    )

    tree.insert(40, (1, 3))
    tree.insert(30, (1, 2))
    tree.insert(20, (1, 1))
    tree.insert(10, (1, 0))

    assert tree.root.keys == [30]

    left = tree.root.children[0]
    right = tree.root.children[1]

    assert left.keys == [10, 20]
    assert right.keys == [30, 40]


def test_root_split_validates():
    tree = BPlusTreeIndex(
        "idx_students_id",
        "id",
        order=4,
    )

    tree.insert(10, (1, 0))
    tree.insert(20, (1, 1))
    tree.insert(30, (1, 2))
    tree.insert(40, (1, 3))

    tree.validate()

def test_insert_into_left_child_after_root_split():
    tree = BPlusTreeIndex(
        "idx_students_id",
        "id",
        order=4,
    )

    tree.insert(10, (1, 0))
    tree.insert(20, (1, 1))
    tree.insert(30, (1, 2))
    tree.insert(40, (1, 3))
    tree.insert(15, (1, 4))

    assert tree.root.leaf is False
    assert tree.search(10) == [(1, 0)]
    assert tree.search(15) == [(1, 4)]
    assert tree.search(20) == [(1, 1)]
    assert tree.search(30) == [(1, 2)]
    assert tree.search(40) == [(1, 3)]


def test_insert_into_right_child_after_root_split():
    tree = BPlusTreeIndex(
        "idx_students_id",
        "id",
        order=4,
    )

    tree.insert(10, (1, 0))
    tree.insert(20, (1, 1))
    tree.insert(30, (1, 2))
    tree.insert(40, (1, 3))
    tree.insert(50, (1, 4))

    assert tree.root.leaf is False
    assert tree.root.keys == [30]
    assert len(tree.root.children) == 2
    assert tree.root.children[0].keys == [10, 20]
    assert tree.root.children[1].keys == [30, 40, 50]

    assert tree.search(50) == [(1, 4)]


def test_second_leaf_split():
    tree = BPlusTreeIndex(
        "idx_students_id",
        "id",
        order=4,
    )

    for index, key in enumerate([10, 20, 30, 40, 50, 60, 70]):
        tree.insert(key, (1, index))

    assert tree.root.leaf is False
    assert tree.root.keys == [30, 50]
    assert len(tree.root.children) == 3


def test_three_leaf_search():
    tree = BPlusTreeIndex(
        "idx_students_id",
        "id",
        order=4,
    )

    keys = [10, 20, 30, 40, 50, 60, 70]

    for index, key in enumerate(keys):
        tree.insert(key, (1, index))

    for index, key in enumerate(keys):
        assert tree.search(key) == [(1, index)]

    assert tree.search(999) == []


def test_leaf_chain_across_multiple_leaves():
    tree = BPlusTreeIndex(
        "idx_students_id",
        "id",
        order=4,
    )

    for index, key in enumerate([10, 20, 30, 40, 50, 60, 70]):
        tree.insert(key, (1, index))

    leaves = []
    current = tree.root

    while not current.leaf:
        current = current.children[0]

    while current is not None:
        leaves.append(current)
        current = current.next_leaf

    assert [leaf.keys for leaf in leaves] == [
        [10, 20],
        [30, 40],
        [50, 60, 70],
    ]


def test_scan_returns_sorted_index_entries():
    tree = BPlusTreeIndex(
        "idx_students_id",
        "id",
        order=4,
    )

    for index, key in enumerate([70, 10, 50, 20, 60, 30, 40]):
        tree.insert(key, (1, index))

    entries = tree.scan()

    assert [entry.key for entry in entries] == [
        10,
        20,
        30,
        40,
        50,
        60,
        70,
    ]


def test_internal_node_split_creates_new_root():
    tree = BPlusTreeIndex(
        "idx_students_id",
        "id",
        order=4,
    )

    keys = list(range(10, 100, 10))

    for index, key in enumerate(keys):
        tree.insert(key, (1, index))

    assert tree.root.leaf is False
    assert tree.root.key_count() >= 2
    assert tree.root.child_count() == tree.root.key_count() + 1


def test_search_after_internal_node_split():
    tree = BPlusTreeIndex(
        "idx_students_id",
        "id",
        order=4,
    )

    keys = list(range(10, 100, 10))

    for index, key in enumerate(keys):
        tree.insert(key, (1, index))

    for index, key in enumerate(keys):
        assert tree.search(key) == [(1, index)]

    assert tree.search(999) == []


def test_reverse_insertion_across_multiple_levels():
    tree = BPlusTreeIndex(
        "idx_students_id",
        "id",
        order=4,
    )

    keys = list(range(10, 100, 10))

    for index, key in enumerate(reversed(keys)):
        tree.insert(key, (1, 8 - index))

    for index, key in enumerate(keys):
        assert tree.search(key) == [(1, index)]

    tree.validate()


def test_validate_multi_level_tree():
    tree = BPlusTreeIndex(
        "idx_students_id",
        "id",
        order=4,
    )

    for index, key in enumerate(range(10, 200, 10)):
        tree.insert(key, (1, index))

    tree.validate()


def test_duplicate_key_survives_multi_leaf_tree():
    tree = BPlusTreeIndex(
        "idx_students_department",
        "department",
        order=4,
    )

    for index, department in enumerate(
        ["CSE", "ECE", "IT", "ME", "CE", "CSE", "EE", "AI"]
    ):
        tree.insert(department, (1, index))

    assert tree.search("CSE") == [
        (1, 0),
        (1, 5),
    ]


def test_duplicate_record_id_is_still_rejected():
    tree = BPlusTreeIndex(
        "idx_students_id",
        "id",
        order=4,
    )

    tree.insert(10, (1, 0))

    with pytest.raises(ValueError):
        tree.insert(10, (1, 0))
        
def test_range_scan_with_both_boundaries():
    tree = BPlusTreeIndex(
        "idx_students_id",
        "id",
        order=4,
    )

    for index, key in enumerate(range(10, 100, 10)):
        tree.insert(key, (1, index))

    entries = tree.search_range(30, 70)

    assert [(entry.key, entry.record_id) for entry in entries] == [
        (30, (1, 2)),
        (40, (1, 3)),
        (50, (1, 4)),
        (60, (1, 5)),
        (70, (1, 6)),
    ]


def test_range_scan_exclusive_boundaries():
    tree = BPlusTreeIndex(
        "idx_students_id",
        "id",
        order=4,
    )

    for index, key in enumerate(range(10, 100, 10)):
        tree.insert(key, (1, index))

    entries = tree.search_range(
        30,
        70,
        include_start=False,
        include_end=False,
    )

    assert [entry.key for entry in entries] == [
        40,
        50,
        60,
    ]


def test_range_scan_left_open():
    tree = BPlusTreeIndex(
        "idx_students_id",
        "id",
        order=4,
    )

    for index, key in enumerate(range(10, 100, 10)):
        tree.insert(key, (1, index))

    entries = tree.search_range(None, 30)

    assert [entry.key for entry in entries] == [
        10,
        20,
        30,
    ]


def test_range_scan_right_open():
    tree = BPlusTreeIndex(
        "idx_students_id",
        "id",
        order=4,
    )

    for index, key in enumerate(range(10, 100, 10)):
        tree.insert(key, (1, index))

    entries = tree.search_range(70, None)

    assert [entry.key for entry in entries] == [
        70,
        80,
        90,
    ]


def test_range_scan_empty_result():
    tree = BPlusTreeIndex(
        "idx_students_id",
        "id",
        order=4,
    )

    for index, key in enumerate(range(10, 100, 10)):
        tree.insert(key, (1, index))

    assert tree.search_range(35, 39) == []


def test_range_scan_reversed_bounds():
    tree = BPlusTreeIndex(
        "idx_students_id",
        "id",
        order=4,
    )

    for index, key in enumerate(range(10, 100, 10)):
        tree.insert(key, (1, index))

    assert tree.search_range(70, 30) == []


def test_range_scan_across_many_leaves():
    tree = BPlusTreeIndex(
        "idx_students_id",
        "id",
        order=4,
    )

    keys = list(range(10, 210, 10))

    for index, key in enumerate(keys):
        tree.insert(key, (1, index))

    entries = tree.search_range(55, 155)

    assert [entry.key for entry in entries] == [
        60,
        70,
        80,
        90,
        100,
        110,
        120,
        130,
        140,
        150,
    ]


def test_range_scan_preserves_duplicate_records():
    tree = BPlusTreeIndex(
        "idx_students_department",
        "department",
        order=4,
    )

    tree.insert("CSE", (1, 0))
    tree.insert("CSE", (1, 1))
    tree.insert("ECE", (1, 2))
    tree.insert("IT", (1, 3))

    entries = tree.search_range("CSE", "CSE")

    assert [(entry.key, entry.record_id) for entry in entries] == [
        ("CSE", (1, 0)),
        ("CSE", (1, 1)),
    ]


def test_validate_after_many_splits():
    tree = BPlusTreeIndex(
        "idx_students_id",
        "id",
        order=4,
    )

    for index, key in enumerate(range(10, 1000, 10)):
        tree.insert(key, (1, index))

    tree.validate()


def test_range_scan_after_reverse_insertion():
    tree = BPlusTreeIndex(
        "idx_students_id",
        "id",
        order=4,
    )

    keys = list(range(10, 210, 10))

    for index, key in enumerate(reversed(keys)):
        tree.insert(key, (1, len(keys) - index - 1))

    entries = tree.search_range(50, 120)

    assert [entry.key for entry in entries] == [
        50,
        60,
        70,
        80,
        90,
        100,
        110,
        120,
    ]

    tree.validate()