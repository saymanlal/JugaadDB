from jugaaddb.core.database import Database
from jugaaddb.core.schema import Column


DB_FILE = "college.jdb"


db = Database.create(DB_FILE)

students = db.create_table(
    "students",
    [
        Column(
            "id",
            "INTEGER",
            primary_key=True,
            nullable=False
        ),
        Column(
            "name",
            "TEXT",
            nullable=False
        ),
        Column(
            "branch",
            "TEXT"
        ),
        Column(
            "cgpa",
            "FLOAT"
        ),
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


print("Students:")
for row in students.select_all():
    print(row)