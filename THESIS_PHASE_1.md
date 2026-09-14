# JugaadDB — Phase 1 Technical Thesis

## A Simple Study of the Database Foundation Built from Scratch in Python

---

# 1. Introduction

JugaadDB is a database management system (DBMS — software that stores and manages data) being developed from scratch in Python.

The main purpose of the project is to understand what happens inside a database.

Normally, when we use a database, we write something like:

```sql
SELECT * FROM students;
```

and the database gives us the answer.

But a database has to do a lot of work internally before it can give that answer.

It has to:

```text
store data
find data
organize data
validate data
save data permanently
read data later
handle changes
```

JugaadDB is being developed to understand and implement these internal ideas step by step.

Phase 1 focuses on the foundation:

```text
Database
Schema
Tables
Rows
Persistence
Pages
Binary Records
Slotted Pages
Record Manager
```

The current Phase 1 test checkpoint is:

```text
89 passed
```

---

# 2. What Does "Database" Mean?

A database is simply an organized place where data can be stored and retrieved.

Daily example:

Suppose a college has a notebook:

```text
ID     Name       Branch    CGPA
1      Sayman     CSE       8.5
2      Rahul      CSE       9.1
3      Aman       IT        8.2
```

That notebook is a very simple form of data storage.

A DBMS makes this idea much more powerful.

Instead of manually searching the notebook, we can ask the system:

```text
Give me students whose CGPA is greater than 8.5.
```

The DBMS finds the required data.

JugaadDB is being built to create that kind of system from the lower level upward.

---

# 3. What Was the Problem Before Phase 1?

At the beginning, the project needed a proper foundation.

We needed answers to basic questions:

- Where will the database live?
- How will it survive after the Python program closes?
- How will a table be represented?
- How will a row be validated?
- How will records become bytes?
- How will bytes be stored inside a file?
- How can one particular record be found again?

Phase 1 solves these foundation-level problems.

---

# 4. Phase 1 Architecture

The Phase 1 architecture is:

```text
Database
    ↓
Table
    ↓
RecordManager
    ↓
RecordCodec
    ↓
SlottedPage
    ↓
Page
    ↓
FileManager
    ↓
.jdb file
```

Think of a real warehouse.

```text
Database       = complete warehouse
Table          = one section
Record         = one box
SlottedPage    = shelf
Page           = fixed-size shelf space
FileManager    = person handling the storage room
.jdb file      = actual warehouse building
```

The software analogy is not perfect, but it makes the idea easier to understand.

---

# 5. File-by-File Explanation

This section explains every Phase 1 source file in simple language.

---

# 5.1 `jugaaddb/core/schema.py`

## What is this file?

This file defines what a table is allowed to contain.

It contains:

```text
Column
Schema
SUPPORTED_TYPES
```

## What is a Column?

A column is one type of information in a table.

Example:

```text
id
name
branch
cgpa
```

A column definition can say:

```text
id → INTEGER
name → TEXT
cgpa → FLOAT
```

## Daily-life example

Imagine a college admission form.

It may have:

```text
Name
Age
Roll Number
Course
```

You cannot write a photograph inside the "Age" field.

Similarly, JugaadDB checks whether data matches the defined column type.

## What does Schema mean?

Schema means the structure/rules of a table.

For example:

```text
students

id       INTEGER
name     TEXT
branch   TEXT
cgpa     FLOAT
```

That is the schema.

## What does this file do?

It currently handles:

- supported data types
- duplicate column detection
- primary-key definition
- NULL rules
- UNIQUE rules
- row validation

## Why was this change made?

Without schema validation, a table could receive completely random data.

For example:

```text
cgpa = "hello"
```

would make no sense if CGPA is supposed to be a number.

So this file acts like a gatekeeper.

---

# 5.2 `jugaaddb/core/database.py`

## What is this file?

This is the high-level database controller.

It handles:

- database creation
- database opening
- table creation
- table retrieval
- saving database state

## Daily-life example

Imagine a college administration office.

The office manages several registers:

```text
students
teachers
courses
fees
```

The database object is like the main office that knows which registers exist.

## Example

```python
db = Database.create("college.jdb")
```

means:

```text
Create a new JugaadDB database
and store it in college.jdb.
```

Then:

```python
db.table("students")
```

means:

