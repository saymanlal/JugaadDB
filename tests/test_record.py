import pytest

from jugaaddb.storage.record import RecordSerializer


def test_empty_record():
    data = RecordSerializer.serialize([])

    assert RecordSerializer.deserialize(data) == []


def test_integer():
    data = RecordSerializer.serialize([42])

    assert RecordSerializer.deserialize(data) == [42]


def test_negative_integer():
    data = RecordSerializer.serialize([-999])

    assert RecordSerializer.deserialize(data) == [-999]


def test_float():
    data = RecordSerializer.serialize([3.14159])

    result = RecordSerializer.deserialize(data)

    assert result[0] == pytest.approx(3.14159)


def test_text():
    data = RecordSerializer.serialize(["Ayush"])

    assert RecordSerializer.deserialize(data) == ["Ayush"]


def test_unicode_text():
    data = RecordSerializer.serialize(
        ["JugaadDB 🚀"]
    )

    assert RecordSerializer.deserialize(data) == [
        "JugaadDB 🚀"
    ]


def test_boolean():
    data = RecordSerializer.serialize(
        [True, False]
    )

    assert RecordSerializer.deserialize(data) == [
        True,
        False
    ]


def test_null():
    data = RecordSerializer.serialize([None])

    assert RecordSerializer.deserialize(data) == [None]


def test_mixed_values():
    values = [
        42,
        3.14,
        "Ayush",
        True,
        None,
        False
    ]

    data = RecordSerializer.serialize(values)

    assert RecordSerializer.deserialize(data) == values


def test_multiple_text_values():
    values = [
        "hello",
        "world",
        "",
        "JugaadDB"
    ]

    data = RecordSerializer.serialize(values)

    assert RecordSerializer.deserialize(data) == values


def test_unsupported_type_rejected():
    with pytest.raises(TypeError):
        RecordSerializer.serialize([
            {"name": "Ayush"}
        ])


def test_corrupted_record_header_rejected():
    with pytest.raises(ValueError):
        RecordSerializer.deserialize(b"\x00")


def test_corrupted_field_header_rejected():
    data = b"\x00\x01"

    with pytest.raises(ValueError):
        RecordSerializer.deserialize(data)


def test_corrupted_field_payload_rejected():
    # One INTEGER field claims 8 bytes,
    # but only 2 bytes are present.
    data = (
        b"\x00\x01"
        b"\x01\x00\x00\x00\x08"
        b"\x00\x01"
    )

    with pytest.raises(ValueError):
        RecordSerializer.deserialize(data)


def test_invalid_boolean_rejected():
    data = (
        b"\x00\x01"
        b"\x04\x00\x00\x00\x01"
        b"\x02"
    )

    with pytest.raises(ValueError):
        RecordSerializer.deserialize(data)