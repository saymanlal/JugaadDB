# JugaadDB

## Phase 3 — Indexing and Query Optimization

---

# Abstract

JugaadDB is a custom database management system developed from scratch in Python with the objective of studying and implementing the internal architecture of a database engine.

Phase 3 focuses on the implementation of indexing and query optimization. The phase introduces a generic indexing abstraction, an in-memory index, a B+Tree index, index persistence, SQL-level `CREATE INDEX` support, automatic index maintenance, index scans, stable record identifiers, planner-level index selection, performance benchmarking, and smarter predicate optimization.

The implementation transforms the query execution architecture from a basic table-scan model into an optimizer-aware execution pipeline capable of selecting between table scans and index scans.

At the completion of Phase 3, the project contains **424 passing automated tests**. A controlled benchmark using 1000 rows demonstrated an average lookup time of approximately **2.728 ms** for a table scan and **0.596 ms** for a B+Tree index lookup, representing approximately **4.58× speedup** and **78.14% improvement** for the tested workload.

Phase 3 establishes the indexing and query optimization foundation required for the next stage: physical storage integration.

---

# 1. Introduction

Traditional database applications expose high-level operations such as:

```sql
SELECT *
FROM students
WHERE id = 500;
```

The internal work required to execute such a query is hidden from the user.

A database system must determine:

* How data is stored
* How records are identified
* How records are located
* Whether an index exists
* Which execution strategy should be selected
* How index entries remain synchronized with table changes
* How query predicates are evaluated

JugaadDB is designed to expose and implement these concepts directly.

The project does not use an existing database engine as its storage or query-processing core. Instead, its architecture is implemented incrementally in Python.

Phase 3 specifically addresses the problem of efficient record lookup.

---

# 2. Problem Statement

A table scan evaluates a query predicate against every row.

For a table containing `N` records, an equality lookup such as:

```sql
WHERE id = 500
```

may require examining a large portion of the table.

This creates an unnecessary cost when only a small number of records satisfy the condition.

Indexes solve this problem by maintaining an additional searchable structure that maps values to records.

However, implementing an index introduces several engineering problems:

1. The index structure must support insertion.
2. The index structure must support deletion.
3. Duplicate values must be handled.
4. Tree structure must remain valid after splits and merges.
5. Table updates must keep indexes synchronized.
6. Index entries must point to stable records.
7. The query planner must know when an index can be used.
8. Candidate rows returned by an index must still respect the full SQL predicate.

Phase 3 addresses these problems.

---

# 3. Objectives

The main objectives of Phase 3 were:

* Build a reusable indexing abstraction.
* Implement an in-memory index.
* Implement a B+Tree index.
* Implement B+Tree insertion.
* Implement B+Tree deletion.
* Support duplicate index keys.
* Support exact searches.
* Support range searches.
* Validate B+Tree structural correctness.
* Persist index metadata and tree structures.
* Add SQL `CREATE INDEX`.
* Maintain indexes automatically during CRUD operations.
* Introduce stable Record IDs.
* Implement index scans.
* Integrate index scans with SQL execution.
* Allow the planner to choose an index.
* Optimize indexed equality predicates inside `AND`.
* Preserve full predicate correctness.
* Measure index lookup performance.

---

# 4. System Architecture

The Phase 3 architecture is:

```text
                         SQL QUERY
                             |
                             v
                          Lexer
                             |
                             v
                          Parser
                             |
                             v
                            AST
                             |
                             v
                          Planner
                             |
                             v
                       Query Optimizer
                         /         \
                        /           \
                       v             v
                 Table Scan      Index Scan
                      |              |
                      |            Index
                      |              |
                      |           B+Tree
                      |              |
                      |       Stable Record IDs
                      |              |
                      +-------> Candidate Rows
                                     |
                                     v
                              Predicate Check
                                     |
                                     v
                                   Result
```

The indexing subsystem itself is organized as:

```text
IndexManager
     |
     +------------------+
     |                  |
 MemoryIndex       BPlusTreeIndex
                        |
                  BTreeNode
                  /       \
             Internal     Leaf
                           |
                       Record IDs
```

---

# 5. Index Abstraction

A generic `Index` interface was introduced to decouple query execution from a specific indexing implementation.

The abstraction provides operations corresponding to:

```text
insert(key, record_id)
delete(key, record_id)
search(key)
scan()
```

