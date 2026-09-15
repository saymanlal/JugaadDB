from jugaaddb.storage.buffer_pool import BufferPool
from jugaaddb.storage.file_manager import FileManager
from jugaaddb.storage.page import Page


def create_pool(tmp_path, capacity=4):
    path = tmp_path / "dirty_pages.jdb"

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


def test_new_page_is_clean(
    tmp_path,
):
    file_manager, buffer_pool = create_pool(
        tmp_path
    )

    page = buffer_pool.new_page()

    assert buffer_pool.is_dirty(
        page.page_id
    ) is False

    assert buffer_pool.dirty_count == 0
    assert buffer_pool.dirty_page_ids == []

    file_manager.close = getattr(
        file_manager,
        "close",
        lambda: None,
    )

    file_manager.close()


def test_store_marks_page_dirty(
    tmp_path,
):
    file_manager, buffer_pool = create_pool(
        tmp_path
    )

    page = buffer_pool.new_page()

    buffer_pool.store(page)

    assert buffer_pool.is_dirty(
        page.page_id
    ) is True

    assert buffer_pool.dirty_count == 1
    assert buffer_pool.dirty_page_ids == [
        page.page_id
    ]


def test_mark_dirty_requires_loaded_page(
    tmp_path,
):
    file_manager, buffer_pool = create_pool(
        tmp_path
    )

    page = buffer_pool.new_page()

    page_id = page.page_id

    buffer_pool.clear()

    try:
        buffer_pool.mark_dirty(
            page_id
        )
    except ValueError as error:
        assert str(error) == (
            f"Page is not loaded in buffer pool: {page_id}"
        )
    else:
        raise AssertionError(
            "Expected ValueError."
        )


def test_mark_clean_clears_dirty_state(
    tmp_path,
):
    file_manager, buffer_pool = create_pool(
        tmp_path
    )

    page = buffer_pool.new_page()

    buffer_pool.store(page)

    assert buffer_pool.is_dirty(
        page.page_id
    ) is True

    buffer_pool.mark_clean(
        page.page_id
    )

    assert buffer_pool.is_dirty(
        page.page_id
    ) is False

    assert buffer_pool.dirty_count == 0


def test_flush_dirty_flushes_only_dirty_pages(
    tmp_path,
):
    file_manager, buffer_pool = create_pool(
        tmp_path
    )

    first = buffer_pool.new_page()
    second = buffer_pool.new_page()

    buffer_pool.store(first)

    dirty_pages = buffer_pool.flush_dirty()

    assert dirty_pages == [
        first.page_id
    ]

    assert buffer_pool.is_dirty(
        first.page_id
    ) is False

    assert buffer_pool.is_dirty(
        second.page_id
    ) is False

    assert buffer_pool.dirty_count == 0


def test_flush_dirty_returns_flushed_page_ids(
    tmp_path,
):
    file_manager, buffer_pool = create_pool(
        tmp_path
    )

    first = buffer_pool.new_page()
    second = buffer_pool.new_page()

    buffer_pool.store(first)
    buffer_pool.store(second)

    flushed = buffer_pool.flush_dirty()

    assert set(flushed) == {
        first.page_id,
        second.page_id,
    }

    assert buffer_pool.dirty_page_ids == []


def test_flush_dirty_is_idempotent(
    tmp_path,
):
    file_manager, buffer_pool = create_pool(
        tmp_path
    )

    page = buffer_pool.new_page()

    buffer_pool.store(page)

    first_flush = buffer_pool.flush_dirty()
    second_flush = buffer_pool.flush_dirty()

    assert first_flush == [
        page.page_id
    ]

    assert second_flush == []

    assert buffer_pool.dirty_count == 0


def test_clear_clean_preserves_dirty_pages(
    tmp_path,
):
    file_manager, buffer_pool = create_pool(
        tmp_path
    )

    clean_page = buffer_pool.new_page()
    dirty_page = buffer_pool.new_page()

    buffer_pool.store(dirty_page)

    removed = buffer_pool.clear_clean()

    assert clean_page.page_id in removed

    assert dirty_page.page_id not in removed

    assert buffer_pool.contains(
        dirty_page.page_id
    ) is True

    assert buffer_pool.is_dirty(
        dirty_page.page_id
    ) is True


def test_clear_clean_preserves_pinned_clean_pages(
    tmp_path,
):
    file_manager, buffer_pool = create_pool(
        tmp_path
    )

    page = buffer_pool.new_page()

    buffer_pool.pin(
        page.page_id
    )

    removed = buffer_pool.clear_clean()

    assert page.page_id not in removed

    assert buffer_pool.contains(
        page.page_id
    ) is True

    buffer_pool.unpin(
        page.page_id
    )


def test_dirty_page_is_flushed_before_eviction(
    tmp_path,
):
    file_manager, buffer_pool = create_pool(
        tmp_path,
        capacity=1,
    )

    first = buffer_pool.new_page()

    dirty_data = bytearray(4096)
    dirty_data[:10] = b"dirty-data"

    buffer_pool.store(
        Page(
            first.page_id,
            bytes(dirty_data),
        )
    )

    second = buffer_pool.new_page()

    assert second.page_id != first.page_id

    assert buffer_pool.contains(
        first.page_id
    ) is False

    assert buffer_pool.contains(
        second.page_id
    ) is True

    stored = file_manager.read_page(
        first.page_id
    )

    assert stored.read()[:10] == (
        b"dirty-data"
    )