```text
Give me the students table.
```

## Why was this file needed?

We needed one clear entry point for users of the database.

A user should not have to manually operate pages and raw bytes just to create a table.

This file provides the high-level interface.

---

# 5.3 `jugaaddb/relational/table.py`

## What is this file?

This file represents a table.

A table is a collection of rows following a schema.

Example:

```text
students

id   name     branch   cgpa
1    Sayman   CSE      8.5
2    Rahul    CSE      9.1
```

## What operations does it support?

Currently:

```text
insert
select_all
update
delete
```

## Daily-life example

Imagine a register.

To add a student:

```text
INSERT
```

To see students:

```text
SELECT
```

To correct someone's CGPA:

```text
UPDATE
```

To remove a record:

```text
DELETE
```

## What validations happen here?

The table checks:

- valid columns
- valid values
- primary-key duplicates
- UNIQUE duplicates

## Why was this file needed?

The database needs a logical table-level interface.

The lower storage layer should not need to understand what "student" or "CGPA" means.

This file handles the relational-table side.

---

# 5.4 `jugaaddb/storage/constants.py`

## What is this file?

This file stores important storage numbers and identifiers in one place.

For example:

```text
PAGE_SIZE = 4096
```

## What is a page?

A page is a fixed-size block of storage.

Here:

```text
4096 bytes
```

## Daily-life example

Imagine a notebook where every page has exactly one fixed page size.

Instead of saying:

```text
use 4096 everywhere
```

we define:

```text
PAGE_SIZE
```

Then all storage code can use the same rule.

## Why was this change made?

Centralizing constants prevents inconsistent values.

If page size needs to change later, we can change one place instead of searching through the entire project.

---

# 5.5 `jugaaddb/storage/page.py`

## What is this file?

This file represents one physical page.

It is a low-level storage object.

It knows:

```text
page ID
raw bytes
```

It does not know:

```text
student
name
CGPA
SQL
table
```

## Daily-life example

Think about a blank sheet of fixed size.

The sheet does not know what you will write on it.

It only provides space.

A `Page` is similar.

## Main responsibilities

It can:

- create a page
- store bytes
- return bytes
- check whether it is empty
- validate page size

## Why was this file needed?

The storage engine needs a basic physical unit.

That physical unit is the page.

---

# 5.6 `jugaaddb/storage/file_manager.py`

## What is this file?

This file directly manages the `.jdb` file.

It knows how to:

- create the file
- open the file
- validate the file
- read pages
- write pages
- allocate new pages
- count pages

## What is a file header?

A file header is information stored at the beginning of the database file that helps identify the file.

JugaadDB stores:

```text
magic
version
```

## What is "magic"?

Magic is a special fixed byte pattern used to recognize a file type.

It is like writing:

```text
THIS IS A JUGAADDB FILE
```

in a machine-readable form.

## Why?

If someone gives JugaadDB a random file, the system should not blindly treat it as a valid database.

## Page 0

Page `0` is reserved for the file header.

Data pages start from:

```text
Page 1
Page 2
Page 3
...
```

## Daily-life example

Imagine a book.

The first page contains:

```text
Book title
Version
Basic information
```

The remaining pages contain the actual content.

The JugaadDB file follows a similar idea.

---

# 5.7 `jugaaddb/storage/engine.py`

## What is this file?

This is the current database persistence engine.

Persistence means:

> Data remains available even after the program closes.

For example:

```text
Python program starts
        ↓
insert Sayman
        ↓
program closes
        ↓
program starts again
        ↓
Sayman still exists
```

That is persistence.

## What does the engine currently do?

It:

- creates initial database data
- converts data into bytes
- stores those bytes in pages
- loads the bytes later
- reconstructs the database structure

## Important Phase 1 detail

The current engine uses JSON as a transitional logical payload inside the page-based binary file structure.

This is not the final storage design.

The project has separately built:

```text
RecordSerializer
RecordCodec
SlottedPage
RecordManager
```

to move the project toward actual record-level physical storage.

## Why was this approach used?

Because the project is being developed incrementally.

It allowed the database to become persistent and testable first, while the lower-level record engine was developed independently.

This avoids trying to build the entire DBMS in one step.

---

# 5.8 `jugaaddb/storage/record.py`

## What is this file?

This file converts values into binary records.