The abstraction also represents an index entry as:

```text
(key, record_id)
```

This separation allows different index implementations to coexist behind a common interface.

---

# 6. Memory Index

The first implementation was a memory-based index.

Its conceptual representation is:

```text
Key
 |
 +---- Record ID
 +---- Record ID
 +---- Record ID
```

This structure supports duplicate values.

For example:

```text
cgpa = 9.1

    |
    +---- (1, 2)
    +---- (1, 5)
    +---- (1, 8)
```

This abstraction was useful for establishing index semantics before introducing the more complex B+Tree implementation.

---

# 7. B+Tree Implementation

The primary index structure developed in Phase 3 is a B+Tree-style index.

A simplified structure is:

```text
                    [50]
                   /    \
                  /      \
        [10,20,30]      [50,70,90]
           |                |
           v                v
        Leaf Node        Leaf Node
```

Leaf nodes maintain record references.

Leaf nodes are linked:

```text
Leaf A -> Leaf B -> Leaf C -> Leaf D
```

This linked structure enables ordered scans.

---

# 8. B+Tree Node Design

The tree contains two primary node categories.

## Internal Nodes

Internal nodes contain:

```text
keys
children
```

The keys act as separators between child subtrees.

## Leaf Nodes

Leaf nodes contain:

```text
keys
values
next_leaf
```

where each value may contain multiple Record IDs for duplicate keys.

---

# 9. B+Tree Insertion

Insertion follows the standard high-level B+Tree process:

```text
Search appropriate leaf
        |
Insert key
        |
Check capacity
        |
   +----+----+
   |         |
No split    Split
             |
       Promote separator
             |
        Parent update
             |
       Possible root split
```

The implementation supports:

* Leaf splitting
* Internal splitting
* Root splitting
* Duplicate keys
* Leaf-chain maintenance

---

# 10. B+Tree Deletion

Deletion was implemented to maintain tree correctness after records are removed.

The process is:

```text
Delete record ID
      |
Remove value
      |
Key still present?
   /          \
 yes           no
 |             |
Done       Remove key
              |
        Underflow check
              |
       +------+------+
       |             |
    Sufficient     Underflow
                      |
              Borrow or Merge
```

Underflow handling includes:

* Borrowing from siblings
* Merging nodes
* Updating parent separators
* Preserving leaf links
* Shrinking the root

---

# 11. Duplicate Keys

A database index cannot assume that every indexed value is unique.

For example:

```text
cgpa = 9.1
```

may occur in multiple records.

Therefore the B+Tree stores multiple Record IDs for the same key.

Conceptually:

```text
9.1
 |
 +---- Record A
 +---- Record B
 +---- Record C
```

Deletion removes an individual Record ID without necessarily removing the key itself.

The key is removed only when its final Record ID disappears.

---

# 12. B+Tree Validation

A dedicated validation mechanism was implemented to verify structural invariants.

Validation covers concepts including:

* Root correctness
* Node types
* Child relationships
* Key ordering
* Separator correctness
* Leaf depth
* Leaf-chain ordering
* Leaf-chain completeness
* Record ID consistency

This significantly improves reliability during development because complex split and merge operations can be tested independently.

---

# 13. Index Persistence

Phase 3 introduced custom persistent index structures.

The persistence subsystem includes:

```text
IndexMetadata
IndexSerializer
IndexFile
BTreeSerializer
BTreePersistence
```

Instead of relying on Python pickle, index structures are explicitly serialized.

This provides better control over the database file representation.

Persisted information includes:

* Table name
* Index name
* Indexed column
* Index type
* B+Tree order
* Uniqueness
* Tree structure
* Keys
* Record IDs
* Leaf relationships

---

# 14. CREATE INDEX

The SQL engine was extended with:

```sql
CREATE INDEX index_name
ON table_name (column_name);
```

Example:

```sql
CREATE INDEX students_id_idx
ON students (id);
```

The execution path is:

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

Existing records are indexed during index creation.

---

# 15. Automatic Index Maintenance

An index is useful only when it remains synchronized with its underlying table.

Phase 3 therefore integrates index maintenance with CRUD operations.

## Insert

```text
Insert Row
    |
Generate Stable Record ID
    |
Store Row
    |
Insert into every relevant index
```

## Update

For an indexed column:

