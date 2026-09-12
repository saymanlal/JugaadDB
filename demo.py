from jugaaddb.core.database import Database

db = Database.open("college.jdb")

students = db.table("students")

print("Students:")

for row in students.select_all():
    print(row)