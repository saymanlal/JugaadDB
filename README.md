# JugaadDB

> **JugaadDB — A Database Management System Built from Scratch in Python**

JugaadDB is a custom database management system (DBMS) being built from the ground up in Python.

The goal is not to wrap an existing database such as MySQL, PostgreSQL, MongoDB, or SQLite. JugaadDB is designed to build its own database fundamentals step by step: storage, records, pages, schema, SQL processing, indexing, transactions, recovery, security, and multiple data models.

## Project Status

### Phase 1 — Completed

Phase 1 establishes the persistent relational database foundation.

**Current test status: 89/89 passed.**

Completed areas:

- Database creation and opening
- `.jdb` database file creation
- File header validation
- Page-based file storage
- Schema and column definitions
- Basic data types
- NULL handling
- Primary-key validation
- UNIQUE-column validation
- Table creation
- INSERT
- SELECT/read
- UPDATE
- DELETE
- Persistence across database reloads
- Binary record serialization
- Schema-aware record encoding/decoding
- Slotted-page record storage
- Record IDs
- Record insertion, reading, and deletion through `RecordManager`

Phase 1.5 is treated as the storage bridge inside the Phase 1 foundation. It replaces the idea of treating a row only as a high-level Python dictionary with a physical record representation that can live inside a page.

---

## Why JugaadDB?

Most beginner DBMS projects stop at:

```text
Python + SQLite/MySQL
        ↓
CRUD interface
        ↓
"Database project"
```

JugaadDB takes a different approach:

```text
SQL
 ↓
Query processing
 ↓
Database engine
 ↓
Record management
 ↓
Slotted pages
 ↓
Physical pages
 ↓
File manager
 ↓
.jdb file
```

The project is intended to demonstrate what happens underneath a database rather than only demonstrating how to call one.

---

## Current Architecture

```text
JUGAADDB
│
├── core
│   ├── schema.py
│   └── database.py
│
├── relational
│   └── table.py
│
└── storage
    ├── constants.py
    ├── page.py
    ├── file_manager.py
    ├── engine.py
    ├── record.py
    ├── record_codec.py
    ├── slotted_page.py
    └── record_manager.py
```

### Layered view

```text
Database
   │
   ▼
Table
   │
   ▼
RecordManager
   │
   ▼
RecordCodec
   │
   ▼
SlottedPage
   │
   ▼
Page
   │
   ▼
FileManager
   │
   ▼
.jdb
```

Each layer has a separate responsibility.

---

# Project Structure

## `jugaaddb/core/schema.py`

Defines the structure of a table.

It currently provides:

- `Column`
- `Schema`
- supported data types
- row validation
- primary-key definition
- nullable rules
- UNIQUE rules

Supported types currently include:

- `INTEGER`
- `FLOAT`
- `TEXT`
- `BOOLEAN`

Example:

```python
Column(
    name="id",
    data_type="INTEGER",
    primary_key=True,
    nullable=False
)
```

---

## `jugaaddb/core/database.py`

Provides the high-level database interface.

It currently handles:

- creating a database
- opening an existing database
- creating tables
- retrieving tables
- saving database state

Example:

```python
db = Database.create("college.jdb")

students = db.create_table(
    "students",
    [
        Column("id", "INTEGER", primary_key=True, nullable=False),
        Column("name", "TEXT"),
        Column("cgpa", "FLOAT")
    ]
)
```

---

## `jugaaddb/relational/table.py`

Represents a relational table and provides the current high-level row operations.

It currently supports:

- `insert()`
- `select_all()`
- `update()`
- `delete()`

It also enforces:

- schema validation
- primary-key uniqueness
- UNIQUE constraints
- valid column names

This is the high-level relational layer. The later SQL engine will eventually sit above this type of database functionality.

---

# Storage Layer

## `jugaaddb/storage/constants.py`

Contains storage constants used by the physical file layer.

Important values include:

- page size
- file magic
- file version
- header size
- payload length field size

The current page size is:

```text
4096 bytes
```

A constant is used instead of scattering the number throughout the code so that storage behavior can be changed from one place.

---

## `jugaaddb/storage/page.py`

Represents a physical fixed-size page.

A page is a fixed block of bytes used by the storage system.

Current responsibilities:

- create a page
- validate page IDs
- hold exactly `PAGE_SIZE` bytes
- read raw page bytes
- write data into a page
- determine whether a page is empty

The class is intentionally low-level.

It does not understand:

- tables
- columns
- SQL
- Python dictionaries

It only understands page-sized bytes.

---

## `jugaaddb/storage/file_manager.py`

Handles the actual database file.

Current responsibilities:

- create a `.jdb` file
- open and validate a `.jdb` file
- validate the file header
- count pages
- read pages
- overwrite existing pages
- allocate new pages

The first physical page, page `0`, is reserved for the file header.

Data pages begin from page `1`.

Conceptually:

```text
.jdb
┌─────────────────────┐
│ Page 0              │
│ File Header         │
├─────────────────────┤
│ Page 1              │
│ Data                │
├─────────────────────┤
│ Page 2              │
│ Data                │
├─────────────────────┤
│ Page 3              │
│ Data                │
└─────────────────────┘
```

---

## `jugaaddb/storage/engine.py`

Provides the current database-level persistence mechanism.

It currently:

- creates the initial database structure
- saves database data
- loads database data
- converts the database structure to bytes
- stores the bytes across physical pages
- reconstructs the database structure after loading

The current implementation uses JSON as a transitional logical payload inside the page-based binary file structure.

This is intentional for Phase 1.

It gives the project a working persistent database while the lower-level record-storage system is built separately.

The long-term goal is to move increasingly more responsibility from this transitional representation into the custom storage engine.

---

# Record Storage Layer

## `jugaaddb/storage/record.py`

Contains the binary `RecordSerializer`.

It converts Python values into a compact binary record representation and converts them back.

Supported record values include:

- `NULL`
- `INTEGER`
- `FLOAT`
- `TEXT`
- `BOOLEAN`

The serializer stores type information and payload length for each field.

Conceptually:

```text
Record
│
├── field count
│
├── field 1
│   ├── type
│   ├── length
│   └── value
│
├── field 2
│   ├── type
│   ├── length
│   └── value
│
└── ...
```

This is the beginning of a real binary record format.

---

## `jugaaddb/storage/record_codec.py`

Connects the logical schema with the binary serializer.

`RecordCodec`:

```text
Python row
   ↓
Schema validation
   ↓
Column order
   ↓
RecordSerializer
   ↓
binary record
```

When reading:

```text
binary record
   ↓
RecordSerializer
   ↓
values
   ↓
Schema column names
   ↓
Python row
```

This prevents the binary storage layer from having to understand table-specific column names itself.

---

## `jugaaddb/storage/slotted_page.py`

Implements a slotted-page structure for variable-length records.

A slotted page contains:

```text
┌──────────────────────────────┐
│ Header                       │
├──────────────────────────────┤
│ Record 0                     │
│ Record 1                     │
│ Record 2                     │
│ ...                          │
│                              │
│ Free Space                   │
│                              │
├──────────────────────────────┤
│ Slot Directory               │
│ Slot 0: offset + length      │
│ Slot 1: offset + length      │
│ Slot 2: offset + length      │
└──────────────────────────────┘
```

The slot directory lets the system locate records using a slot number.

A deleted record keeps its slot ID. Its slot length becomes zero.

This gives JugaadDB a stable physical identity:

```text
RecordID = (page_id, slot_id)
```

For example:

```text
(1, 0)
(1, 1)
(2, 0)
```

---

## `jugaaddb/storage/record_manager.py`

Provides schema-aware physical record management.

It connects:

```text
Schema
  ↓
RecordCodec
  ↓
SlottedPage
  ↓
Page
  ↓
FileManager
```

Current responsibilities:

- insert a record
- return a `RecordID`
- find a page with enough free space
- allocate a new page when required
- read a record by `RecordID`
- decode a record back into a Python row
- delete a record
- persist modified pages

The separation between `SlottedPage` and `Page` is intentional.

`FileManager` works with physical `Page` objects.

`RecordManager` converts the slotted-page representation into physical page bytes before sending it to the file layer.

---

# Phase 1 Data Flow

### Insert

```text
row
 ↓
Schema validation
 ↓
RecordCodec
 ↓
Binary record
 ↓
RecordManager
 ↓
SlottedPage
 ↓
Page
 ↓
FileManager
 ↓
.jdb
```

### Read

```text
RecordID
 ↓
FileManager
 ↓
Page
 ↓
SlottedPage
 ↓
Binary record
 ↓
RecordCodec
 ↓
Python row
```

### Delete

```text
RecordID
 ↓
RecordManager
 ↓
SlottedPage
 ↓
slot marked deleted
 ↓
Page
 ↓
FileManager
 ↓
.jdb
```

