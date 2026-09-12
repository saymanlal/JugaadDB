import json
import struct
from pathlib import Path
from typing import Any

from .constants import (
    PAGE_SIZE,
    PAYLOAD_LENGTH_SIZE,
)
from .file_manager import FileManager
from .page import Page


class StorageEngine:
    """
    Binary storage engine for JugaadDB.

    Current transitional layout:

        Page 0
        ┌──────────────────────────────┐
        │ JugaadDB File Header        │
        └──────────────────────────────┘

        Page 1+
        ┌──────────────────────────────┐
        │ 4 bytes: payload length     │
        │ serialized database data    │
        │ ...                          │
        └──────────────────────────────┘

    The logical database structure is currently serialized as JSON
    inside the binary page container.

    This is intentionally transitional. Later phases will replace
    this with proper records and slotted pages.
    """

    def __init__(self, path: str):
        self.path = Path(path)
        self.file_manager = FileManager(str(self.path))

    def create(self) -> None:
        """
        Create a new empty JugaadDB binary file.
        """

        self.file_manager.create()

        empty_database = {
            "catalog": {
                "tables": {}
            }
        }

        self.save(empty_database)

    def load(self) -> dict[str, Any]:
        """
        Load database contents from binary pages.
        """

        self.file_manager.open()

        if self.file_manager.data_page_count() == 0:
            return {
                "catalog": {
                    "tables": {}
                }
            }

        payload = self._read_payload()

        if not payload:
            return {
                "catalog": {
                    "tables": {}
                }
            }

        try:
            data = json.loads(
                payload.decode("utf-8")
            )
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ValueError(
                "Corrupted JugaadDB data payload."
            ) from exc

        self._validate_database_structure(data)

        return data

    def save(self, data: dict[str, Any]) -> None:
        """
        Serialize database contents and persist them
        across one or more fixed-size pages.
        """

        self._validate_database_structure(data)

        payload = json.dumps(
            data,
            ensure_ascii=False,
            separators=(",", ":")
        ).encode("utf-8")

        self._write_payload(payload)

    def _write_payload(self, payload: bytes) -> None:
        """
        Write payload across data pages.

        Page 1 contains the payload length followed by
        payload bytes.

        Remaining pages contain continuation payload bytes.
        """

        total_length = len(payload)

        capacity_first_page = (
            PAGE_SIZE - PAYLOAD_LENGTH_SIZE
        )

        if total_length <= capacity_first_page:
            required_pages = 1
        else:
            remaining = total_length - capacity_first_page

            additional_pages = (
                remaining + PAGE_SIZE - 1
            ) // PAGE_SIZE

            required_pages = 1 + additional_pages

        # Allocate missing pages.
        while self.file_manager.data_page_count() < required_pages:
            self.file_manager.allocate_page()

        # Page 1:
        # [4-byte length][first payload chunk]
        first_chunk = payload[:capacity_first_page]

        first_page_data = (
            struct.pack(">I", total_length)
            + first_chunk
        )

        first_page = Page(1)
        first_page.write(first_page_data)

        self.file_manager.write_page(first_page)

        # Remaining pages.
        offset = capacity_first_page

        page_id = 2

        while offset < total_length:
            chunk = payload[
                offset:offset + PAGE_SIZE
            ]

            page = Page(page_id)
            page.write(chunk)

            self.file_manager.write_page(page)

            offset += len(chunk)
            page_id += 1

    def _read_payload(self) -> bytes:
        """
        Read the serialized payload from page 1 onward.
        """

        first_page = self.file_manager.read_page(1)

        first_data = first_page.read()

        if len(first_data) < PAYLOAD_LENGTH_SIZE:
            raise ValueError(
                "Corrupted JugaadDB payload header."
            )

        total_length = struct.unpack(
            ">I",
            first_data[:PAYLOAD_LENGTH_SIZE]
        )[0]

        capacity_first_page = (
            PAGE_SIZE - PAYLOAD_LENGTH_SIZE
        )

        if total_length == 0:
            return b""

        payload = bytearray()

        first_chunk_size = min(
            total_length,
            capacity_first_page
        )

        payload.extend(
            first_data[
                PAYLOAD_LENGTH_SIZE:
                PAYLOAD_LENGTH_SIZE + first_chunk_size
            ]
        )

        remaining = total_length - first_chunk_size

        page_id = 2

        while remaining > 0:
            if page_id >= self.file_manager.page_count():
                raise ValueError(
                    "Corrupted JugaadDB file: "
                    "payload is incomplete."
                )

            page = self.file_manager.read_page(page_id)

            chunk_size = min(
                remaining,
                PAGE_SIZE
            )

            payload.extend(
                page.read()[:chunk_size]
            )

            remaining -= chunk_size
            page_id += 1

        return bytes(payload)

    def _validate_database_structure(
        self,
        data: dict[str, Any]
    ) -> None:

        if not isinstance(data, dict):
            raise TypeError(
                "Database data must be a dictionary."
            )

        catalog = data.get("catalog")

        if not isinstance(catalog, dict):
            raise ValueError(
                "Invalid database structure: missing catalog."
            )

        tables = catalog.get("tables")

        if not isinstance(tables, dict):
            raise ValueError(
                "Invalid database structure: "
                "catalog.tables must be a dictionary."
            )