# JugaadDB

## Phase 4 Technical Thesis

### Physical Storage Integration, Buffer Management and Persistent Index Integration

---

## 1. Abstract

JugaadDB is a custom database management system implemented from scratch in Python. The project aims to demonstrate the internal architecture and engineering principles behind modern database systems without depending on an external database engine for its core storage functionality.

Earlier development phases established the logical database layer, SQL processing pipeline, indexing system and query optimization mechanisms. Phase 4 focuses on connecting these logical components to a persistent physical storage layer.

The major objective of Phase 4 is to transform logical table operations into physically stored database records. This phase introduces physical tables, record management, slotted pages, stable physical Record IDs, buffer pools, dirty-page management, physical persistence and SQL-index integration.

At the completion of Phase 4, the complete JugaadDB test suite contains **594 passing tests**.

---

## 2. Phase 4 Objectives

The main objectives of Phase 4 were:

1. Introduce physical table storage.
2. Store records in binary database pages.
3. Implement slotted-page record organization.
4. Introduce stable physical Record IDs.
5. Integrate RecordManager with physical tables.
6. Implement a database buffer pool.
7. Support dirty-page tracking and flushing.
8. Integrate physical storage with the catalog.
9. Preserve data across database reopen.
10. Integrate persistent B+Tree indexes with physical records.
11. Maintain indexes during INSERT, UPDATE and DELETE.
12. Validate the complete storage architecture through regression testing.

---

## 3. Existing Architecture Before Phase 4

Before Phase 4, JugaadDB already contained:

* database creation
* schema management
* logical tables
* CRUD operations
* SQL lexer
* SQL parser
* AST
* planner
* executor
* query optimization
* memory indexes
* B+Tree indexes
* persistent index structures

However, the logical table layer was not yet fully connected to a physical record storage system.

Phase 4 was therefore designed as the bridge between the logical database engine and the storage subsystem.

---

## 4. Phase 4 Architecture

The resulting architecture is:

```text
                         JUGAADDB
                            |
        +-------------------+-------------------+
        |                   |                   |
    SQL ENGINE          DATABASE CORE       INDEXING
        |                   |                   |
    Lexer                Catalog            B+Tree
    Parser               Schema             Persistence
    AST                  Tables
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

This architecture establishes a clear separation between query processing, logical data management, physical storage and indexing.

---

## 5. Physical Storage Design

JugaadDB uses fixed-size physical pages.

The current page size is:

```text
4096 bytes
```

The physical storage file contains a database header followed by data pages.

The FileManager is responsible for:

* creating storage files
* opening existing files
* validating file headers
* tracking page counts
* allocating pages
* reading pages
* writing pages

The FileManager provides the lowest-level page-oriented storage abstraction.

---

## 6. Page Abstraction

A physical page represents a fixed-size block of database storage.

The page abstraction provides:

* page identification
* binary payload access
* fixed-size validation

The page layer allows higher-level storage components to work with physical pages without directly manipulating database files.

---

## 7. Slotted Page Architecture

The slotted page is the main physical record organization mechanism introduced in Phase 4.

Conceptually:

```text
+---------------------------+
| Page Header               |
+---------------------------+
| Record Data               |
| Record Data               |
| Record Data               |
|                           |
|       Free Space          |
|                           |
+---------------------------+
| Slot Directory            |
+---------------------------+
```

The slot directory stores metadata required to locate records inside the page.

Each slot identifies a record using information such as:

* record offset
* record length
* deletion state

The design allows variable-length records to be stored inside fixed-size pages.

---

## 8. Record IDs

A physical record is identified by:

```text
(page_id, slot_id)
```

For example:

```text
(4, 2)
```

means that the record is located in page 4 at slot 2.

This physical identity is important because indexes need stable references to physical records.

The Record ID system also allows the database to connect:

```text
Index Entry
     ↓
Record ID
     ↓
