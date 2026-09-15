import pytest

from jugaaddb.storage.buffer_pool import BufferPool
from jugaaddb.storage.file_manager import FileManager
from jugaaddb.storage.page import Page


class FailingFileManager:
    def __init__(
        self,
        file_manager,
        failing_page_id,
    ):
        self._file_manager = file_manager
        self.failing_page_id = failing_page_id

    def read_page(
        self,
        page_id,
    ):
        return self._file_manager.read_page(
            page_id
        )

    def allocate_page(self):
        return self._file_manager.allocate_page()

    def write_page(
        self,
        page,
    ):
        if page.page_id == self.failing_page_id:
            raise IOError(
                "Simulated page write failure."
            )

        return self._file_manager.write_page(
            page
        )


def create_pool(
    tmp_path,
    capacity=4,
):
    path = tmp_path / "buffer_hardening.jdb"

    file_manager = FileManager(
        str(path)
    )

    file_manager.create()

    buffer_pool = BufferPool(
        file_manager,
        capacity=capacity,
    )

    return (
        file_manager,
        buffer_pool,
    )


def test_dirty_count_tracks_multiple_pages(
    tmp_path,
):
    file_manager, buffer_pool = create_pool(
        tmp_path
    )

    first = buffer_pool.new_page()
    second = buffer_pool.new_page()
    third = buffer_pool.new_page()

    buffer_pool.store(first)
    buffer_pool.store(third)

    assert buffer_pool.dirty_count == 2

    assert set(
        buffer_pool.dirty_page_ids
    ) == {
        first.page_id,
        third.page_id,
    }


def test_pinned_page_is_reported(
    tmp_path,
):
    file_manager, buffer_pool = create_pool(
        tmp_path
    )

    page = buffer_pool.new_page()

    buffer_pool.pin(
        page.page_id
    )

    assert buffer_pool.is_pinned(
        page.page_id
    ) is True

    assert buffer_pool.pinned_page_ids == [
        page.page_id
    ]

    buffer_pool.unpin(
        page.page_id
    )

    assert buffer_pool.is_pinned(
        page.page_id
    ) is False


def test_flush_dirty_supports_partial_flush(
    tmp_path,
):
    file_manager, buffer_pool = create_pool(
        tmp_path
    )

    first = buffer_pool.new_page()
    second = buffer_pool.new_page()
    third = buffer_pool.new_page()

    buffer_pool.store(first)
    buffer_pool.store(second)
    buffer_pool.store(third)

    flushed = buffer_pool.flush_dirty(
        max_pages=2
    )

    assert flushed == [
        first.page_id,
        second.page_id,
    ]

    assert buffer_pool.dirty_count == 1

    assert buffer_pool.dirty_page_ids == [
        third.page_id
    ]


def test_flush_dirty_rejects_invalid_max_pages(
    tmp_path,
):
    file_manager, buffer_pool = create_pool(
        tmp_path
    )

    with pytest.raises(
        TypeError,
        match="max_pages must be an integer",
    ):
        buffer_pool.flush_dirty(
            max_pages="2"
        )

    with pytest.raises(
        ValueError,
        match="max_pages must be greater than zero",
    ):
        buffer_pool.flush_dirty(
            max_pages=0
        )

    with pytest.raises(
        ValueError,
        match="max_pages must be greater than zero",
    ):
        buffer_pool.flush_dirty(
            max_pages=-1
        )


def test_failed_flush_keeps_page_dirty(
    tmp_path,
):
    file_manager, buffer_pool = create_pool(
        tmp_path
    )

    page = buffer_pool.new_page()

    buffer_pool.store(
        Page(
            page.page_id,
            bytes(
                bytearray(4096)
            ),
        )
    )

    failing_manager = FailingFileManager(
        file_manager,
        page.page_id,
    )

    buffer_pool.file_manager = (
        failing_manager
    )

    with pytest.raises(
        IOError,
        match="Simulated page write failure",
    ):
        buffer_pool.flush(
            page.page_id
        )

    assert buffer_pool.contains(
        page.page_id
    ) is True

    assert buffer_pool.is_dirty(
        page.page_id
    ) is True

    assert buffer_pool.dirty_count == 1


def test_failed_dirty_eviction_keeps_page_cached(
    tmp_path,
):
    file_manager, buffer_pool = create_pool(
        tmp_path,
        capacity=1,
    )

    first = buffer_pool.new_page()

    buffer_pool.store(
        Page(
            first.page_id,
            bytes(
                bytearray(4096)
            ),
        )
    )

    failing_manager = FailingFileManager(
        file_manager,
        first.page_id,
    )

    buffer_pool.file_manager = (
        failing_manager
    )

    with pytest.raises(
        IOError,
        match="Simulated page write failure",
    ):
        buffer_pool.evict(
            first.page_id
        )

    assert buffer_pool.contains(
        first.page_id
    ) is True

    assert buffer_pool.is_dirty(
        first.page_id
    ) is True


def test_dirty_page_cannot_be_removed_by_clear_clean(
    tmp_path,
):
    file_manager, buffer_pool = create_pool(
        tmp_path
    )

    page = buffer_pool.new_page()

    buffer_pool.store(page)

    removed = buffer_pool.clear_clean()

    assert page.page_id not in removed

    assert buffer_pool.contains(
        page.page_id
    ) is True

    assert buffer_pool.is_dirty(
        page.page_id
    ) is True


def test_pinned_page_cannot_be_evicted(
    tmp_path,
):
    file_manager, buffer_pool = create_pool(
        tmp_path
    )

    page = buffer_pool.new_page()

    buffer_pool.pin(
        page.page_id
    )

    with pytest.raises(
        ValueError,
        match="Cannot evict pinned page",
    ):
        buffer_pool.evict(
            page.page_id
        )

    assert buffer_pool.contains(
        page.page_id
    ) is True

    buffer_pool.unpin(
        page.page_id
    )


def test_full_flush_clears_all_dirty_pages(
    tmp_path,
):
    file_manager, buffer_pool = create_pool(
        tmp_path
    )

    pages = [
        buffer_pool.new_page()
        for _ in range(4)
    ]

    for page in pages:
        buffer_pool.store(page)

    assert buffer_pool.dirty_count == 4

    buffer_pool.flush_all()

    assert buffer_pool.dirty_count == 0

    assert buffer_pool.dirty_page_ids == []


def test_mark_clean_does_not_remove_page(
    tmp_path,
):
    file_manager, buffer_pool = create_pool(
        tmp_path
    )

    page = buffer_pool.new_page()

    buffer_pool.store(page)

    buffer_pool.mark_clean(
        page.page_id
    )

    assert buffer_pool.contains(
        page.page_id
    ) is True

    assert buffer_pool.is_dirty(
        page.page_id
    ) is False