```text
Old value
    |
Delete old index entry
    |
New value
    |
Insert new index entry
```

## Delete

```text
Delete Row
    |
Remove corresponding index entries
```

Rollback handling was added around these operations to reduce the possibility of leaving the table and index state inconsistent after an operation fails.

---

# 16. Stable Record IDs

A major correctness issue was discovered during index maintenance.

If an index points to a row using its list position:

```text
Row 0
Row 1
Row 2
Row 3
```

and Row 1 is deleted:

```text
Row 0
Row 2 -> becomes Row 1
Row 3 -> becomes Row 2
```

all later positions change.

An index pointing to the old positions can therefore become invalid.

Phase 3.7.0 solved this by introducing stable logical Record IDs.

Instead of:

```text
Record ID = row position
```

the model becomes:

```text
Record ID = stable identifier
```

Remaining rows retain their IDs even after another row is deleted.

New records receive new IDs rather than reusing deleted identifiers.

This provides a stable reference model for indexing.

---

# 17. Index Scan

An `IndexScan` abstraction was introduced to isolate index traversal.

Supported operations include:

```text
exact()
range()
all()
```

An exact lookup:

```sql
WHERE id = 500
```

can therefore execute approximately as:

```text
Index
 |
Search 500
 |
Record IDs
 |
Rows
```

rather than scanning every row.

---

# 18. SQL-Level Index Scan

The executor was modified to understand index-based plans.

The planner can produce:

```text
Projection
    |
IndexScan
```

instead of:

```text
Projection
    |
Filter
    |
TableScan
```

The executor resolves the index and retrieves candidate rows through the index.

---

# 19. Predicate Re-evaluation

An important correctness rule was introduced.

An index is used to locate candidate records, but the index lookup does not replace the SQL predicate.

For:

```sql
WHERE id = 2
AND cgpa = 9.1
```

an index on `cgpa` can find:

```text
All rows where cgpa = 9.1
```

But the executor must still verify:

```text
id = 2
AND
cgpa = 9.1
```

against each candidate row.

Therefore:

```text
Index
  |
Candidate Rows
  |
Full Predicate
  |
Final Result
```

This protects query correctness.

---

# 20. Planner Optimization

The planner was enhanced to examine indexes available for the referenced column.

The execution decision becomes:

```text
Condition
    |
Indexable?
  /       \
No        Yes
 |          |
Filter    Index
 |          |
Table     IndexScan
Scan
```

The planner therefore becomes aware of physical access strategies.

---

# 21. Smarter Predicate Optimization

Phase 3.8 introduced predicate extraction from logical `AND` expressions.

Example:

```sql
WHERE id = 500
AND cgpa = 9.1
```

The optimizer extracts:

```text
id = 500
cgpa = 9.1
```

and checks which predicates have supporting indexes.

If `id` is indexed:

```text
IndexScan(id = 500)
```

If only `cgpa` is indexed:

```text
IndexScan(cgpa = 9.1)
```

If neither is indexed:

```text
Filter(TableScan)
```

---

# 22. OR Predicate Handling

The optimizer deliberately does not transform a general OR condition into a single index scan.

Example:

```sql
WHERE id = 2
OR cgpa = 9.1
```

currently remains:

```text
Filter
   |
TableScan
```

This prevents an incorrect assumption that one index can represent the complete OR condition.

A future optimizer can introduce:

```text
IndexScan A
     |
   Union
     |
IndexScan B
```

but that is outside the current Phase 3 scope.

---

# 23. Index Selection

The planner currently evaluates available index candidates and assigns a score.

The current scoring strategy gives stronger preference to B+Tree indexes.

Conceptually:

```text
B+Tree  -> higher score
Other   -> lower score
```

The selected index is then converted into an `IndexScan` plan.

This is an initial optimizer rather than a complete cost-based optimizer.

---

# 24. Performance Evaluation

A benchmark was created to compare table scanning and indexed lookup.

Configuration:

```text
Records: 1000
Repeated lookups: 10
```

Results:

| Metric  | Table Scan | B+Tree Index |
| ------- | ---------: | -----------: |
| Average |   2.728 ms |     0.596 ms |
| Minimum |   1.084 ms |     0.565 ms |
| Maximum |  17.168 ms |     0.754 ms |

Calculated:

```text
Speedup = 4.58x
Improvement = 78.14%
```

Correctness verification:

```text
PASS
```

