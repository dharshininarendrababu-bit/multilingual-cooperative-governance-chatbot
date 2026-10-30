import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "cooperative.db")

print("Database:", DB_PATH)

if not os.path.exists(DB_PATH):
    print("ERROR: cooperative.db not found!")
    exit()

connection = sqlite3.connect(DB_PATH)
cursor = connection.cursor()

try:
    # Show table names
    cursor.execute("""
        SELECT name
        FROM sqlite_master
        WHERE type='table'
        ORDER BY name
    """)

    tables = cursor.fetchall()

    print("\nTables:")
    for table in tables:
        print(" -", table[0])

    # Check enquiries table
    print("\nENQUIRIES TABLE STRUCTURE")
    print("=" * 50)

    cursor.execute("PRAGMA table_info(enquiries)")
    columns = cursor.fetchall()

    if not columns:
        print("ERROR: enquiries table does not exist!")
    else:
        for column in columns:
            print(
                "id =", column[0],
                "| name =", column[1],
                "| type =", column[2],
                "| notnull =", column[3],
                "| default =", column[4]
            )

    # Check existing rows
    print("\nEXISTING ENQUIRIES")
    print("=" * 50)

    cursor.execute("SELECT * FROM enquiries")
    rows = cursor.fetchall()

    print("Total rows:", len(rows))

    for row in rows[:10]:
        print(row)

except Exception as error:
    print("\nERROR:", error)

finally:
    connection.close()
    print("\nDatabase connection closed.")
    