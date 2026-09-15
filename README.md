# JugaadDB

## A Database Management System Built from Scratch in Python

JugaadDB is a custom database management system built from scratch in Python. It is designed to demonstrate how a real database engine works internally, including SQL processing, physical storage, buffer management, indexing, persistence, and query optimization.

The project does not use SQLite, PostgreSQL, MySQL, MongoDB, or any other database engine as its core storage system.

> One Engine. Multiple Data Models. Zero Required Infrastructure.

## Project Status

Current milestone:

**Phase 4 - Physical Storage Integration: COMPLETE**

Test status:

```text
594 passed
```

The complete existing test suite passes successfully.

## Core Architecture

```text
                         JUGAADDB
                            |
        +-------------------+-------------------+
        |                   |                   |
    SQL ENGINE          DATABASE CORE       INDEXING
        |                   |                   |
    Lexer                Catalog            B+Tree
    Parser               Schema             Memory Index
    AST                  Tables             Persistence
    Planner
    Executor
        |
        v
      TABLE
        |
        v
  PHYSICAL TABLE
        |
        v
   BUFFER POOL
        |
        v
 RECORD MANAGER
        |
        v
  SLOTTED PAGE
        |
        v
  FILE MANAGER
        |
        v
 PHYSICAL STORAGE
```

## Major Components

### SQL Engine

JugaadDB contains its own SQL processing pipeline:

```text
SQL Query
   ↓
Lexer
   ↓
Parser
   ↓
AST
   ↓
Planner
   ↓
Optimizer
   ↓
Executor
   ↓
Result
```

Supported functionality includes:

* CREATE TABLE
* INSERT
* SELECT
* UPDATE
* DELETE
* WHERE conditions
* AND / OR conditions
* comparison operators
* projections
* filtering
* CREATE INDEX
* indexed queries

## Database Core

The database core manages:

* databases
* tables
* schemas
* columns
* data types
* primary keys
* nullable constraints
* unique constraints
* catalog metadata
* table lifecycle

Current supported primitive types:

```text
INTEGER
FLOAT
TEXT
BOOLEAN
```

## Physical Storage Engine

JugaadDB implements physical record storage instead of delegating storage to another database.

The storage architecture contains:

```text
FileManager
    ↓
Page
    ↓
SlottedPage
    ↓
RecordManager
    ↓
PhysicalTable
```

### Pages

The storage engine uses fixed-size pages.

```text
PAGE_SIZE = 4096 bytes
```

The database file contains a header page followed by physical data pages.

### Slotted Pages

Records are stored using a slotted-page structure.

A page maintains:

* page metadata
* slot directory
* record offsets
* record lengths
* deleted-slot information
* free-space tracking

This allows records to be addressed using stable physical identifiers.

## Record IDs

Physical records use:

```text
(page_id, slot_id)
```

Example:

```text
(3, 7)
```

This identifies a record physically inside the database storage layer.

Record IDs remain stable across database reopen operations.

## Record Serialization

JugaadDB contains custom binary record serialization.

Supported field encoding:

```text
NULL
INTEGER
FLOAT
TEXT
BOOLEAN
```

The system converts logical rows into binary records and reconstructs rows from the physical representation.

## Buffer Pool

JugaadDB implements an in-memory buffer pool between the database engine and physical storage.

```text
Query
  ↓
RecordManager
  ↓
BufferPool
  ↓
FileManager
  ↓
Disk
```

The buffer pool provides:

* page caching
* cache hits
* cache misses
* LRU-style page management
* dirty page tracking
* page flushing
* partial dirty-page flushing
* page eviction
* pin/unpin support
* capacity management
* clean-page removal
* write failure protection

Example statistics:

```text
size
hits
misses
hit_rate
dirty_count
dirty_page_ids
pinned_page_ids
```

## Persistence

JugaadDB persists:

* database metadata
* schemas
* physical records
* Record IDs
* indexes
* B+Tree structures

The database can be closed and reopened while preserving its stored state.

## Indexing

JugaadDB supports custom indexes.

Current index architecture:

```text
IndexManager
     |
     +---- MemoryIndex
     |
     +---- BPlusTreeIndex
                  |
             Persistence
```

## B+Tree

JugaadDB implements a custom B+Tree index with:

* configurable order
* leaf nodes
* internal nodes
* duplicate keys
* RecordID lists
* node splitting
* root splitting
* leaf chaining
* range scanning
* deletion
* borrowing
* merging
* root shrinking
* structural validation

The B+Tree is implemented without relying on a database library.

## Persistent Indexes

B+Tree indexes can be persisted using a custom binary persistence format.

The persistence layer stores:

```text
Index Metadata
+
B+Tree Structure
```

No Python pickle-based persistence is used.

Persistent indexes are automatically restored when the database is reopened.

## Index Maintenance

Indexes remain synchronized with physical records during:

```text
INSERT
UPDATE
DELETE
```

The SQL engine can use available indexes when planning suitable queries.

## Query Optimization

JugaadDB includes basic query optimization.

The optimizer can:

* detect equality predicates
* detect indexable AND predicates
* select suitable indexes
* score candidate indexes deterministically
* choose index scans where appropriate
* perform full condition rechecks

