import statistics
import time

from jugaaddb.core.database import Database
from jugaaddb.core.schema import Column


ROW_COUNT = 1000
LOOKUP_VALUE = ROW_COUNT - 1
RUNS = 10


def create_database(path):
    db = Database.create(path)

    db.create_table(
        "records",
        [
            Column(
                "id",
                "INTEGER",
                primary_key=True,
                nullable=False,
            ),
            Column(
                "name",
                "TEXT",
                nullable=False,
            ),
            Column(
                "score",
                "FLOAT",
                nullable=False,
            ),
        ],
    )

    return db


def populate(db):
    table = db.table("records")

    for index in range(ROW_COUNT):
        table.insert(
            {
                "id": index,
                "name": f"User-{index}",
                "score": float(index) / 10,
            }
        )


def measure(query_function):
    timings = []
    result = None

    for _ in range(RUNS):
        start = time.perf_counter()
        result = query_function()
        elapsed = time.perf_counter() - start
        timings.append(elapsed)

    return result, timings


def benchmark_without_index():
    db = create_database(
        "benchmark_table_scan.jdb"
    )

    populate(db)

    query = (
        f"SELECT * FROM records "
        f"WHERE id = {LOOKUP_VALUE};"
    )

    return measure(
        lambda: db.execute(query)
    )


def benchmark_with_index():
    db = create_database(
        "benchmark_index_scan.jdb"
    )

    populate(db)

    db.execute(
        "CREATE INDEX records_id_idx "
        "ON records (id);"
    )

    query = (
        f"SELECT * FROM records "
        f"WHERE id = {LOOKUP_VALUE};"
    )

    return measure(
        lambda: db.execute(query)
    )


def average_ms(timings):
    return statistics.mean(timings) * 1000


def minimum_ms(timings):
    return min(timings) * 1000


def maximum_ms(timings):
    return max(timings) * 1000


def print_result(
    title,
    result,
    timings,
):
    print()
    print(title)
    print("-" * len(title))
    print(f"Rows returned : {len(result.rows)}")
    print(f"Runs          : {RUNS}")
    print(
        f"Average       : "
        f"{average_ms(timings):.3f} ms"
    )
    print(
        f"Minimum       : "
        f"{minimum_ms(timings):.3f} ms"
    )
    print(
        f"Maximum       : "
        f"{maximum_ms(timings):.3f} ms"
    )


def main():
    print(
        "JugaadDB Query Performance Benchmark"
    )
    print(
        f"Dataset       : {ROW_COUNT} rows"
    )
    print(
        f"Lookup        : id = {LOOKUP_VALUE}"
    )

    table_result, table_timings = (
        benchmark_without_index()
    )

    print_result(
        "Table Scan",
        table_result,
        table_timings,
    )

    index_result, index_timings = (
        benchmark_with_index()
    )

    print_result(
        "B+Tree Index Scan",
        index_result,
        index_timings,
    )

    if table_result.rows != index_result.rows:
        raise RuntimeError(
            "Table scan and index scan returned "
            "different results."
        )

    table_average = average_ms(
        table_timings
    )

    index_average = average_ms(
        index_timings
    )

    if index_average > 0:
        speedup = (
            table_average /
            index_average
        )
    else:
        speedup = float("inf")

    if table_average > 0:
        improvement = (
            (
                table_average -
                index_average
            )
            / table_average
            * 100
        )
    else:
        improvement = 0

    print()
    print(
        "Performance Comparison"
    )
    print(
        "----------------------"
    )
    print(
        f"Table Scan      : "
        f"{table_average:.3f} ms"
    )
    print(
        f"B+Tree Index    : "
        f"{index_average:.3f} ms"
    )
    print(
        f"Speedup         : "
        f"{speedup:.2f}x"
    )
    print(
        f"Improvement     : "
        f"{improvement:.2f}%"
    )

    print()
    print(
        "Correctness     : PASS"
    )


if __name__ == "__main__":
    main()