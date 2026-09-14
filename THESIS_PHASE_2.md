# JugaadDB — Phase 2 Technical Thesis

## Database Management System Built from Scratch in Python

### Phase 2: SQL Engine

---

## Abstract

JugaadDB is a custom Database Management System being developed from scratch in Python. Its objective is to understand and implement the internal architecture of a database system rather than depending on an existing database engine.

Phase 1 established persistence, schema, table, CRUD, page, and storage foundations. Phase 1.5 introduced binary record serialization, schema-aware record encoding, slotted pages, and a Record Manager.

Phase 2 introduces the SQL processing layer.

The central achievement of Phase 2 is an end-to-end SQL pipeline:

```text
SQL
 ↓
Lexer
 ↓
Parser
 ↓
AST
 ↓
Planner
 ↓
Executor
 ↓
Database
```

The implemented SQL layer supports SELECT, INSERT, UPDATE, DELETE, and CREATE TABLE, together with expressions, logical conditions, schema-aware validation, structured results, and SQL-specific error handling.

Final Phase 2 checkpoint:

```text
191 passed
0 failed
```

---

# 1. Introduction

Traditional database applications commonly hide database internals behind an existing engine such as MySQL, PostgreSQL, SQLite, or MongoDB.

JugaadDB follows a different approach. The project attempts to build the database engine itself.

Development is incremental. Each subsystem is implemented and tested before the next layer is added.

Phase 1 created the database foundation.

Phase 1.5 introduced physical record-storage concepts.

Phase 2 adds the SQL language-processing layer.

---

# 2. Objective of Phase 2

The primary objective was:

> To make JugaadDB capable of receiving SQL text, understanding it, converting it into an internal representation, creating an execution plan, executing that plan, and returning a structured result.

This required solving five major problems:

1. Understanding SQL text.
2. Understanding SQL structure.
3. Creating an execution plan.
4. Executing the plan.
5. Reporting invalid operations correctly.

---

# 3. Phase 2 Architecture

```text
                 SQL QUERY
                     │
                     ▼
                 ┌───────┐
                 │ Lexer │
                 └───┬───┘
                     │
                     ▼
                 ┌────────┐
                 │ Tokens │
                 └────┬───┘
                      │
                      ▼
                 ┌────────┐
                 │ Parser │
                 └────┬───┘
                      │
                      ▼
                 ┌───────┐
                 │  AST  │
                 └───┬───┘
                     │
                     ▼
                 ┌─────────┐
                 │ Planner │
                 └────┬────┘
                      │
                      ▼
             ┌─────────────────┐
             │ Execution Plan  │
             └────────┬────────┘
                      │
                      ▼
                ┌──────────┐
                │ Executor │
                └────┬─────┘
                     │
                     ▼
              ┌─────────────┐
              │ JugaadDB    │
              │ Database    │
              └─────────────┘
```

The architecture separates lexical analysis, parsing, planning, and execution.

---

# 4. Lexer

## 4.1 Purpose

A lexer converts SQL source text into tokens.

For example:

```sql
SELECT name FROM students
```

is conceptually converted into:

```text
SELECT
IDENTIFIER(name)
FROM
IDENTIFIER(students)
```

The parser can then work with structured tokens rather than raw characters.

## 4.2 Supported Elements

The lexer supports SQL keywords, identifiers, integer values, floating-point values, strings, operators, punctuation, NULL, boolean values, AND, OR, and NOT.

## 4.3 String Handling

Quoted strings are supported. Escape sequences are processed during lexical analysis.

## 4.4 Numeric Validation

Malformed numeric forms are rejected. This prevents invalid SQL numeric values from silently entering later stages.

---

# 5. Abstract Syntax Tree

## 5.1 Purpose

The parser converts tokens into an Abstract Syntax Tree.

The AST represents the meaning and structure of a SQL statement.

Implemented structures include:

```text
Identifier
Literal
BinaryExpression
LogicalExpression
Assignment

SelectStatement
InsertStatement
UpdateStatement
DeleteStatement
CreateTableStatement

ColumnDefinition
```

## 5.2 Identifier

An identifier represents an object name such as:

```text
students
name
cgpa
```

## 5.3 Literal

A literal represents a concrete value such as:

```text
10
8.5
'Sayman'
NULL
TRUE
```

## 5.4 Binary Expression

A binary expression represents comparisons such as:

```sql
cgpa > 8.0
```

Conceptually:

```text
left     = cgpa
operator = >
right    = 8.0
```