Physical Record
```

Record IDs remain stable across database reopen operations.

---

## 9. Record Serialization

Logical rows cannot be written directly as Python dictionaries into physical pages.

JugaadDB therefore uses custom binary record serialization.

The supported field types are:

```text
INTEGER
FLOAT
TEXT
BOOLEAN
NULL
```

The serialization pipeline is:

```text
Python Row
    ↓
RecordCodec
    ↓
Binary Record
    ↓
SlottedPage
    ↓
Physical Page
```

Reading reverses this process:

```text
Physical Page
    ↓
SlottedPage
    ↓
Binary Record
    ↓
RecordCodec
    ↓
Python Row
```

This separates logical schema representation from physical storage representation.

---

## 10. RecordManager

RecordManager provides the physical record-level interface.

Its major responsibilities include:

* inserting records
* reading records
* updating records
* deleting records
* restoring deleted records
* scanning physical records
* counting physical records
* generating and validating Record IDs

The main operations are conceptually:

```text
insert(row)
read(record_id)
update(record_id, row)
delete(record_id)
restore(record_id, row)
scan()
count()
```

RecordManager therefore acts as the primary interface between tables and physical pages.

---

## 11. PhysicalTable

The PhysicalTable abstraction connects schema information with RecordManager.

Its responsibility is to expose physical storage operations to the relational table layer while preserving the logical schema.

The architecture becomes:

```text
Logical Table
      ↓
PhysicalTable
      ↓
RecordManager
      ↓
SlottedPage
      ↓
FileManager
```

This separation prevents SQL and relational logic from directly manipulating physical page structures.

---

## 12. Buffer Pool

A buffer pool was introduced to reduce repeated physical page access.

The buffer pool acts as an in-memory cache:

```text
RecordManager
      ↓
BufferPool
      ↓
FileManager
      ↓
Disk
```

Instead of reading the same page from disk repeatedly, frequently accessed pages can remain in memory.

---

## 13. Buffer Pool Features

The implemented BufferPool supports:

* configurable capacity
* page fetch
* new page allocation
* cache hits
* cache misses
* hit-rate calculation
* page storage
* dirty-page tracking
* clean-page tracking
* page flushing
* dirty-page flushing
* complete buffer flushing
* page eviction
* pinning
* unpinning
* pinned-page protection
* clean-page clearing

Statistics include:

```text
size
hits
misses
hit_rate
dirty_count
dirty_page_ids
pinned_page_ids
```

---

## 14. Dirty Page Management

When a page is modified in memory, it becomes dirty.

The buffer pool tracks this state so that modified data is eventually persisted.

The lifecycle is:

```text
Read Page
   ↓
Buffer Pool
   ↓
Modify
   ↓
Dirty
   ↓
Flush
   ↓
Disk
   ↓
Clean
```

The implementation also protects dirty state when a physical write fails.

This prevents a failed write from incorrectly marking modified data as clean.

---

## 15. Page Eviction

Because the buffer pool has finite capacity, pages must eventually be removed.

JugaadDB uses an LRU-style ordering mechanism to identify candidate pages.

A pinned page cannot be evicted.

Therefore:

```text
Page
 |
 +-- Clean + Unpinned → Evictable
 |
 +-- Dirty + Unpinned → Flush + Evictable
 |
 +-- Pinned → Protected
```

If every page is pinned, eviction fails instead of silently removing a page that is still in use.

---

## 16. Catalog Integration

Physical storage metadata was integrated into the database catalog.

A table now contains information describing its physical representation.

Conceptually:

```text
Table Metadata
 |
 +-- Schema
 |
 +-- Logical Metadata
 |
 +-- Physical Path
 |
 +-- Physical Format
```

The physical format is currently identified as:

```text
slotted-page
```

This allows the database to reconstruct physical table connections after reopening.

---

## 17. Database Lifecycle

The Database object now manages:

* physical tables
* buffer pools
* catalog
* index manager

During database opening:

```text
Database.open()
      ↓