---

# Example

```python
from jugaaddb.core.database import Database
from jugaaddb.core.schema import Column

db = Database.create("college.jdb")

students = db.create_table(
    "students",
    [
        Column("id", "INTEGER", primary_key=True, nullable=False),
        Column("name", "TEXT", nullable=False),
        Column("branch", "TEXT"),
        Column("cgpa", "FLOAT")
    ]
)

students.insert({
    "id": 1,
    "name": "Sayman",
    "branch": "CSE",
    "cgpa": 8.5
})

students.insert({
    "id": 2,
    "name": "Rahul",
    "branch": "CSE",
    "cgpa": 9.1
})

print(students.select_all())
```

Expected logical result:

```text
[
    {
        "id": 1,
        "name": "Sayman",
        "branch": "CSE",
        "cgpa": 8.5
    },
    {
        "id": 2,
        "name": "Rahul",
        "branch": "CSE",
        "cgpa": 9.1
    }
]
```

---

# Testing

The project uses `pytest`.

Run the complete test suite:

```bash
python -m pytest -v
```

Current Phase 1 checkpoint:

```text
89 passed
```

The tests cover the implemented database, schema, page, file, record, slotted-page, and record-manager behavior.

---

# Design Principles

## 1. Build instead of wrap

JugaadDB should implement database concepts itself instead of delegating the core problem to an existing database.

## 2. Layer separation

Each layer should have one main responsibility.

For example:

```text
FileManager → physical file
Page        → fixed-size byte block
SlottedPage → records + slots
RecordCodec → schema ↔ binary record
Table       → relational operations
Database    → database-level organization
```

## 3. Persistent behavior

A database should not disappear when the Python process ends.

JugaadDB therefore stores its state in a `.jdb` file and tests reloading behavior.

## 4. Incremental engineering

Complex DBMS features are being built in stages instead of pretending to implement everything at once.

---

# Roadmap

## Phase 1 — Database Foundation

**Status: COMPLETE**

- Persistence
- File format foundation
- Schema
- Tables
- CRUD
- Binary records
- Slotted pages
- Record manager
- Tests

## Phase 2 — SQL Engine

Planned:

- Lexer
- Tokens
- Parser
- AST (Abstract Syntax Tree — query ka structured form)
- SQL executor
- `CREATE TABLE`
- `INSERT`
- `SELECT`
- `WHERE`
- `UPDATE`
- `DELETE`
- `ORDER BY`
- `LIMIT`

Target:

```sql
CREATE TABLE students (...);

INSERT INTO students VALUES (...);

SELECT * FROM students
WHERE cgpa > 8.0;
```

## Phase 3 — Indexing

Planned:

- B-tree/B+tree-style indexing
- Hash indexing
- index manager
- query lookup optimization

## Phase 4 — Transactions and Recovery

Planned:

- transaction manager
- WAL (Write-Ahead Logging — change ko main data se pehle log me record karna)
- commit
- rollback
- crash recovery

## Phase 5 — NoSQL

Planned:

- document model
- key-value model
- flexible document storage
- unified engine interface

## Phase 6 — Security

Planned:

- authentication
- RBAC (Role-Based Access Control — role ke basis par permissions)
- password protection
- encryption
- audit logging

## Phase 7 — Interface and Customization

Planned:

- CLI
- GUI
- database inspection tools
- configuration/customization
- performance information

## Phase 8 — Optional Deployment

The core project remains designed to work locally without paid infrastructure.

Optional free deployment/cloud demonstrations may be added later where practical.

---

# Project Philosophy

JugaadDB is intentionally being built from the bottom upward.

Instead of starting with a polished UI, the project starts with:

```text
bytes
 ↓
pages
 ↓
records
 ↓
tables
 ↓
database
 ↓
SQL
 ↓
indexes
 ↓
transactions
 ↓
security
 ↓
interfaces
```

The objective is to understand and implement the foundations of a database system, not merely make something that looks like one.

---

# Phase 1 Completion Statement

Phase 1 is considered complete at the current project scope.

The storage foundation now has:

```text
Persistent file
     +
Physical pages
     +
Binary records
     +
Slotted pages
     +
Record IDs
     +
Schema-aware encoding
     +
CRUD
     +
Persistence tests
```

**Phase 1 test checkpoint: 89/89 passed.**

The next major development stage is **Phase 2 — SQL Engine**.