Binary means data represented as bytes that the computer can store directly.

Example logical row:

```text
1
Sayman
8.5
True
```

The serializer turns these values into a structured sequence of bytes.

## Why not simply store the Python dictionary?

Because physical database storage ultimately needs a defined byte representation.

A dictionary is a Python-level object.

A database file needs bytes.

## What types are currently supported?

```text
NULL
INTEGER
FLOAT
TEXT
BOOLEAN
```

## What does the serializer store?

For each field, it stores information about:

```text
type
length
value
```

## Daily-life example

Imagine sending a parcel.

If you only throw objects into a box, the receiver may not know what each object means.

Instead, you attach labels:

```text
Type: book
Size: 200 pages
Content: ...
```

The serializer does a similar job for binary data.

---

# 5.9 `jugaaddb/storage/record_codec.py`

## What is this file?

This file connects the schema to the binary serializer.

It knows:

```text
which column comes first
which column comes second
what the values should be
```

## Example

Schema:

```text
id
name
cgpa
```

Row:

```python
{
    "id": 1,
    "name": "Sayman",
    "cgpa": 8.5
}
```

The codec turns it into ordered values:

```text
1
Sayman
8.5
```

and passes them to the serializer.

## On reading

It performs the reverse process:

```text
bytes
 ↓
values
 ↓
column names
 ↓
dictionary
```

## Why was this file needed?

We do not want the low-level serializer to know about table schemas.

This separation makes the architecture cleaner.

---

# 5.10 `jugaaddb/storage/slotted_page.py`

## What is this file?

This is one of the most important Phase 1 storage components.

A slotted page is a page designed to store multiple variable-length records.

## What does "slot" mean?

A slot is an entry that tells the database where a particular record is located.

For example:

```text
Slot 0 → record location
Slot 1 → record location
Slot 2 → record location
```

## Daily-life example

Imagine a parking lot.

Each parking space has a number:

```text
Slot 0
Slot 1
Slot 2
```

The car may change, but the parking-space number remains the identifier.

Similarly, JugaadDB uses slot IDs to identify records.

## Page layout

```text
┌──────────────────────────────┐
│ Header                       │
├──────────────────────────────┤
│ Record Area                  │
│                              │
│ Record 0                     │
│ Record 1                     │
│ Record 2                     │
│                              │
│ Free Space                   │
│                              │
├──────────────────────────────┤
│ Slot Directory               │
│ Slot 0                       │
│ Slot 1                       │
│ Slot 2                       │
└──────────────────────────────┘
```

The record area grows from the beginning.

The slot directory grows from the end.

Free space remains between them.

## Why variable-length records?

Consider:

```text
Aman
Sayman
Krushn
```

These names do not have the same length.

A database therefore needs a way to store records without forcing every record to have exactly the same size.

## Deletion

When a record is deleted, JugaadDB currently does not immediately remove the physical record bytes.

Instead:

```text
slot length = 0
```

The slot remains.

This preserves the `RecordID`.

---

# 5.11 `jugaaddb/storage/record_manager.py`

## What is this file?

This file connects the logical record system to the physical storage system.

It is the bridge between:

```text
row
```

and:

```text
physical page
```

## Record ID

Every stored record can be identified using:

```text
(page_id, slot_id)
```

Example:

```text
(1, 0)
```

means:

```text
page 1
slot 0
```

## Insert flow

```text
Python row
 ↓
RecordCodec
 ↓
binary record
 ↓
find suitable page
 ↓
SlottedPage.insert()
 ↓
slot ID
 ↓
save page
 ↓
RecordID
```

## Read flow

```text
RecordID
 ↓
load page
 ↓
find slot
 ↓
read binary record
 ↓
RecordCodec
 ↓
Python dictionary
```

## Delete flow

```text
RecordID
 ↓
load page
 ↓
mark slot deleted
 ↓
save page
```

## Why was this file needed?

Without a RecordManager, higher-level code would need to manually understand:

```text
serialization
pages
slots
file writing
```

The RecordManager hides these details.

That is its main job.

---

# 6. Why `SlottedPage` Does Not Directly Go Into `FileManager`

This is an important architectural decision.

`FileManager` works with:

```text
Page
```

because it is a physical file-management layer.

`SlottedPage` is a higher-level structure that understands records and slots.

