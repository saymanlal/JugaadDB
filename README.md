# JugaadDB

## A Database Management System Built from Scratch in Python

**JugaadDB** is a custom database management system implemented from scratch in Python. The project focuses on understanding and implementing the internal components of a database engine instead of depending on an existing relational database system.

JugaadDB is designed around a modular architecture containing a storage layer, relational layer, SQL processing engine, indexing subsystem, and query optimization components.

> **One Engine. Multiple Data Models. Zero Required Infrastructure.**

---

## Project Status

**Current Phase:** Phase 3 — Indexing and Query Optimization

**Test Status:** 424 passed

**Language:** Python 3.12+

**Database File Format:** Custom `.jdb` format

**External Database Dependency:** None

**Required Infrastructure:** None

---

## Vision

The long-term goal of JugaadDB is to build a lightweight database engine that demonstrates how modern database systems work internally.

The project is intentionally implemented from the ground up rather than wrapping an existing database such as:

* SQLite
* MySQL
* PostgreSQL
* MongoDB

JugaadDB aims to provide its own implementations for important database concepts including:

* Database files
* Pages
* Records
* Schemas
* Tables
* SQL parsing
* Query planning
* Query execution
* Indexes
* B+Tree structures
* Index persistence
* Query optimization
* Transactions
* Write-ahead logging
* Recovery
* NoSQL-style document storage
* Key-value storage
* Authentication
* Authorization
* Audit logging

---

# Architecture

The current and planned architecture is:

```text
                         JUGAADDB
                            |
        +-------------------+-------------------+
        |                   |                   |
    SQL ENGINE        DATABASE CORE       INDEXING ENGINE
        |                   |                   |
    Lexer              Database             Index
    Parser             Schema               Manager
    AST                Table                B+Tree
    Planner            Relations            Index Scan
    Executor
        |
        +-------------------+
                            |
                     QUERY OPTIMIZER
                            |
              +-------------+-------------+
              |                           |
          Table Scan                  Index Scan
                                          |
                                      B+Tree
                                          |
                                   Stable Record IDs
                                          |
                                  Physical Storage
                                          |
                                    Record Manager
                                          |
                                     Slotted Pages
                                          |
                                     File Manager
                                          |
                                       .jdb File
```

---

# Repository Structure

```text
JugaadDB/
├── benchmarks/
│   └── index_performance.py
│
├── docs/
│
├── examples/
│
├── jugaaddb/
│   ├── core/
│   │   ├── database.py
│   │   └── schema.py
│   │
│   ├── relational/
│   │   └── table.py
│   │
│   ├── storage/
│   │   ├── constants.py
│   │   ├── file_manager.py
│   │   ├── page.py
│   │   ├── record_codec.py
│   │   ├── record_manager.py
│   │   ├── record_serializer.py
│   │   ├── slotted_page.py
│   │   └── storage_engine.py
│   │
│   ├── sql/
│   │   ├── ast.py
│   │   ├── errors.py
│   │   ├── executor.py
│   │   ├── lexer.py
│   │   ├── parser.py
│   │   ├── plan.py
│   │   ├── planner.py
│   │   ├── result.py
│   │   └── tokens.py
│   │
│   └── indexing/
│       ├── base.py
│       ├── btree.py
│       ├── index_file.py
│       ├── manager.py
│       ├── memory.py
│       ├── metadata.py
│       ├── persistence.py
│       ├── scan.py
│       ├── serializer.py
│       └── tree_serializer.py
│
├── tests/
│   ├── core/
│   ├── relational/
│   ├── storage/
│   ├── sql/
│   └── indexing/
│
├── .gitignore
├── LICENSE
├── README.md
├── pyproject.toml
└── requirements.txt
```

---

# Implemented Features

## Phase 1 — Persistence Foundation

JugaadDB started with a custom database abstraction capable of creating and opening database files.

Implemented:

* Database creation
* Database reopening
* Table creation
* Schema definition
* Column types
* Primary keys
* Nullable constraints
* Unique constraints
* Insert
* Select
* Update
* Delete
* Persistence validation

Supported types include:

```text
INTEGER
FLOAT
TEXT
BOOLEAN
```

---

# Phase 1.5 — Physical Record Foundation

The project introduced the initial physical storage primitives.

Implemented:

* Fixed-size database pages
* Database file headers
* Page allocation
* Binary page storage
* Binary record serialization
* Schema-aware record encoding
* Schema-aware record decoding
* Slotted pages
* Slot directories
* Record deletion
* Record manager
* Physical Record IDs

The slotted-page model follows the basic concept:

```text
+----------------------------------+
| Page Header                      |
+----------------------------------+
|                                  |
| Record Area                      |
|                                  |
|                                  |
+----------------------------------+
| Slot Directory                   |
+----------------------------------+
```

