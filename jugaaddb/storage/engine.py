import json
from pathlib import Path
from typing import Any


class StorageEngine:
    MAGIC = "JUGAADDB"
    VERSION = 1

    def __init__(self, path: str):
        self.path = Path(path)

    def create(self) -> None:
        if self.path.exists():
            raise FileExistsError(
                f"Database already exists: {self.path}"
            )

        data = {
            "header": {
                "magic": self.MAGIC,
                "version": self.VERSION,
            },
            "catalog": {
                "tables": {}
            }
        }

        self._write(data)

    def load(self) -> dict[str, Any]:
        if not self.path.exists():
            raise FileNotFoundError(
                f"Database does not exist: {self.path}"
            )

        with self.path.open("r", encoding="utf-8") as file:
            data = json.load(file)

        self._validate_header(data)

        return data

    def save(self, data: dict[str, Any]) -> None:
        self._write(data)

    def _write(self, data: dict[str, Any]) -> None:
        temp_path = self.path.with_suffix(
            self.path.suffix + ".tmp"
        )

        with temp_path.open("w", encoding="utf-8") as file:
            json.dump(
                data,
                file,
                indent=2,
                ensure_ascii=False
            )

        temp_path.replace(self.path)

    def _validate_header(self, data: dict[str, Any]) -> None:
        header = data.get("header", {})

        if header.get("magic") != self.MAGIC:
            raise ValueError(
                "Invalid JugaadDB file."
            )

        if header.get("version") != self.VERSION:
            raise ValueError(
                "Unsupported JugaadDB file version."
            )