Therefore:

```text
SlottedPage
    ↓
raw bytes
    ↓
Page
    ↓
FileManager
```

This is called layer separation (different parts have different jobs).

## Daily-life example

Imagine courier delivery.

The warehouse worker prepares a package.

The transport company does not need to understand the product inside the package.

It only transports the package.

Similarly:

```text
SlottedPage = prepares/manages record layout
Page        = physical byte container
FileManager = stores/transfers physical pages
```

This separation will become increasingly important when indexing, transactions, and recovery are added.

---

# 7. The `to_bytes()` Addition

During Phase 1.5 integration, `RecordManager` needed a way to convert a `SlottedPage` back into raw bytes.

The `SlottedPage` already had:

```text
read(slot_id)
```

but that method means:

```text
read one record
```

It does not mean:

```text
read the entire page
```

Therefore a dedicated:

```text
to_bytes()
```

operation was added.

It returns:

```text
bytes(self.data)
```

This makes the intent explicit.

The flow becomes:

```text
SlottedPage
    ↓ to_bytes()
raw page bytes
    ↓
Page
    ↓
FileManager
```

---

# 8. Why Duplicate Page Writes Were Removed

During RecordManager integration, a page could accidentally be written twice:

```text
write_page()
_save_page()
```

Both operations represented the same persistence action.

This was unnecessary.

The final design uses:

```text
_save_page()
```

as the single path.

That gives a cleaner flow:

```text
change page
    ↓
_save_page()
    ↓
Page
    ↓
FileManager
```

This reduces duplicate work and keeps the storage responsibility centralized.

---

# 9. Why `RecordSerializer` Was Added

Before physical records, a row mainly existed as a Python dictionary.

Example:

```python
{
    "id": 1,
    "name": "Sayman",
    "cgpa": 8.5
}
```

That is convenient for Python, but physical storage needs bytes.

Therefore:

```text
Python values
       ↓
RecordSerializer
       ↓
bytes
```

and later:

```text
bytes
       ↓
RecordSerializer
       ↓
Python values
```

This creates a defined record representation.

---

# 10. Why `RecordCodec` Was Added

The serializer should not have to know:

```text
student.id
student.name
student.cgpa
```

It should only know values.

The codec knows the schema and controls the mapping:

```text
column
 ↓
value
 ↓
serializer
```

This makes the system modular (parts can be changed independently).

---

# 11. Why `SlottedPage` Was Added

A simple page is only:

```text
4096 bytes
```

That alone does not tell us where records are.

A slotted page adds structure.

It answers:

```text
How many records are here?
Where is record 0?
Where is record 1?
How much free space is left?
Which slot was deleted?
```

This is a major step toward a real storage engine.

---

# 12. Why `RecordManager` Was Added

Without RecordManager:

```text
Table
 ↓
raw page handling
 ↓
raw serialization
 ↓
file operations
```

would become tightly mixed together.

With RecordManager:

```text
Table
 ↓
RecordManager
 ↓
storage system
```

The table can eventually ask:

```text
insert this row
read this RecordID
delete this RecordID
```

without needing to know the physical details.

---

# 13. CRUD in Phase 1

CRUD means:

```text
C = Create
R = Read
U = Update
D = Delete
```

Daily example:

Imagine a student register.

### Create

Add a student:

```text
Sayman
```

### Read

Check the student's information.

### Update

Change:

```text
CGPA 8.5 → 8.7
```

### Delete

Remove the student record.

JugaadDB currently supports these basic relational operations.

---

# 14. Primary Key

A primary key is a value used to uniquely identify a row.

Example:

```text
id
```

Values:

```text
1
2
3
```

should not repeat.

Daily example:

College roll number.

Two students should not normally have the same roll number.

JugaadDB checks duplicate primary-key values.

---

# 15. UNIQUE Constraint

UNIQUE means:

> A particular column value should not repeat.

For example:

```text
email
```

If one row has:

```text
sayman@example.com
```

another row cannot use the same value if that column is UNIQUE.

Primary key and UNIQUE are related ideas, but they are not exactly the same rule.

---

# 16. NULL

NULL means:

> There is no value stored for this field.

It does not simply mean zero.

For example:

```text
cgpa = NULL
```

means CGPA is currently missing.

While:

```text
cgpa = 0
```

means the value is actually zero.

JugaadDB's schema can define whether a column allows NULL.

---

# 17. Persistence

Persistence means data survives program shutdown.

Example:

### Before

```text
Start program
Insert Sayman
Close program
```

If data disappears, it was not persistent.

### After

```text
Start program
Insert Sayman
Close program

Start again
Read students

Sayman is still there
```

Phase 1 includes persistence tests.

---

# 18. What Does 89 Passed Mean?

The project currently has:

```text
89 tests
89 passed
0 failed
```

This means the implemented behavior covered by the test suite is currently working.

It does not mean:

```text
JugaadDB is finished.
```

It means:

```text
Phase 1 scope is working and verified by the current tests.
```

That distinction is important in software engineering.

---

# 19. Phase 1 End-to-End Example

Suppose we insert:

```python
{
    "id": 1,
    "name": "Sayman",
    "branch": "CSE",
    "cgpa": 8.5
}
```

The conceptual journey is:

```text
Python dictionary
        ↓
Schema validates it
        ↓
RecordCodec orders its values
        ↓
RecordSerializer converts values to bytes
        ↓
RecordManager finds a suitable page
        ↓
SlottedPage stores the record
        ↓
Page contains the final bytes
        ↓
FileManager writes the page
        ↓
college.jdb stores the data
```

When reading:

```text
college.jdb
        ↓
FileManager
        ↓
Page
        ↓
SlottedPage
        ↓
RecordManager
        ↓
RecordCodec
        ↓
Python dictionary
```

That is the core Phase 1 journey.

---

# 20. Why Phase 1 Is Important

Phase 1 may look less impressive than a GUI, but it creates the foundation for the difficult parts of the project.

For example:

```text
SQL
 ↓
needs executor
 ↓
needs records
 ↓
needs storage
```

Indexes need records.

Transactions need storage changes.

Recovery needs stored pages and logs.

NoSQL also needs storage.

Therefore:

```text
Good storage foundation
        ↓
stronger future DBMS
```

---

# 21. What Phase 1 Does Not Yet Have

Phase 1 is complete at its defined scope, but JugaadDB is not a complete DBMS yet.

The following major systems are future work:

- SQL lexer
- SQL parser
- AST
- query planner
- query optimizer
- indexes
- B-tree/B+tree-style structures
- transactions
- WAL
- crash recovery
- concurrency control
- NoSQL document model
- key-value model
- authentication
- RBAC
- encryption
- audit logging
- GUI
- advanced query features

These belong to later phases.

---

# 22. Phase 1 Changes — What, Why, and Result

## Database and Schema

### What changed

Created the basic database and schema system.

### Why

The project needed a structured way to define tables and validate data.

### Result

JugaadDB can understand:

```text
tables
columns
types
primary keys
NULL rules
UNIQUE rules
```

---

## CRUD

### What changed

Added:

```text
insert
select
update
delete
```

### Why

A database needs basic data manipulation before more advanced query processing can be built.

### Result

Tables can be modified and read through the current Python API.

---

## Persistence

### What changed

Added `.jdb` file-based persistence.

### Why

Data should survive program shutdown.

### Result

Database state can be saved and loaded again.

---

## Physical Pages

### What changed

Introduced fixed-size pages and page-aware file storage.

### Why

Databases generally need structured physical storage rather than treating the entire database as one unlimited blob.

### Result

The file is divided into page-sized blocks.

---

## Binary Record Serialization

### What changed

Added `RecordSerializer`.

### Why

Python objects need a stable byte representation for physical storage.

### Result

Supported values can be encoded into and decoded from binary records.

---

## Record Codec

### What changed

Added `RecordCodec`.

### Why

Schema information and binary serialization needed a clean bridge.

### Result

Rows can move between:

```text
schema-aware Python dictionaries
```

and:

```text
binary records
```

---

## Slotted Pages

### What changed

Added `SlottedPage`.

### Why

A page needs a way to hold multiple variable-length records and locate them.

### Result

Records can be stored using slots and offsets.

---

## Record Manager

### What changed

Added `RecordManager`.

### Why

Higher-level code should not directly manipulate page layouts and binary records.

### Result

The system can:

```text
insert → RecordID
read → row
delete → stored slot marked deleted
```

