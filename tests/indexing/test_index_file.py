import struct

import pytest

from jugaaddb.indexing.index_file import (
    HEADER_FORMAT,
    HEADER_SIZE,
    IndexFile,
)
from jugaaddb.indexing.serializer import MAGIC, VERSION


def test_index_file_does_not_exist_initially(tmp_path):
    path = tmp_path / "students.jidx"

    index_file = IndexFile(path)

    assert index_file.exists() is False


def test_create_index_file(tmp_path):
    path = tmp_path / "students.jidx"

    index_file = IndexFile(path)
    index_file.create(b"hello")

    assert path.exists()
    assert index_file.exists()


def test_create_and_read_payload(tmp_path):
    path = tmp_path / "students.jidx"

    index_file = IndexFile(path)
    index_file.create(b"hello")

    assert index_file.read() == b"hello"


def test_open_returns_payload(tmp_path):
    path = tmp_path / "students.jidx"

    index_file = IndexFile(path)
    index_file.create(b"payload")

    assert index_file.open() == b"payload"


def test_write_replaces_payload(tmp_path):
    path = tmp_path / "students.jidx"

    index_file = IndexFile(path)
    index_file.create(b"old")
    index_file.write(b"new")

    assert index_file.read() == b"new"


def test_empty_payload_is_supported(tmp_path):
    path = tmp_path / "students.jidx"

    index_file = IndexFile(path)
    index_file.create()

    assert index_file.read() == b""


def test_create_rejects_existing_file(tmp_path):
    path = tmp_path / "students.jidx"

    index_file = IndexFile(path)
    index_file.create(b"first")

    with pytest.raises(FileExistsError):
        index_file.create(b"second")


def test_open_rejects_missing_file(tmp_path):
    path = tmp_path / "missing.jidx"

    index_file = IndexFile(path)

    with pytest.raises(FileNotFoundError):
        index_file.open()


def test_read_rejects_missing_file(tmp_path):
    path = tmp_path / "missing.jidx"

    index_file = IndexFile(path)

    with pytest.raises(FileNotFoundError):
        index_file.read()


def test_write_rejects_missing_file(tmp_path):
    path = tmp_path / "missing.jidx"

    index_file = IndexFile(path)

    with pytest.raises(FileNotFoundError):
        index_file.write(b"payload")


def test_create_rejects_non_bytes_payload(tmp_path):
    path = tmp_path / "students.jidx"

    index_file = IndexFile(path)

    with pytest.raises(TypeError):
        index_file.create("payload")


def test_write_rejects_non_bytes_payload(tmp_path):
    path = tmp_path / "students.jidx"

    index_file = IndexFile(path)
    index_file.create(b"payload")

    with pytest.raises(TypeError):
        index_file.write("new payload")


def test_invalid_magic_is_rejected(tmp_path):
    path = tmp_path / "students.jidx"

    index_file = IndexFile(path)
    index_file.create(b"payload")

    data = bytearray(path.read_bytes())
    data[0:4] = b"XXXX"
    path.write_bytes(bytes(data))

    with pytest.raises(ValueError):
        index_file.read()


def test_invalid_version_is_rejected(tmp_path):
    path = tmp_path / "students.jidx"

    index_file = IndexFile(path)
    index_file.create(b"payload")

    data = bytearray(path.read_bytes())
    data[4] = VERSION + 1
    path.write_bytes(bytes(data))

    with pytest.raises(ValueError):
        index_file.read()


def test_truncated_file_is_rejected(tmp_path):
    path = tmp_path / "students.jidx"

    index_file = IndexFile(path)
    index_file.create(b"payload")

    path.write_bytes(path.read_bytes()[:HEADER_SIZE - 1])

    with pytest.raises(ValueError):
        index_file.read()


def test_invalid_payload_length_is_rejected(tmp_path):
    path = tmp_path / "students.jidx"

    index_file = IndexFile(path)
    index_file.create(b"payload")

    data = bytearray(path.read_bytes())

    struct.pack_into(
        HEADER_FORMAT,
        data,
        0,
        MAGIC,
        VERSION,
        999999,
    )

    path.write_bytes(bytes(data))

    with pytest.raises(ValueError):
        index_file.read()


def test_trailing_bytes_are_rejected(tmp_path):
    path = tmp_path / "students.jidx"

    index_file = IndexFile(path)
    index_file.create(b"payload")

    path.write_bytes(path.read_bytes() + b"\x00")

    with pytest.raises(ValueError):
        index_file.read()


def test_nested_parent_directory_is_created(tmp_path):
    path = tmp_path / "indexes" / "students" / "students.jidx"

    index_file = IndexFile(path)
    index_file.create(b"payload")

    assert path.exists()
    assert index_file.read() == b"payload"


def test_binary_payload_is_preserved(tmp_path):
    path = tmp_path / "students.jidx"

    payload = bytes(range(256))

    index_file = IndexFile(path)
    index_file.create(payload)

    assert index_file.read() == payload