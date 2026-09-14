import pytest

from jugaaddb.storage.constants import PAGE_SIZE
from jugaaddb.storage.page import Page


def test_new_page_is_empty():
    page = Page(0)

    assert page.page_id == 0
    assert len(page.read()) == PAGE_SIZE
    assert page.is_empty()


def test_page_write_and_read():
    page = Page(1)

    page.write(b"hello")

    assert page.read()[:5] == b"hello"
    assert len(page.read()) == PAGE_SIZE
    assert not page.is_empty()


def test_page_rejects_negative_id():
    with pytest.raises(ValueError):
        Page(-1)


def test_page_rejects_wrong_size_data():
    with pytest.raises(ValueError):
        Page(0, b"too small")


def test_page_rejects_oversized_write():
    page = Page(0)

    with pytest.raises(ValueError):
        page.write(b"x" * (PAGE_SIZE + 1))