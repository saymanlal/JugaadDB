from pathlib import Path
import struct

from .serializer import MAGIC, VERSION


HEADER_FORMAT = ">4sBI"
HEADER_SIZE = struct.calcsize(HEADER_FORMAT)


class IndexFile:
    def __init__(self, path: str | Path):
        if not isinstance(path, (str, Path)):
            raise TypeError("Index file path must be a string or Path.")

        self.path = Path(path)

    def exists(self) -> bool:
        return self.path.exists()

    def create(self, payload: bytes = b"") -> None:
        if not isinstance(payload, bytes):
            raise TypeError("Index payload must be bytes.")

        if self.exists():
            raise FileExistsError(
                f"Index file already exists: {self.path}"
            )

        self.path.parent.mkdir(parents=True, exist_ok=True)

        data = self._build_file(payload)

        with self.path.open("wb") as file:
            file.write(data)

    def open(self) -> bytes:
        if not self.exists():
            raise FileNotFoundError(
                f"Index file does not exist: {self.path}"
            )

        with self.path.open("rb") as file:
            data = file.read()

        return self._parse_file(data)

    def write(self, payload: bytes) -> None:
        if not isinstance(payload, bytes):
            raise TypeError("Index payload must be bytes.")

        if not self.exists():
            raise FileNotFoundError(
                f"Index file does not exist: {self.path}"
            )

        data = self._build_file(payload)

        with self.path.open("wb") as file:
            file.write(data)

    def read(self) -> bytes:
        return self.open()

    def _build_file(self, payload: bytes) -> bytes:
        header = struct.pack(
            HEADER_FORMAT,
            MAGIC,
            VERSION,
            len(payload),
        )

        return header + payload

    def _parse_file(self, data: bytes) -> bytes:
        if len(data) < HEADER_SIZE:
            raise ValueError("Index file is too short.")

        magic, version, payload_length = struct.unpack_from(
            HEADER_FORMAT,
            data,
            0,
        )

        if magic != MAGIC:
            raise ValueError("Invalid index file magic.")

        if version != VERSION:
            raise ValueError(
                f"Unsupported index file version: {version}"
            )

        expected_length = HEADER_SIZE + payload_length

        if len(data) != expected_length:
            raise ValueError("Invalid index file payload length.")

        return data[HEADER_SIZE:]