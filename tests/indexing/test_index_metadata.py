import pytest

from jugaaddb.indexing.metadata import IndexMetadata


def test_index_metadata_defaults():
    metadata = IndexMetadata(
        table_name="students",
        index_name="idx_students_id",
        column="id",
    )

    assert metadata.table_name == "students"
    assert metadata.index_name == "idx_students_id"
    assert metadata.column == "id"
    assert metadata.index_type == "btree"
    assert metadata.order == 4
    assert metadata.unique is False


def test_index_metadata_custom_values():
    metadata = IndexMetadata(
        table_name="students",
        index_name="idx_students_email",
        column="email",
        index_type="BTREE",
        order=8,
        unique=True,
    )

    assert metadata.index_type == "btree"
    assert metadata.order == 8
    assert metadata.unique is True


def test_index_metadata_to_dict():
    metadata = IndexMetadata(
        table_name="students",
        index_name="idx_students_id",
        column="id",
        order=4,
        unique=True,
    )

    assert metadata.to_dict() == {
        "table_name": "students",
        "index_name": "idx_students_id",
        "column": "id",
        "index_type": "btree",
        "order": 4,
        "unique": True,
    }


def test_index_metadata_from_dict():
    data = {
        "table_name": "students",
        "index_name": "idx_students_id",
        "column": "id",
        "index_type": "btree",
        "order": 6,
        "unique": True,
    }

    metadata = IndexMetadata.from_dict(data)

    assert metadata.table_name == "students"
    assert metadata.index_name == "idx_students_id"
    assert metadata.column == "id"
    assert metadata.index_type == "btree"
    assert metadata.order == 6
    assert metadata.unique is True


def test_index_metadata_round_trip():
    original = IndexMetadata(
        table_name="students",
        index_name="idx_students_id",
        column="id",
        index_type="btree",
        order=5,
        unique=True,
    )

    restored = IndexMetadata.from_dict(original.to_dict())

    assert restored == original


def test_index_metadata_normalizes_index_type():
    metadata = IndexMetadata(
        table_name="students",
        index_name="idx_students_id",
        column="id",
        index_type="BtReE",
    )

    assert metadata.index_type == "btree"


def test_index_metadata_rejects_empty_table_name():
    with pytest.raises(ValueError):
        IndexMetadata(
            table_name="",
            index_name="idx_students_id",
            column="id",
        )


def test_index_metadata_rejects_empty_index_name():
    with pytest.raises(ValueError):
        IndexMetadata(
            table_name="students",
            index_name="",
            column="id",
        )


def test_index_metadata_rejects_empty_column():
    with pytest.raises(ValueError):
        IndexMetadata(
            table_name="students",
            index_name="idx_students_id",
            column="",
        )


def test_index_metadata_rejects_unknown_type():
    with pytest.raises(ValueError):
        IndexMetadata(
            table_name="students",
            index_name="idx_students_id",
            column="id",
            index_type="unknown",
        )


def test_index_metadata_rejects_invalid_order_type():
    with pytest.raises(TypeError):
        IndexMetadata(
            table_name="students",
            index_name="idx_students_id",
            column="id",
            order="4",
        )


def test_index_metadata_rejects_small_order():
    with pytest.raises(ValueError):
        IndexMetadata(
            table_name="students",
            index_name="idx_students_id",
            column="id",
            order=2,
        )


def test_index_metadata_rejects_invalid_unique_type():
    with pytest.raises(TypeError):
        IndexMetadata(
            table_name="students",
            index_name="idx_students_id",
            column="id",
            unique=1,
        )


def test_index_metadata_from_dict_requires_core_fields():
    with pytest.raises(ValueError):
        IndexMetadata.from_dict(
            {
                "table_name": "students",
                "column": "id",
            }
        )


def test_index_metadata_from_dict_rejects_non_dict():
    with pytest.raises(TypeError):
        IndexMetadata.from_dict("invalid")