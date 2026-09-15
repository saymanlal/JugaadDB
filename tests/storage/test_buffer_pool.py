from pathlib import Path

import pytest

from jugaaddb.storage.buffer_pool import BufferPool
from jugaaddb.storage.constants import PAGE_SIZE
from jugaaddb.storage.file_manager import FileManager


def create_file_manager(
    tmp_path: Path,
):
    path = tmp_path / "buffer.jdb"

    file_manager = FileManager(
        str(path)
    )

    file_manager.create()

    return file_manager


def test_buffer_pool_starts_empty(
    tmp_path,
):
    file_manager = create_file_manager(
        tmp_path
    )

    pool = BufferPool(
        file_manager,
        capacity=2,
    )

    assert pool.size == 0
    assert pool.hits == 0
    assert pool.misses == 0
    assert pool.hit_rate == 0.0


def test_fetch_loads_page_into_cache(
    tmp_path,
):
    file_manager = create_file_manager(
        tmp_path
    )

    page = file_manager.allocate_page()

    pool = BufferPool(
        file_manager,
        capacity=2,
    )

    loaded = pool.fetch(
        page.page_id
    )

    assert loaded.page_id == page.page_id
    assert pool.size == 1
    assert pool.misses == 1
    assert pool.hits == 0


def test_fetch_same_page_is_cache_hit(
    tmp_path,
):
    file_manager = create_file_manager(
        tmp_path
    )

    page = file_manager.allocate_page()

    pool = BufferPool(
        file_manager,
        capacity=2,
    )

    first = pool.fetch(
        page.page_id
    )

    second = pool.fetch(
        page.page_id
    )

    assert first is second
    assert pool.hits == 1
    assert pool.misses == 1
    assert pool.hit_rate == 0.5


def test_cache_respects_capacity(
    tmp_path,
):
    file_manager = create_file_manager(
        tmp_path
    )

    page1 = file_manager.allocate_page()
    page2 = file_manager.allocate_page()

    pool = BufferPool(
        file_manager,
        capacity=1,
    )

    pool.fetch(
        page1.page_id
    )

    pool.fetch(
        page2.page_id
    )

    assert pool.size == 1
    assert pool.contains(
        page1.page_id
    ) is False
    assert pool.contains(
        page2.page_id
    ) is True


def test_lru_page_is_evicted(
    tmp_path,
):
    file_manager = create_file_manager(
        tmp_path
    )

    page1 = file_manager.allocate_page()
    page2 = file_manager.allocate_page()

    pool = BufferPool(
        file_manager,
        capacity=2,
    )

    pool.fetch(
        page1.page_id
    )

    pool.fetch(
        page2.page_id
    )

    pool.fetch(
        page1.page_id
    )

    page3 = file_manager.allocate_page()

    pool.fetch(
        page3.page_id
    )

    assert pool.contains(
        page1.page_id
    ) is True

    assert pool.contains(
        page2.page_id
    ) is False

    assert pool.contains(
        page3.page_id
    ) is True


def test_mark_dirty_and_flush(
    tmp_path,
):
    file_manager = create_file_manager(
        tmp_path
    )

    page = file_manager.allocate_page()

    pool = BufferPool(
        file_manager,
        capacity=2,
    )

    loaded = pool.fetch(
        page.page_id
    )

    loaded.data[0:4] = b"TEST"

    pool.mark_dirty(
        page.page_id
    )

    pool.flush(
        page.page_id
    )

    reopened = file_manager.read_page(
        page.page_id
    )

    assert reopened.read()[0:4] == b"TEST"


def test_dirty_page_survives_eviction(
    tmp_path,
):
    file_manager = create_file_manager(
        tmp_path
    )

    page1 = file_manager.allocate_page()
    page2 = file_manager.allocate_page()

    pool = BufferPool(
        file_manager,
        capacity=1,
    )

    loaded = pool.fetch(
        page1.page_id
    )

    loaded.data[0:4] = b"DATA"

    pool.mark_dirty(
        page1.page_id
    )

    pool.fetch(
        page2.page_id
    )

    persisted = file_manager.read_page(
        page1.page_id
    )

    assert persisted.read()[0:4] == b"DATA"