---

## `to_bytes()` Page Serialization

### What changed

Added a dedicated method for converting a `SlottedPage` into raw bytes.

### Why

`read(slot_id)` reads one record, not the complete page.

### Result

The correct storage path became:

```text
SlottedPage.to_bytes()
        ↓
Page
        ↓
FileManager
```

---

## Duplicate Write Removal

### What changed

Removed duplicate page-write operations from RecordManager.

### Why

The same modified page should not be written twice through two separate calls.

### Result

Page persistence now goes through one clear `_save_page()` path.

---

# 23. Final Phase 1 Architecture

```text
                    JugaadDB
                       │
             ┌─────────┴─────────┐
             │                   │
          Database             Table
             │                   │
             │                   │
             └─────────┬─────────┘
                       │
                RecordManager
                       │
                  RecordCodec
                       │
                SlottedPage
                       │
                     Page
                       │
                 FileManager
                       │
                    .jdb
```

This architecture creates a clear separation between:

```text
logical database operations
```

and:

```text
physical storage operations
```

---

# 24. Phase 1 Completion

Phase 1 is complete according to the current project scope.

The completed foundation contains:

```text
Database
Schema
Tables
CRUD
Persistence
Physical Pages
Binary Records
Record Codec
Slotted Pages
Record Manager
```

Verification:

```text
89 tests
89 passed
0 failed
```

This gives JugaadDB a stable foundation for the next major stage.

---

# 25. Next Phase

The next stage is:

# Phase 2 — SQL Engine

The planned flow is:

```text
SQL Query
    ↓
Lexer
    ↓
Tokens
    ↓
Parser
    ↓
AST
    ↓
Planner
    ↓
Executor
    ↓
RecordManager
    ↓
Storage
```

For example:

```sql
SELECT *
FROM students
WHERE cgpa > 8.5;
```

The goal of Phase 2 will be to make JugaadDB understand SQL itself instead of requiring users to call Python methods directly.

---

# 26. Final Understanding

The simplest way to understand Phase 1 is:

```text
We started with data.

We defined what valid data looks like.

We created tables.

We added CRUD.

We made the database persistent.

Then we went deeper.

We created pages.

We created binary records.

We created slotted pages.

We created Record IDs.

We created a RecordManager.

Finally, we tested the complete foundation.
```

In one line:

> **Phase 1 teaches JugaadDB how to organize, represent, store, retrieve, modify, and persist data before SQL is introduced.**

---

# Appendix A — Important Terms in Simple Language

| Term | Simple meaning |
|---|---|
| DBMS | Software that manages data |
| Database | Organized collection of data |
| Schema | Structure/rules of a table |
| Table | Organized collection of rows |
| Row/Record | One complete data entry |
| Column | One type/category of information |
| Persistence | Data survives program restart |
| Page | Fixed-size storage block |
| Binary | Data represented as bytes |
| Serializer | Converts values into stored bytes |
| Codec | Converts between logical data and encoded data |
| Slotted Page | Page organized to store records and their locations |
| Slot | Entry used to locate a record |
| Record ID | Identifier such as `(page_id, slot_id)` |
| Primary Key | Unique identifier for a row |
| UNIQUE | Rule preventing duplicate values |
| NULL | Missing/no value |
| CRUD | Create, Read, Update, Delete |
| Physical Storage | How data is actually stored |
| Logical Layer | How users/programs understand data |
| Validation | Checking whether data follows rules |
| Persistence Layer | Part responsible for saving/loading data |
| Modular | Split into independent parts with separate jobs |
| Serialization | Converting data into a storable/transmittable form |
| Variable-length | Size can differ between records |
| Offset | Position where something starts |
| Header | Initial information describing a file/page |
| Magic | Special bytes identifying a file type |
| Record Manager | Component responsible for storing and retrieving records |
| Storage Engine | System responsible for managing stored database data |
| SQL | Language used to communicate with relational databases |
| Lexer | Component that breaks SQL into tokens |
| Parser | Component that understands SQL structure |
| AST | Structured representation of a query |
| Planner | Decides how a query should be executed |
| Executor | Performs the planned query |

---

# Phase 1 Status

```text
STATUS: COMPLETE

TESTS: 89/89 PASSED

NEXT: PHASE 2 — SQL ENGINE
```