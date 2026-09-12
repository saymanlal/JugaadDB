from .constants import PAGE_SIZE


class Page:
    def __init__(
        self,
        page_id: int,
        data: bytes | None = None
    ):
        if page_id < 0:
            raise ValueError("Page ID cannot be negative.")

        self.page_id = page_id

        if data is None:
            self.data = bytearray(PAGE_SIZE)
        else:
            if len(data) != PAGE_SIZE:
                raise ValueError(
                    f"Page must contain exactly {PAGE_SIZE} bytes."
                )

            self.data = bytearray(data)

    def read(self) -> bytes:
        return bytes(self.data)

    def write(self, data: bytes) -> None:
        if len(data) > PAGE_SIZE:
            raise ValueError(
                f"Data exceeds page size of {PAGE_SIZE} bytes."
            )

        self.data[:] = b"\x00" * PAGE_SIZE
        self.data[:len(data)] = data

    def is_empty(self) -> bool:
        return all(byte == 0 for byte in self.data)