from collections import OrderedDict
from dataclasses import dataclass

from .page import Page


@dataclass
class BufferFrame:
    page: Page
    dirty: bool = False
    pin_count: int = 0


class BufferPool:
    def __init__(
        self,
        file_manager,
        capacity: int = 16,
    ):
        if type(capacity) is not int:
            raise TypeError(
                "Buffer pool capacity must be an integer."
            )

        if capacity <= 0:
            raise ValueError(
                "Buffer pool capacity must be greater than zero."
            )

        self.file_manager = file_manager
        self.capacity = capacity
        self._frames: OrderedDict[
            int,
            BufferFrame,
        ] = OrderedDict()
        self._hits = 0
        self._misses = 0

    @property
    def size(self) -> int:
        return len(self._frames)

    @property
    def hits(self) -> int:
        return self._hits

    @property
    def misses(self) -> int:
        return self._misses

    @property
    def hit_rate(self) -> float:
        total = self._hits + self._misses

        if total == 0:
            return 0.0

        return self._hits / total

    @property
    def dirty_count(self) -> int:
        return sum(
            1
            for frame in self._frames.values()
            if frame.dirty
        )

    @property
    def dirty_page_ids(self) -> list[int]:
        return [
            page_id
            for page_id, frame in self._frames.items()
            if frame.dirty
        ]

    @property
    def pinned_page_ids(self) -> list[int]:
        return [
            page_id
            for page_id, frame in self._frames.items()
            if frame.pin_count > 0
        ]

    def contains(
        self,
        page_id: int,
    ) -> bool:
        self._validate_page_id(page_id)

        return page_id in self._frames

    def is_dirty(
        self,
        page_id: int,
    ) -> bool:
        self._validate_page_id(page_id)

        frame = self._frames.get(page_id)

        if frame is None:
            return False

        return frame.dirty

    def is_pinned(
        self,
        page_id: int,
    ) -> bool:
        self._validate_page_id(page_id)

        frame = self._frames.get(page_id)

        if frame is None:
            return False

        return frame.pin_count > 0

    def fetch(
        self,
        page_id: int,
    ) -> Page:
        self._validate_page_id(page_id)

        frame = self._frames.get(page_id)

        if frame is not None:
            self._hits += 1
            self._frames.move_to_end(page_id)
            return frame.page

        self._misses += 1

        page = self.file_manager.read_page(
            page_id
        )

        self._ensure_capacity()

        self._frames[page_id] = BufferFrame(
            page=page
        )

        return page

    def new_page(self) -> Page:
        page = self.file_manager.allocate_page()

        self._ensure_capacity()

        self._frames[page.page_id] = BufferFrame(
            page=page
        )

        return page

    def mark_dirty(
        self,
        page_id: int,
    ) -> None:
        self._validate_page_id(page_id)

        frame = self._get_frame(page_id)

        frame.dirty = True

        self._frames.move_to_end(page_id)

    def mark_clean(
        self,
        page_id: int,
    ) -> None:
        self._validate_page_id(page_id)

        frame = self._get_frame(page_id)

        frame.dirty = False

        self._frames.move_to_end(page_id)

    def store(
        self,
        page: Page,
    ) -> None:
        if not isinstance(page, Page):
            raise TypeError(
                "Buffer pool can only store Page instances."
            )

        self._validate_page_id(
            page.page_id
        )

        frame = self._frames.get(
            page.page_id
        )

        if frame is None:
            self._ensure_capacity()

            self._frames[page.page_id] = (
                BufferFrame(
                    page=page,
                    dirty=True,
                )
            )

            return

        frame.page = page
        frame.dirty = True

        self._frames.move_to_end(
            page.page_id
        )

    def pin(
        self,
        page_id: int,
    ) -> Page:
        self._validate_page_id(page_id)

        frame = self._get_frame(page_id)

        frame.pin_count += 1

        self._frames.move_to_end(
            page_id
        )

        return frame.page

    def unpin(
        self,
        page_id: int,
    ) -> None:
        self._validate_page_id(page_id)

        frame = self._get_frame(page_id)

        if frame.pin_count == 0:
            raise ValueError(
                f"Page is not pinned: {page_id}"
            )

        frame.pin_count -= 1

    def flush(
        self,
        page_id: int,
    ) -> None:
        self._validate_page_id(page_id)

        frame = self._get_frame(page_id)

        if not frame.dirty:
            return

        self.file_manager.write_page(
            frame.page
        )

        frame.dirty = False

        self._frames.move_to_end(
            page_id
        )

    def flush_dirty(
        self,
        max_pages: int | None = None,
    ) -> list[int]:
        if max_pages is not None:
            if type(max_pages) is not int:
                raise TypeError(
                    "max_pages must be an integer."
                )

            if max_pages <= 0:
                raise ValueError(
                    "max_pages must be greater than zero."
                )

        dirty_page_ids = list(
            self.dirty_page_ids
        )

        if max_pages is not None:
            dirty_page_ids = dirty_page_ids[
                :max_pages
            ]

        flushed = []

        for page_id in dirty_page_ids:
            self.flush(page_id)
            flushed.append(page_id)

        return flushed

    def flush_all(self) -> None:
        for page_id in list(
            self._frames.keys()
        ):
            self.flush(page_id)

    def evict(
        self,
        page_id: int,
    ) -> None:
        self._validate_page_id(page_id)

        frame = self._frames.get(page_id)

        if frame is None:
            return

        if frame.pin_count > 0:
            raise ValueError(
                f"Cannot evict pinned page: {page_id}"
            )

        if frame.dirty:
            self.file_manager.write_page(
                frame.page
            )

        del self._frames[page_id]

    def clear(self) -> None:
        self.flush_all()
        self._frames.clear()

    def clear_clean(self) -> list[int]:
        removed = []

        for page_id, frame in list(
            self._frames.items()
        ):
            if frame.dirty:
                continue

            if frame.pin_count > 0:
                continue

            del self._frames[page_id]
            removed.append(page_id)

        return removed

    def _ensure_capacity(self) -> None:
        if len(self._frames) < self.capacity:
            return

        for page_id, frame in list(
            self._frames.items()
        ):
            if frame.pin_count > 0:
                continue

            self.evict(page_id)
            return

        raise RuntimeError(
            "Buffer pool has no evictable pages."
        )

    def _get_frame(
        self,
        page_id: int,
    ) -> BufferFrame:
        frame = self._frames.get(page_id)

        if frame is None:
            raise ValueError(
                f"Page is not loaded in buffer pool: {page_id}"
            )

        return frame

    def _validate_page_id(
        self,
        page_id: int,
    ) -> None:
        if type(page_id) is not int:
            raise TypeError(
                "Page ID must be an integer."
            )

        if page_id < 0:
            raise ValueError(
                "Page ID cannot be negative."
            )