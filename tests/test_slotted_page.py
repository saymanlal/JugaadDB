import pytest

from jugaaddb.storage.slotted_page import SlottedPage


def test_new_slotted_page_is_empty():
    page = SlottedPage(1)

    assert page.page_id == 1
    assert page.slot_count_total() == 0
    assert page.free_space() > 0


def test_insert_and_read_record():
    page = SlottedPage(1)

    slot_id = page.insert(b"hello")

    assert slot_id == 0
    assert page.slot_count_total() == 1
    assert page.read(0) == b"hello"


def test_multiple_records():
    page = SlottedPage(1)

    first = page.insert(b"first")
    second = page.insert(b"second")
    third = page.insert(b"third")

    assert first == 0
    assert second == 1
    assert third == 2

    assert page.read(0) == b"first"
    assert page.read(1) == b"second"
    assert page.read(2) == b"third"


def test_variable_length_records():
    page = SlottedPage(1)

    page.insert(b"A")
    page.insert(b"longer record")
    page.insert(b"x" * 500)

    assert page.read(0) == b"A"
    assert page.read(1) == b"longer record"
    assert page.read(2) == b"x" * 500


def test_free_space_decreases_after_insert():
    page = SlottedPage(1)

    before = page.free_space()

    page.insert(b"hello")

    after = page.free_space()

    assert after < before


def test_delete_record():
    page = SlottedPage(1)

    slot_id = page.insert(b"hello")

    assert page.read(slot_id) == b"hello"

    page.delete(slot_id)

    assert page.is_deleted(slot_id)
    assert page.read(slot_id) == b""


def test_deleted_slot_still_exists():
    page = SlottedPage(1)

    slot_id = page.insert(b"hello")

    page.delete(slot_id)

    assert page.slot_count_total() == 1


def test_invalid_slot_rejected():
    page = SlottedPage(1)

    with pytest.raises(ValueError):
        page.read(0)


def test_negative_slot_rejected():
    page = SlottedPage(1)

    with pytest.raises(ValueError):
        page.read(-1)


def test_non_integer_slot_rejected():
    page = SlottedPage(1)

    with pytest.raises(TypeError):
        page.read("0")


def test_non_bytes_record_rejected():
    page = SlottedPage(1)

    with pytest.raises(TypeError):
        page.insert("hello")


def test_page_rejects_record_that_is_too_large():
    page = SlottedPage(1)

    with pytest.raises(ValueError):
        page.insert(b"x" * 4096)