## 5.5 Logical Expression

Logical expressions connect conditions.

Example:

```sql
department = 'AIML' AND cgpa > 8.0
```

This is represented as a logical combination of two binary expressions.

---

# 6. Parser

The parser validates SQL grammar and creates AST structures.

Supported statements:

```text
SELECT
INSERT
UPDATE
DELETE
CREATE TABLE
```

The parser also handles WHERE expressions and logical conditions.

---

# 7. SELECT

Basic query:

```sql
SELECT * FROM students
```

Projection query:

```sql
SELECT id, name FROM students
```

Filtered query:

```sql
SELECT name FROM students WHERE cgpa > 8.0
```

Supported comparison operators:

```text
=
!=
<
<=
>
>=
```

Logical operators:

```text
AND
OR
```

`AND` has higher precedence than `OR`.

Therefore:

```sql
A = 1 OR B = 2 AND C = 3
```

is interpreted as:

```text
A = 1 OR (B = 2 AND C = 3)
```

---

# 8. INSERT

INSERT maps SQL columns to values.

Example:

```sql
INSERT INTO students
(id, name, cgpa)
VALUES
(1, 'Sayman', 8.5)
```

Validation includes unknown columns, duplicate columns, mismatched column/value count, missing required columns, incorrect data types, duplicate primary keys, duplicate UNIQUE values, and invalid NULL values.

---

# 9. UPDATE

Basic UPDATE:

```sql
UPDATE students SET cgpa = 10.0 WHERE id = 1
```

Compound condition:

```sql
UPDATE students SET cgpa = 10.0
WHERE department = 'AIML' AND cgpa > 8.0
```

OR condition:

```sql
UPDATE students SET department = 'TECH'
WHERE id = 1 OR id = 2
```

The executor identifies matching rows and applies the changes through the table layer.

---

# 10. DELETE

Basic DELETE:

```sql
DELETE FROM students WHERE id = 1
```

Compound condition:

```sql
DELETE FROM students
WHERE department = 'AIML' AND cgpa < 8.0
```

OR condition:

```sql
DELETE FROM students WHERE id = 1 OR id = 2
```

The executor identifies matching rows and deletes them through the table layer.

---

# 11. CREATE TABLE

SQL table creation is connected to the existing schema system.

Example:

```sql
CREATE TABLE students (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT UNIQUE,
    cgpa FLOAT
)
```

Supported schema concepts:

```text
INTEGER
FLOAT
TEXT
BOOLEAN

PRIMARY KEY
UNIQUE
NULL
NOT NULL
```

The executor converts SQL column definitions into the existing `Column` objects. This avoids maintaining two separate schema-validation systems.

---

# 12. Query Planner

The planner converts AST statements into execution plans.

Current structures include:

```text
TableScan
Filter
Projection
InsertPlan
UpdatePlan
DeletePlan
CreateTablePlan
```

Example:

```sql
SELECT name FROM students WHERE cgpa > 8.0
```

becomes conceptually:

```text
Projection
    │
    ▼
Filter
    │
    ▼
TableScan
```

The planner is intentionally independent from execution. This architecture prepares JugaadDB for query optimization.

---

# 13. Executor

The executor runs execution plans.

Supported operations:

```text
Projection
InsertPlan
UpdatePlan
DeletePlan
CreateTablePlan
```

The executor also performs SQL semantic validation such as unknown column, duplicate column, invalid condition, invalid expression, and invalid table handling.

Low-level `ValueError` and `TypeError` exceptions are converted into SQL execution errors where appropriate.

---

# 14. Structured Results

Phase 2 introduces two result structures.

## 14.1 QueryResult

Used for row-returning queries.

It contains:

```text
columns
rows
query_type
```

It also provides row count, list conversion, iteration, and indexing.

## 14.2 CommandResult

Used for commands such as INSERT, UPDATE, DELETE, and CREATE TABLE.

It contains:

```text
affected_rows
query_type
```

---

# 15. SQL Error System

The SQL error hierarchy is:

```text
SQLError
├── SQLSyntaxError
├── SQLExecutionError
└── SQLPlanningError
```

The purpose is to separate SQL-layer errors from generic Python exceptions.

---

# 16. Schema Semantics Through SQL

SQL execution does not bypass schema rules.

Example:

```sql
CREATE TABLE students (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL
)
```

Then:

```sql
INSERT INTO students (id) VALUES (1)
```

is rejected because `name` is required.

Similarly:

```sql
INSERT INTO students (id, name)
VALUES ('wrong', 'Sayman')
```

is rejected because `id` expects INTEGER.

Duplicate primary keys and UNIQUE values are also rejected.

The validation chain is:

```text
SQL Layer
    ↓
Executor
    ↓
Table Layer
    ↓
Schema Layer
```

---

# 17. Integration Through Database.execute()

The SQL interface is exposed through:

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

---

# 18. Testing Strategy

Phase 2 was developed incrementally.

Final checkpoint:

```text
191 passed
0 failed
```

Tests cover lexer behavior, string handling, escape sequences, numeric validation, parser behavior, AST construction, query planning, SQL execution, end-to-end integration, persistence, schema semantics, NULL, NOT NULL, UNIQUE, PRIMARY KEY, duplicate columns, unknown columns, invalid SQL errors, AND, OR, comparison operators, projection, UPDATE, DELETE, and affected-row counts.

---

# 19. What Was Achieved

Before Phase 2:

```text
Python API
    ↓
Database
    ↓
Table
```

After Phase 2:

```text
SQL
 ↓
Lexer
 ↓
Parser
 ↓
AST
 ↓
Planner
 ↓
Executor
 ↓
Database
 ↓
Table
 ↓
Storage
```

This is the primary architectural achievement of Phase 2.

---

# 20. Real-World Analogy

Consider the request:

> "Show me students whose CGPA is greater than 8."

The request must first be understood before the data can be retrieved.

Conceptually:

```text
Request
   ↓
Understand words
   ↓
Understand structure
   ↓
Create a plan
   ↓
Perform operation
   ↓
Return result
```

JugaadDB follows a similar sequence:

```text
SQL
 ↓
Lexer
 ↓
Parser
 ↓
AST
 ↓
Planner
 ↓
Executor
 ↓
Result
```

---

# 21. Phase 2 Limitation

The SQL executor currently works through the existing table abstraction and transitional storage implementation.

The physical Record Manager and slotted-page infrastructure created earlier are not yet the complete SQL execution backend.

This is intentional. The project is being built incrementally so each subsystem can be tested before deep integration.

---

# 22. Phase 3 Requirement

A database that scans every row for every query becomes inefficient as the dataset grows.

Suppose a table contains:

```text
1,000,000 rows
```

and the query is:

```sql
SELECT * FROM students WHERE id = 950000
```

A full table scan may inspect a large number of records.

An index can provide a more direct lookup path.

The intended architecture is:

```text
SQL Query
    ↓
Planner
    ↓
Does useful index exist?
   / \
 yes  no
  ↓    ↓
Index  Table
Scan   Scan
  \    /
   Result
```

---

# 23. Phase 3 Preview

Phase 3 will focus on Indexing and Query Performance.

Planned components:

```text
Index abstraction
Index Manager
B+Tree / B-Tree style structure
Persistent indexes
CREATE INDEX
Index insertion
Index deletion
Index update
Index lookup
Planner integration
Index Scan
Performance comparison
```

The goal is to allow JugaadDB to locate useful records through indexes instead of always scanning the entire table.

---

# 24. Complete Roadmap

```text
PHASE 1
Persistence + Schema + CRUD
        ✅

PHASE 1.5
Physical Record Storage
        ✅

PHASE 2
SQL Engine
        ✅
191/191 tests

PHASE 3
Indexing + Query Performance
        🚀

PHASE 4
Transactions + WAL + Recovery
        ⏳

PHASE 5
NoSQL Document + Key-Value Engine
        ⏳

PHASE 6
Security + RBAC + Encryption + Audit
        ⏳

PHASE 7
GUI + Customization + Optional Cloud Demo
        ⏳
```

---

# 25. Conclusion

Phase 2 successfully establishes the SQL layer of JugaadDB.

The database can now accept SQL text and process it through multiple internal stages:

```text
Lexer
Parser
AST
Planner
Executor
```

The phase supports SELECT, INSERT, UPDATE, DELETE, CREATE TABLE, filtering, comparison operators, AND/OR expressions, schema constraints, structured results, SQL-specific errors, and end-to-end execution.

The final automated test result is:

```text
191 passed
```

This provides a stable foundation for Phase 3.

The next engineering challenge is indexing: allowing JugaadDB to locate data efficiently instead of depending entirely on full table scans.

---

## Phase 2 Final Status

```text
Status: COMPLETE

Tests:
191 passed
0 failed

Next:
PHASE 3 — INDEXING & QUERY PERFORMANCE
```