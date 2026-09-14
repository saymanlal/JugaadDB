from jugaaddb.sql.result import CommandResult, QueryResult


def test_query_result_metadata():
    result = QueryResult(
        columns=("name", "cgpa"),
        rows=(
            {"name": "Sayman", "cgpa": 8.5},
            {"name": "Rahul", "cgpa": 9.1},
        ),
    )

    assert result.columns == ("name", "cgpa")
    assert result.row_count == 2
    assert len(result) == 2
    assert result[0]["name"] == "Sayman"
    assert result.query_type == "SELECT"


def test_query_result_to_list():
    result = QueryResult(
        columns=("id",),
        rows=(
            {"id": 1},
            {"id": 2},
        ),
    )

    assert result.to_list() == [
        {"id": 1},
        {"id": 2},
    ]


def test_query_result_backwards_compatible_with_list():
    result = QueryResult(
        columns=("id",),
        rows=(
            {"id": 1},
        ),
    )

    assert result == [{"id": 1}]


def test_command_result_metadata():
    result = CommandResult(
        affected_rows=3,
        query_type="UPDATE",
    )

    assert result.affected_rows == 3
    assert result.query_type == "UPDATE"
    assert int(result) == 3


def test_command_result_backwards_compatible_with_int():
    result = CommandResult(
        affected_rows=2,
        query_type="DELETE",
    )

    assert result == 2
    assert bool(result)


def test_zero_command_result_is_false():
    result = CommandResult(
        affected_rows=0,
        query_type="DELETE",
    )

    assert not result