This establishes the foundation required for a future full physical-storage integration.

---

# Phase 2 — SQL Engine

JugaadDB gained a custom SQL processing pipeline.

```text
SQL
 |
Lexer
 |
Tokens
 |
Parser
 |
AST
 |
Planner
 |
Logical Plan
 |
Executor
 |
Result
```

Implemented components:

### Lexer

Converts SQL text into tokens.

### Parser

Converts tokens into an Abstract Syntax Tree.

### AST

Represents SQL statements using structured Python objects.

### Planner

Converts AST nodes into executable logical plans.

### Executor

Executes plans against the database.

Supported SQL capabilities include:

```sql
CREATE TABLE
CREATE INDEX
INSERT
SELECT
UPDATE
DELETE
WHERE
AND
OR
ORDER-related expression infrastructure
NULL
NOT NULL
PRIMARY KEY
UNIQUE
```

---

# Phase 3 — Indexing and Query Optimization

Phase 3 introduced the indexing subsystem and query optimization pipeline.

The main goal was to move JugaadDB beyond simple table scanning.

---

## Phase 3.1 — Index Foundation

A generic index abstraction was introduced.

The index interface supports:

```text
insert()
delete()
search()
scan()
```

Implemented index types include:

* Memory index
* B+Tree index

An `IndexManager` was introduced to manage indexes per table.

Conceptually:

```text
Database
   |
IndexManager
   |
   +---- students
          |
          +---- id_index
          +---- cgpa_index
```

---

# Phase 3.2 — B+Tree

JugaadDB implemented a B+Tree-style index from scratch.

The implementation supports:

* Leaf nodes
* Internal nodes
* Root nodes
* Key insertion
* Duplicate keys
* Record ID lists
* Leaf splitting
* Internal splitting
* Root splitting
* Leaf chaining
* Exact search
* Range search
* Structural validation

The leaf level is connected using:

```text
Leaf 1 → Leaf 2 → Leaf 3 → Leaf 4
```

This enables efficient ordered scans and range operations.

---

# B+Tree Deletion

B+Tree deletion was implemented with:

* Record removal
* Key removal
* Duplicate-value removal
* Underflow handling
* Borrowing from siblings
* Merging nodes
* Parent separator refresh
* Root shrinking
* Leaf-chain preservation
* Empty-root handling

The tree also contains validation logic capable of checking structural invariants.

---

# Phase 3.3 — Persistent Index

The B+Tree was extended with custom persistence support.

Implemented components include:

```text
IndexMetadata
IndexSerializer
IndexFile
BTreeSerializer
BTreePersistence
```

The persistence format avoids Python pickle and uses explicit serialization.

Persisted information includes:

* Index metadata
* Index name
* Table name
* Indexed column
* Index type
* B+Tree order
* Unique flag
* Tree nodes
* Keys
* Record IDs
* Leaf relationships

This provides the foundation for persistent index storage.

---

# Phase 3.4 — CREATE INDEX

JugaadDB added SQL support for:

```sql
CREATE INDEX index_name ON table_name (column_name);
```

Example:

```sql
CREATE INDEX students_id_idx
ON students (id);
```

When an index is created, existing table records are indexed.

The SQL pipeline becomes:

```text
CREATE INDEX
     |
Lexer
     |
Parser
     |
AST
     |
Planner
     |
CreateIndexPlan
     |
Executor
     |
IndexManager
     |
B+Tree
```

---

# Phase 3.5 — Automatic Index Maintenance

Indexes must remain synchronized with table modifications.

JugaadDB therefore introduced automatic index maintenance.

## INSERT

```text
INSERT row
   |
Table
   |
Store row
   |
Generate Record ID
   |
Update indexes
```

## UPDATE

When an indexed column changes:

```text
Old value
    |
Remove old index entry
    |
New value
    |
Insert new index entry
```

## DELETE

Deleting a row also removes its corresponding index entries.

Rollback logic was added around index modifications so that failed operations do not leave the table and indexes unnecessarily inconsistent.

---

# Phase 3.6 — Index Scan

The project introduced an `IndexScan` abstraction.

An index scan supports:

```text
exact()
range()
all()
```

This separates index traversal from query execution.

For example:

```text
WHERE id = 500
```

can become:

```text
Index
  |
Exact Search
  |
Record IDs
  |
Rows
```

instead of:

```text
Table
  |
Every Row
  |
Predicate Evaluation
```

---

# Phase 3.6.2 — SQL Index Scan

The SQL executor was integrated with index scans.

For an indexable equality condition:

```sql
SELECT *
FROM students
WHERE id = 500;
```

the planner can select an index.

The execution path becomes:

