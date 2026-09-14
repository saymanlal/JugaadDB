# JugaadDB

## Database Management System Built from Scratch in Python

**Phase 2 — SQL Engine: COMPLETE**

**Final test status: 191 passed / 191 total**

JugaadDB is a custom database management system being developed from scratch in Python. The project focuses on implementing database-engine concepts rather than wrapping an existing database such as MySQL, PostgreSQL, MongoDB, or SQLite.

Phase 1 established persistence, schema, tables, CRUD, pages, and storage foundations. Phase 1.5 introduced binary record serialization, schema-aware record encoding, slotted pages, and a Record Manager. Phase 2 builds the SQL processing layer on top of these foundations.

## Phase 2 Overview

Phase 2 adds an end-to-end SQL pipeline:

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
Execution Plan
   ↓
Executor
   ↓
JugaadDB
```

Implemented SQL statements:

- SELECT
- INSERT
- UPDATE
- DELETE
- CREATE TABLE

Implemented SQL concepts:

- identifiers and literals
- comparison operators: `=`, `!=`, `<`, `<=`, `>`, `>=`
- WHERE conditions
- AND / OR logical expressions
- AND precedence over OR
- INTEGER, FLOAT, TEXT, BOOLEAN
- NULL / NOT NULL
- PRIMARY KEY
- UNIQUE
- duplicate-column validation
- unknown-column validation
- structured query results
- SQL-specific errors

## Lexer

The lexer converts SQL source text into tokens. It recognizes SQL keywords, identifiers, numbers, strings, operators, punctuation, NULL, boolean literals, AND, OR, and NOT.

String processing supports quoted strings and escape sequences. Numeric processing rejects malformed forms such as invalid trailing-dot numbers.

## AST

The parser converts tokens into an Abstract Syntax Tree.

The AST contains structures for identifiers, literals, binary expressions, logical expressions, assignments, SELECT, INSERT, UPDATE, DELETE, CREATE TABLE, and column definitions.

## Parser

The parser validates SQL grammar and constructs AST objects.

Examples:

```sql
SELECT * FROM students
```

```sql
SELECT name, cgpa FROM students WHERE cgpa > 8.0
```

```sql
INSERT INTO students (id, name) VALUES (1, 'Sayman')
```

```sql
UPDATE students SET cgpa = 10.0 WHERE department = 'AIML' AND cgpa > 8.0
```

```sql
DELETE FROM students WHERE id = 1 OR id = 2
```

```sql
CREATE TABLE students (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT UNIQUE,
    cgpa FLOAT
)
```

## Query Planner

The planner converts AST statements into execution plans.

Current plan concepts:

- TableScan
- Filter
- Projection
- InsertPlan
- UpdatePlan
- DeletePlan
- CreateTablePlan

The planner is intentionally separated from execution so future optimization can choose between a full table scan and an index scan.

## SQL Executor

The executor performs SELECT, INSERT, UPDATE, DELETE, and CREATE TABLE operations.

It also performs semantic validation such as unknown-column detection, duplicate-column detection, expression validation, and SQL-level error conversion.

Schema enforcement remains connected to the existing schema and table layers.

## Query Results

`QueryResult` represents row-returning queries and provides columns, rows, query type, row count, iteration, indexing, and list conversion.

`CommandResult` represents commands and provides affected row count and query type.

## SQL Error System

```text
SQLError
├── SQLSyntaxError
├── SQLExecutionError
└── SQLPlanningError
```

Low-level `ValueError` and `TypeError` failures are converted into SQL execution errors where appropriate.

## Schema Semantics

SQL table creation connects directly to the existing schema system.

Example:

```sql
CREATE TABLE students (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT UNIQUE,
    cgpa FLOAT
)
```

The database enforces primary-key uniqueness, UNIQUE values, NOT NULL requirements, supported data types, unknown-column rejection, duplicate-column rejection, and required-column validation.

## Compound Conditions

Phase 2 supports compound filtering for SELECT, UPDATE, and DELETE.

Examples:

```sql
SELECT * FROM students WHERE department = 'AIML' AND cgpa > 8.0
```

```sql
UPDATE students SET cgpa = 10.0 WHERE department = 'AIML' AND cgpa > 8.0
```

```sql
DELETE FROM students WHERE department = 'AIML' AND cgpa < 8.0
```

```sql
UPDATE students SET department = 'TECH' WHERE id = 1 OR id = 2
```

## Database API

SQL is exposed through:

```python
db.execute(sql)
```

The complete path is:

```text
SQL string
    ↓
Lexer
    ↓
Parser
    ↓
Planner
    ↓
Executor
    ↓
Result
```

## Testing

Phase 2 was developed incrementally with automated tests.

Final checkpoint:

```text
191 passed
0 failed
```

The suite covers lexer behavior, strings, escapes, numeric validation, parsing, AST construction, planning, execution, SQL integration, persistence, schema semantics, NULL, NOT NULL, UNIQUE, PRIMARY KEY, duplicate columns, unknown columns, SQL errors, AND/OR, comparisons, projection, UPDATE, DELETE, and affected-row counts.

## Architecture After Phase 2

```text
JUGAADDB
│
├── SQL ENGINE
│   ├── Lexer
│   ├── Parser
│   ├── AST
│   ├── Planner
│   └── Executor
│
├── DATABASE CORE
│   ├── Database
│   ├── Schema
│   └── Table
│
├── STORAGE ENGINE
│   ├── File Manager
│   ├── Pages
│   ├── Storage Engine
│   ├── Record Serializer
│   ├── Record Codec
│   ├── Slotted Pages
│   └── Record Manager
│
└── TEST SUITE
```

## Important Design Decision

The SQL executor currently operates through the existing table abstraction and transitional storage implementation. The physical Record Manager and slotted-page infrastructure exist, but SQL execution has not yet been completely migrated to the physical record path.

This is intentional. The project is being developed in controlled stages so each subsystem can be tested independently before deeper integration.

## Phase 3 — Indexing & Query Performance

Phase 2 is complete. The next phase is indexing and query performance.

Planned work:

```text
Index abstraction
      ↓
Index Manager
      ↓
B+Tree / B-Tree style index
      ↓
Persistent index storage
      ↓
CREATE INDEX
      ↓
Index maintenance
      ↓
Index lookup
      ↓
Planner: Table Scan vs Index Scan
      ↓
Performance testing
```

The goal is to move from full table scans toward planner-selected index lookups.

## Complete Roadmap

```text
Phase 1
Persistence + Schema + CRUD
        ✅

Phase 1.5
Physical Record Storage
        ✅

Phase 2
SQL Engine
        ✅
191/191 tests

Phase 3
Indexing + Query Performance
        🚀

Phase 4
Transactions + WAL + Recovery
        ⏳

Phase 5
NoSQL Document + Key-Value Engine
        ⏳

Phase 6
Security + RBAC + Encryption + Audit
        ⏳

Phase 7
GUI + Customization + Optional Cloud Demo
        ⏳
```

## Philosophy

JugaadDB is being built from first principles. The goal is to implement and understand database-engine building blocks rather than merely building an application around an existing database.

The project emphasizes correctness first, followed by performance and advanced database capabilities.