StorageEngine.load()
      ↓
Catalog reconstruction
      ↓
PhysicalTable reconstruction
      ↓
BufferPool creation
      ↓
Persistent index loading
```

During closing:

```text
Database.close()
      ↓
Flush Buffer Pools
      ↓
Persist Indexes
      ↓
Close Physical Tables
```

This provides a controlled lifecycle for database resources.

---

## 18. Persistence Across Reopen

One of the most important Phase 4 requirements is that physical data must survive database shutdown and reopen.

The validation process is:

```text
Create Database
      ↓
Create Table
      ↓
Insert Records
      ↓
Update / Delete
      ↓
Flush
      ↓
Close
      ↓
Open
      ↓
Read Physical Records
```

The resulting records and Record IDs remain available after reopening.

---

## 19. Multiple Physical Pages

A table is not limited to a single page.

When a page does not have enough free space for a new record, RecordManager allocates another physical page.

Conceptually:

```text
Table
 |
 +-- Page 1
 |    +-- Records
 |
 +-- Page 2
 |    +-- Records
 |
 +-- Page 3
 |    +-- Records
 |
 +-- ...
```

This allows tables to grow beyond the capacity of a single page.

---

## 20. Index Integration

Earlier phases introduced custom B+Tree indexing.

Phase 4 connects indexes with physical Record IDs.

The relationship is:

```text
Indexed Value
      ↓
B+Tree
      ↓
Record ID
      ↓
Physical Record
```

For example:

```text
id = 25
   ↓
B+Tree
   ↓
(page_id, slot_id)
   ↓
Physical Record
```

This allows indexed queries to locate physical records directly.

---

## 21. Persistent B+Tree Indexes

B+Tree indexes are persisted independently using a custom binary format.

The persistence representation contains:

```text
Header
Metadata
B+Tree Structure
```

The implementation does not use Python pickle.

When the database is reopened:

```text
Index File
    ↓
BTreePersistence
    ↓
B+Tree Reconstruction
    ↓
IndexManager
```

The restored index is then available to the query planner.

---

## 22. Index Maintenance

Physical storage integration required indexes to remain synchronized with table modifications.

For INSERT:

```text
INSERT
  ↓
Physical Record
  ↓
Record ID
  ↓
Index Entry
```

For UPDATE:

```text
UPDATE
  ↓
Remove old indexed value
  ↓
Write updated record
  ↓
Insert new indexed value
```

For DELETE:

```text
DELETE
  ↓
Remove index reference
  ↓
Delete physical record
```

This keeps the index consistent with the physical table.

---

## 23. SQL + Physical Storage Integration

The SQL engine now reaches the physical storage layer.

The complete execution path is:

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
Disk
```

This is a major architectural milestone because SQL operations now correspond to real persistent physical records.

---

## 24. SQL + Index Integration

For an indexed query:

```sql
SELECT * FROM students WHERE id = 25;
```

the execution can conceptually become:

```text
SQL
 ↓
Parser
 ↓
Planner
 ↓
Detect indexed predicate
 ↓
B+Tree lookup
 ↓
Record ID
 ↓
Physical record lookup
 ↓
Condition recheck
 ↓
Query Result
```

This avoids scanning every physical record when an appropriate index is available.

---

## 25. Query Optimization

The Phase 3 optimizer was extended to work with the physical storage architecture.

The optimizer supports:

* equality predicate extraction
* AND predicate index selection
* deterministic index scoring
* index scan selection
* full condition rechecking

Unsupported OR cases are deliberately not optimized using a single index unless correctness can be guaranteed.

Correctness is prioritized over aggressive optimization.

---

## 26. Performance Validation

A benchmark using 1000 rows produced the following results:

```text
Table Scan Average:
2.728 ms

B+Tree Average:
0.596 ms
```

Observed improvement:

```text
4.58x speedup
78.14% improvement
```

This demonstrates the practical benefit of the custom indexing subsystem.

---

## 27. Regression Testing

Phase 4 introduced extensive regression coverage.

The complete test suite currently reports:

```text
594 passed
```

The tests cover:

* physical insertion
* physical selection
* physical updates
* physical deletes
* Record IDs
* multi-page storage
* buffer pool behavior
* dirty pages
* page eviction
* page pinning
* catalog integration
* database reopen
* SQL physical integration
* B+Tree persistence
* indexed queries
* index maintenance
* storage consistency

A dedicated Phase 4 full regression suite validates complete end-to-end behavior.

---

## 28. Phase 4 Sub-Phases

Phase 4 was divided into:

```text
4.1 Physical Table Storage Foundation
4.2 RecordManager-backed INSERT
4.3 RecordManager-backed SELECT
4.4 Physical UPDATE
4.5 Physical DELETE
4.6 Table / Schema Catalog Integration
4.7 Buffer Pool
4.8 Buffer Pool Hardening
4.9 Physical Record ID Integration
4.10 Storage Persistence and Reopen
4.11 SQL + Index Integration
4.12 Full Storage Regression
```

All Phase 4 milestones are complete.

---

## 29. Final Phase 4 Architecture

The final Phase 4 data path is:

```text
                         SQL
                          |
                          v
                    SQL Executor
                          |
                          v
                       Table
                          |
                          v
                   PhysicalTable
                          |
                          v
                     BufferPool
                          |
                          v
                    RecordManager
                          |
                          v
                     SlottedPage
                          |
                          v
                      FileManager
                          |
                          v
                        Disk
```

Index-assisted queries additionally use:

```text
                    Query Planner
                         |
                         v
                      B+Tree
                         |
                         v
                      RecordID
                         |
                         v
                   Physical Record
```

---

## 30. Engineering Significance

Phase 4 represents the transition of JugaadDB from primarily logical database functionality toward a storage-engine architecture.

The project now demonstrates concepts found in real database systems:

* page-oriented storage
* variable-length records
* slot directories
* physical record identifiers
* buffer management
* dirty pages
* page eviction
* persistent storage
* index persistence
* index maintenance
* logical-to-physical query execution

The architecture also provides the foundation required for future transaction and recovery mechanisms.

---

## 31. Limitations

Although Phase 4 provides a functional physical storage foundation, several advanced database capabilities remain future work.

These include:

* transaction isolation
* Write-Ahead Logging
* crash recovery
* concurrent transaction handling
* locking
* MVCC
* advanced buffer replacement policies
* cost-based query optimization
* unified single-file physical allocation
* advanced storage compaction

These are intentionally reserved for later phases.

---

## 32. Phase 5 Preparation

The physical storage architecture established in Phase 4 provides the foundation for transaction processing.

The next phase will introduce:

```text
Transaction Manager
        ↓
Transaction IDs
        ↓
BEGIN
        ↓
Operations
        ↓
COMMIT / ROLLBACK
        ↓
Write-Ahead Log
        ↓
Recovery
```

The goal of Phase 5 is to ensure that database operations become atomic and recoverable.

---

## 33. Phase 4 Conclusion

Phase 4 successfully integrated JugaadDB's logical database layer with a custom physical storage engine.

The system now supports persistent physical records, stable Record IDs, page-oriented storage, buffer management, persistent indexes and SQL operations over physical data.

The complete regression suite contains:

```text
594 passing tests
```

Therefore:

```text
PHASE 4 — COMPLETE
```

The project is now ready to proceed to transaction processing and recovery.

---

## 34. Project Status

```text
Phase 1        COMPLETE
Phase 1.5      COMPLETE
Phase 2        COMPLETE
Phase 3        COMPLETE
Phase 4        COMPLETE

Tests          594 PASSED

Next:
Phase 5 - Transactions, WAL and Recovery
```