```text
SQL
 ↓
AST
 ↓
Planner
 ↓
IndexScan
 ↓
B+Tree
 ↓
Record IDs
 ↓
Rows
 ↓
Result
```

The executor still re-evaluates predicates against the retrieved rows.

This provides an important correctness property:

> An index is used to find candidate rows, but the SQL predicate remains the final authority.

---

# Phase 3.7.0 — Stable Record IDs

A correctness problem was identified in the initial indexing implementation.

Earlier logical record IDs were based on row positions:

```text
(page=1, row_index)
```

Deleting a row from the middle of a table could shift later rows and therefore invalidate index references.

This was replaced with stable logical Record IDs.

The new approach:

```text
Row
 |
Stable Record ID
 |
Index
```

Deleting one row no longer changes the IDs of remaining rows.

New rows receive a new ID rather than reusing an old deleted ID.

This is critical for reliable index maintenance.

---

# Phase 3.7.1 — Planner Optimization

The query planner was upgraded from a simple index/no-index decision to an optimizer-aware selection process.

The intended architecture became:

```text
SQL
 ↓
AST
 ↓
Logical Plan
 ↓
Optimizer
 ↓
TableScan / IndexScan
 ↓
Executor
```

The planner now examines available indexes before selecting the execution strategy.

For example:

```sql
SELECT *
FROM students
WHERE id = 101;
```

with an index on `id` can produce:

```text
Projection
   |
IndexScan
   |
students_id_idx
```

Without an appropriate index:

```text
Projection
   |
Filter
   |
TableScan
```

---

# Phase 3.7.2 — Performance Benchmark

A benchmark was created to compare table scanning with B+Tree index lookup.

The benchmark used:

```text
Rows: 1000
Repeated lookups: 10
```

Observed results:

| Metric  | Table Scan | B+Tree Index |
| ------- | ---------: | -----------: |
| Average |   2.728 ms |     0.596 ms |
| Minimum |   1.084 ms |     0.565 ms |
| Maximum |  17.168 ms |     0.754 ms |

Observed improvement:

```text
Speedup:     4.58x
Improvement: 78.14%
Correctness: PASS
```

These results demonstrate the benefit of indexed equality lookup within the current engine.

The benchmark should not be interpreted as a production database benchmark because the current table persistence layer is still transitional and Phase 4 will replace that path with deeper physical storage integration.

---

# Phase 3.8 — Smarter Query Optimization

The final Phase 3 improvement introduced smarter predicate analysis.

Previously the optimizer primarily considered simple conditions such as:

```sql
WHERE id = 500
```

The optimizer can now inspect equality predicates inside an `AND` expression.

Example:

```sql
SELECT *
FROM students
WHERE id = 500
AND cgpa = 9.1;
```

If an index exists on `id`, the planner can choose:

```text
IndexScan(id = 500)
```

and preserve the complete condition for final verification.

If only `cgpa` is indexed:

```text
IndexScan(cgpa = 9.1)
```

is selected.

The candidate rows are then rechecked against:

```text
id = 500 AND cgpa = 9.1
```

This prevents false matches.

---

# Predicate Optimization Rules

Current optimization behavior:

### Equality + indexed column

```sql
WHERE id = 10
```

Uses an index when available.

### AND + indexed predicate

```sql
WHERE id = 10 AND cgpa = 9.1
```

Uses an available indexable equality predicate.

### AND + multiple indexed predicates

The optimizer evaluates available candidates and chooses an index according to the current index scoring mechanism.

### AND without indexes

Falls back to:

```text
Filter
  |
TableScan
```

### OR

A single index is not incorrectly selected for the complete OR expression.

Example:

```sql
WHERE id = 10 OR cgpa = 9.1
```

currently falls back to a table scan.

This is intentional because OR optimization requires a more advanced multi-index execution strategy.

---

# Query Optimization Example

Given:

```sql
CREATE INDEX students_id_idx
ON students (id);
```

and:

```sql
SELECT *
FROM students
WHERE id = 2
AND cgpa = 9.1;
```

the plan can become:

```text
Projection
    |
IndexScan
    |
students_id_idx
    |
id = 2
    |
Candidate Record IDs
    |
Rows
    |
Full predicate verification
    |
Result
```

This combines:

* Index-based candidate retrieval
* Stable Record IDs
* Full predicate validation

---

# Testing

JugaadDB follows a test-driven incremental development approach.

At the completion of Phase 3:

```text
424 passed
```

The test suite covers multiple layers:

```text
Core
Relational
Storage
SQL
Indexing
Query Planning
Query Execution
Persistence
B+Tree Structure
Index Maintenance
Stable Record IDs
Query Optimization
```

Run the complete suite using:

```bash
python -m pytest -q
```

Expected Phase 3 status:

```text
424 passed
```

---

# Example Usage

```python
from jugaaddb.core.database import Database

db = Database.open("college.jdb")

db.execute("""
CREATE TABLE students (
    id INTEGER PRIMARY KEY NOT NULL,
    name TEXT NOT NULL,
    cgpa FLOAT NOT NULL
);
""")

db.execute("""
INSERT INTO students (id, name, cgpa)
VALUES (1, 'Sayman', 8.5);
""")

db.execute("""
CREATE INDEX students_id_idx
ON students (id);
""")

result = db.execute("""
SELECT *
FROM students
WHERE id = 1;
""")

print(result.rows)
```

---

# Current Design Principles

JugaadDB follows several important design principles.

## No Existing Database Engine

The project does not depend on SQLite, PostgreSQL, MySQL, MongoDB, or another database engine for its core functionality.

## Modular Architecture

Each subsystem has a separate responsibility.

```text
SQL
Storage
Indexing
Relational
Core
```

are designed as independent modules.

## Explicit Serialization

Important persistent structures use explicit binary serialization instead of Python pickle.

## Stable Identifiers

Indexes reference stable Record IDs rather than mutable row positions.

## Correctness Before Optimization

Indexes are used to retrieve candidates, but predicates can still be re-evaluated before producing final results.

## Incremental Engineering

The database is being built in stages rather than attempting all database features simultaneously.

---

# Current Limitations

Phase 3 is complete, but JugaadDB is not yet a production database.

Current limitations include:

* Table storage is still transitional.
* The physical RecordManager is not yet the primary SQL table-storage path.
* Full Buffer Pool integration is not yet complete.
* Persistent indexes are not yet fully integrated into database reopen/recovery.
* Transactions are not implemented yet.
* WAL is not implemented yet.
* Crash recovery is not implemented yet.
* Concurrent transactions are not implemented yet.
* Multi-index OR optimization is not implemented yet.
* Cost-based query optimization is not yet implemented.
* Full physical page lifecycle management is still planned.
* NoSQL storage is planned but not yet implemented.
* Security and RBAC are planned but not yet implemented.

These limitations are intentional milestones in the roadmap rather than hidden assumptions.

---

# Roadmap

## Phase 4 — Physical Storage Integration

Planned architecture:

```text
Table
 ↓
RecordManager
 ↓
SlottedPage
 ↓
Buffer/Page Cache
 ↓
FileManager
 ↓
.jdb
```

Goals:

* Replace transitional table persistence
* Integrate physical Record IDs
* Connect table operations to RecordManager
* Page-level reads/writes
* Buffer management
* Dirty-page tracking
* Page eviction
* Physical row reconstruction
* Storage-level persistence

---

## Phase 5 — Transactions and Recovery

Planned:

```text
Transaction Manager
WAL
Commit
Rollback
Recovery
```

---

## Phase 6 — NoSQL Engine

Planned support for:

```text
Document Model
Key-Value Model
```

---

## Phase 7 — Security

Planned:

```text
Authentication
RBAC
Permissions
Encryption
Audit Logging
```

---

## Phase 8 — API and Interfaces

Planned:

```text
CLI
REST API
GUI
```

---

## Phase 9 — Benchmarking and Documentation

Planned:

* Query benchmarks
* Storage benchmarks
* Index benchmarks
* Transaction benchmarks
* Comparison experiments
* Technical documentation
* Architecture diagrams

---

## Phase 10 — Cloud Demonstration

Optional deployment for demonstration purposes.

The core database remains designed to run locally without paid infrastructure.

---

# Educational Value

JugaadDB is intended as a practical database-engineering project.

It demonstrates concepts that are normally hidden behind database APIs:

```text
How pages work
How records are serialized
How schemas are validated
How SQL becomes an AST
How queries become plans
How indexes locate records
How B+Trees split and merge
How indexes remain synchronized
Why stable record IDs matter
How query planners choose execution strategies
How indexed queries can outperform table scans
```

Instead of only using:

```python
database.query(...)
```

the project investigates what happens internally before and after that call.

---

# Phase 3 Achievement

Phase 3 establishes a complete indexing and initial query-optimization subsystem.

The major achievement is the transition from:

```text
SQL
 ↓
Table Scan
```

to:

```text
SQL
 ↓
Parser
 ↓
Planner
 ↓
Optimizer
 ↓
Index Scan / Table Scan
 ↓
B+Tree / Table
 ↓
Stable Record IDs
 ↓
Result
```

with:

```text
424 tests passing
4.58x measured indexed lookup speedup
78.14% measured improvement
```

Phase 3 is therefore considered **complete and frozen**.

---

# License

This project is intended as an educational and engineering project.

See `LICENSE` for the applicable license.
