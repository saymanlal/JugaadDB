from jugaaddb.core.database import Database

db = Database.open("college.jdb")

students = db.table("students")

print("Initial:")
for row in students.select_all():
    print(row)

print("\nUpdating Sayman...")

updated = students.update(
    {"id": 1},
    {"cgpa": 9.0}
)

print("Rows updated:", updated)

print("\nAfter UPDATE:")
for row in students.select_all():
    print(row)

print("\nDeleting Rahul...")

deleted = students.delete(
    {"id": 2}
)

print("Rows deleted:", deleted)

print("\nAfter DELETE:")
for row in students.select_all():
    print(row)