---

# 25. Performance Interpretation

The benchmark indicates that indexed lookup is substantially faster than scanning the complete table for the tested equality-query workload.

The important result is not only the measured speedup but the fact that the query engine can automatically choose a different physical execution strategy.

Without an index:

```text
Query
 |
TableScan
 |
Evaluate rows
```

With an index:

```text
Query
 |
IndexScan
 |
B+Tree
 |
Candidate Record IDs
 |
Rows
```

The benchmark demonstrates the practical effect of this architectural change.

However, the benchmark should be interpreted as an engineering demonstration rather than a production database benchmark because the table persistence layer is still transitional.

---

# 26. Testing Strategy

Phase 3 was developed incrementally with automated tests.

Testing covers:

```text
Index abstraction
Memory index
Index manager
B+Tree insertion
B+Tree deletion
Duplicate keys
Range search
Tree validation
Persistence
CREATE INDEX
Index maintenance
Index scans
SQL integration
Stable Record IDs
Planner optimization
Smart predicate optimization
Performance correctness
```

Final status:

```text
424 passed
```

The complete test suite is executed with:

```bash
python -m pytest -q
```

---

# 27. Engineering Challenges

Several important engineering problems were identified during Phase 3.

## Mutable Row Positions

Using row positions as index references caused invalid references after deletion.

Solution:

```text
Stable Record IDs
```

## B+Tree Underflow

Deletion can cause nodes to fall below their minimum occupancy.

Solution:

```text
Borrow
Merge
Parent Separator Refresh
Root Shrinking
```

## Duplicate Keys

Multiple rows may contain the same indexed value.

Solution:

```text
Key -> List[RecordID]
```

## Query Correctness

Using an index alone cannot guarantee that a compound predicate has been fully evaluated.

Solution:

```text
Index Candidate Retrieval
        +
Full Predicate Re-evaluation
```

## Optimizer Safety

Not every logical expression is safely transformable into a single index scan.

Solution:

```text
Equality predicates inside AND -> optimize
General OR -> table scan
```

---

# 28. Phase 3 Achievements

Phase 3 successfully established:

```text
Generic Index API
        +
Memory Index
        +
B+Tree
        +
B+Tree Deletion
        +
Index Persistence
        +
CREATE INDEX
        +
Automatic Maintenance
        +
Index Scan
        +
Stable Record IDs
        +
Planner Optimization
        +
Smart Predicate Optimization
        +
Benchmarking
```

Final automated test status:

```text
424 passed
```

Performance demonstration:

```text
4.58x speedup
78.14% improvement
```

---

# 29. Current Limitations

Phase 3 does not yet represent a production-ready database engine.

The following components remain future work:

* Full physical storage integration
* Buffer pool
* Complete page cache
* Persistent table records through RecordManager
* Persistent index reopening integration
* Transactions
* Write-ahead logging
* Crash recovery
* Concurrency control
* Cost-based optimization
* Multi-index OR execution
* NoSQL document engine
* Key-value engine
* Authentication
* RBAC
* Encryption
* Audit system
* API layer
* GUI

These limitations define the next stages of the project.

---

# 30. Phase 4 Direction

The next phase is Physical Storage Integration.

The intended architecture is:

```text
SQL Executor
      |
    Table
      |
 RecordManager
      |
 SlottedPage
      |
 Buffer/Page Cache
      |
 FileManager
      |
   .jdb file
```

The objective is to replace the transitional table persistence path with the physical storage structures already developed during Phase 1.5.

This will allow the higher layers of JugaadDB to operate on actual pages and records rather than primarily relying on the transitional representation.

---

# 31. Conclusion

Phase 3 represents a major architectural milestone for JugaadDB.

The project moved beyond basic SQL execution and introduced a complete initial indexing subsystem.

The implementation demonstrates how:

```text
Records
   |
Stable IDs
   |
Indexes
   |
B+Tree
   |
Query Planner
   |
Index Scan
```

can work together to improve database query execution.

The final Phase 3 implementation contains:

```text
424 passing tests
```

and a measured:

```text
4.58x indexed lookup speedup
78.14% improvement
```

for the benchmarked workload.

Most importantly, Phase 3 establishes the bridge between logical query processing and physical access-path selection.

The next architectural milestone is therefore Phase 4: integrating the existing physical storage components directly into the relational table layer.