The optimizer intentionally avoids unsafe single-index assumptions for unsupported OR conditions.

## Performance

A benchmark over 1000 rows demonstrated the benefit of the custom B+Tree index.

```text
Table Scan:
2.728 ms average

B+Tree:
0.596 ms average
```

Observed result:

```text
~4.58x faster
~78.14% improvement
```

The benchmark demonstrates that the indexing layer can significantly reduce lookup time compared with a complete table scan.

## Physical Storage Integration

Phase 4 connected the logical database layer with the physical storage engine.

The current flow is:

```text
SQL
 ↓
Planner
 ↓
Executor
 ↓
Table
 ↓
PhysicalTable
 ↓
BufferPool
 ↓
RecordManager
 ↓
SlottedPage
 ↓
FileManager
 ↓
Physical File
```

This means SQL operations are no longer only logical in-memory operations. They are connected to persistent physical records.

## Current Phase Roadmap

### Phase 1 - Persistence Foundation

* database creation
* database opening
* schema
* tables
* logical rows
* CRUD
* basic persistence

Status:

```text
COMPLETE
```

### Phase 1.5 - Physical Record Foundation

* pages
* file manager
* record serializer
* record codec
* slotted pages
* record manager

Status:

```text
COMPLETE
```

### Phase 2 - SQL Engine

* lexer
* parser
* AST
* planner
* executor
* SQL semantics
* SQL integration

Status:

```text
COMPLETE
```

### Phase 3 - Indexing and Optimization

* index abstraction
* memory indexes
* B+Tree
* B+Tree deletion
* persistent indexes
* CREATE INDEX
* automatic index maintenance
* index scans
* stable Record IDs
* planner optimization
* benchmarking
* smarter query optimization

Status:

```text
COMPLETE
```

### Phase 4 - Physical Storage Integration

* physical table foundation
* physical INSERT
* physical SELECT
* physical UPDATE
* physical DELETE
* catalog integration
* buffer pool
* dirty page management
* buffer pool hardening
* physical RecordID integration
* storage persistence and reopen
* SQL + index integration
* complete physical storage regression

Status:

```text
COMPLETE

594 tests passed
```

### Phase 5 - Transactions and Recovery

Planned components:

```text
Transaction Manager
       ↓
Transaction IDs
       ↓
BEGIN / COMMIT / ROLLBACK
       ↓
Write-Ahead Log
       ↓
Undo / Recovery
       ↓
Crash Recovery
```

Planned milestones:

```text
5.1 Transaction Foundation
5.2 Transaction IDs and States
5.3 BEGIN / COMMIT / ROLLBACK
5.4 WAL Foundation
5.5 WAL Record Format
5.6 WAL Persistence
5.7 Physical Change Logging
5.8 Undo / Rollback
5.9 Crash Recovery
5.10 Recovery on Database Reopen
5.11 Transaction + Index Consistency
5.12 Full Transaction Regression
```

### Future Phases

```text
Phase 6  - NoSQL Document / Key-Value Engine
Phase 7  - Security and RBAC
Phase 8  - API / CLI / GUI
Phase 9  - Benchmarking and Documentation
Phase 10 - Deployment and Demonstration
```

## Project Goals

The long-term goal of JugaadDB is to evolve from a student database project into a complete educational database engine demonstrating:

* database architecture
* SQL processing
* storage management
* indexing
* query optimization
* transactions
* recovery
* NoSQL concepts
* security
* APIs
* performance engineering

## Technology Stack

```text
Language        Python
Testing         pytest
Storage         Custom binary page storage
Query Language  Custom SQL engine
Indexing        Custom B+Tree
Caching         Custom Buffer Pool
Serialization   Custom binary serialization
Version Control Git
```

## Design Principles

JugaadDB follows these principles:

1. Build core database mechanisms from scratch.
2. Avoid external database engines as storage backends.
3. Keep the storage layer independent from the SQL layer.
4. Maintain stable physical Record IDs.
5. Persist important database state.
6. Validate internal structures aggressively.
7. Add every major feature with regression tests.
8. Preserve backward compatibility as the engine evolves.
9. Prefer deterministic behavior.
10. Keep the architecture extensible for future SQL and NoSQL functionality.

## Testing

Run the complete test suite:

```bash
python -m pytest -q
```

Current result:

```text
594 passed
```

Run storage regression tests:

```bash
python -m pytest tests/storage/test_phase4_full_regression.py -q
```

## Project Structure

```text
JugaadDB/
├── jugaaddb/
│   ├── core/
│   ├── indexing/
│   ├── relational/
│   ├── sql/
│   └── storage/
│       ├── buffer_pool.py
│       ├── constants.py
│       ├── engine.py
│       ├── file_manager.py
│       ├── page.py
│       ├── physical_table.py
│       ├── record.py
│       ├── record_codec.py
│       ├── record_manager.py
│       └── slotted_page.py
│
├── tests/
│   ├── indexing/
│   ├── sql/
│   └── storage/
│
├── docs/
│   └── THESIS_PHASE_3.md
│
└── README.md
```

## Author

Built as a ground-up database engineering project in Python.

**JugaadDB**

> From SQL statements to physical pages — built from scratch.