def test_pin_prevents_eviction(
    tmp_path,
):
    file_manager = create_file_manager(
        tmp_path
    )

    page1 = file_manager.allocate_page()
    page2 = file_manager.allocate_page()

    pool = BufferPool(
        file_manager,
        capacity=1,
    )

    pool.fetch(
        page1.page_id
    )

    pool.pin(
        page1.page_id
    )

    with pytest.raises(RuntimeError):
        pool.fetch(
            page2.page_id
        )


def test_unpin_allows_eviction(
    tmp_path,
):
    file_manager = create_file_manager(
        tmp_path
    )

    page1 = file_manager.allocate_page()
    page2 = file_manager.allocate_page()

    pool = BufferPool(
        file_manager,
        capacity=1,
    )

    pool.fetch(
        page1.page_id
    )

    pool.pin(
        page1.page_id
    )

    pool.unpin(
        page1.page_id
    )

    pool.fetch(
        page2.page_id
    )

    assert pool.contains(
        page1.page_id
    ) is False

    assert pool.contains(
        page2.page_id
    ) is True


def test_double_unpin_fails(
    tmp_path,
):
    file_manager = create_file_manager(
        tmp_path
    )

    page = file_manager.allocate_page()

    pool = BufferPool(
        file_manager,
        capacity=2,
    )

    pool.fetch(
        page.page_id
    )

    with pytest.raises(ValueError):
        pool.unpin(
            page.page_id
        )


def test_evict_pinned_page_fails(
    tmp_path,
):
    file_manager = create_file_manager(
        tmp_path
    )

    page = file_manager.allocate_page()

    pool = BufferPool(
        file_manager,
        capacity=2,
    )

    pool.fetch(
        page.page_id
    )

    pool.pin(
        page.page_id
    )

    with pytest.raises(ValueError):
        pool.evict(
            page.page_id
        )


def test_flush_all_writes_dirty_pages(
    tmp_path,
):
    file_manager = create_file_manager(
        tmp_path
    )

    page1 = file_manager.allocate_page()
    page2 = file_manager.allocate_page()

    pool = BufferPool(
        file_manager,
        capacity=2,
    )

    first = pool.fetch(
        page1.page_id
    )

    second = pool.fetch(
        page2.page_id
    )

    first.data[0:3] = b"ONE"
    second.data[0:3] = b"TWO"

    pool.mark_dirty(
        page1.page_id
    )

    pool.mark_dirty(
        page2.page_id
    )

    pool.flush_all()

    assert file_manager.read_page(
        page1.page_id
    ).read()[0:3] == b"ONE"

    assert file_manager.read_page(
        page2.page_id
    ).read()[0:3] == b"TWO"


def test_clear_flushes_and_removes_pages(
    tmp_path,
):
    file_manager = create_file_manager(
        tmp_path
    )

    page = file_manager.allocate_page()

    pool = BufferPool(
        file_manager,
        capacity=2,
    )

    loaded = pool.fetch(
        page.page_id
    )

    loaded.data[0:5] = b"HELLO"

    pool.mark_dirty(
        page.page_id
    )

    pool.clear()

    assert pool.size == 0
    assert file_manager.read_page(
        page.page_id
    ).read()[0:5] == b"HELLO"


def test_invalid_capacity_fails(
    tmp_path,
):
    file_manager = create_file_manager(
        tmp_path
    )

    with pytest.raises(ValueError):
        BufferPool(
            file_manager,
            capacity=0,
        )


def test_invalid_page_id_fails(
    tmp_path,
):
    file_manager = create_file_manager(
        tmp_path
    )

    pool = BufferPool(
        file_manager
    )

    with pytest.raises(ValueError):
        pool.fetch(-1)


def test_non_integer_page_id_fails(
    tmp_path,
):
    file_manager = create_file_manager(
        tmp_path
    )

    pool = BufferPool(
        file_manager
    )

    with pytest.raises(TypeError):
        pool.fetch("1")