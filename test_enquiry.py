import traceback
import sqlite3
from database import add_enquiry, get_all_enquiries


print("=" * 60)
print("ENQUIRY DATABASE TEST")
print("=" * 60)

try:

    print("\n1. Testing database connection...")

    connection = sqlite3.connect("cooperative.db")
    cursor = connection.cursor()

    print("Database connection: SUCCESS")


    print("\n2. Checking enquiries table...")

    cursor.execute("PRAGMA table_info(enquiries)")
    columns = cursor.fetchall()

    for column in columns:
        print(
            f"Column: {column[1]} | "
            f"Type: {column[2]} | "
            f"NotNull: {column[3]} | "
            f"Default: {column[4]}"
        )

    connection.close()


    print("\n3. Testing add_enquiry()...")

    enquiry_id = add_enquiry(
        "Test User",
        "What is a cooperative society?",
        "English"
    )

    print("SUCCESS!")
    print("New enquiry ID:", enquiry_id)


    print("\n4. Reading enquiries...")

    enquiries = get_all_enquiries()

    print("Total enquiries:", len(enquiries))

    for enquiry in enquiries[:5]:
        print(enquiry)


except Exception as error:

    print("\n" + "=" * 60)
    print("ENQUIRY TEST FAILED")
    print("=" * 60)

    print("\nERROR TYPE:")
    print(type(error).__name__)

    print("\nERROR MESSAGE:")
    print(str(error))

    print("\nFULL TRACEBACK:")
    traceback.print_exc()


print("\nTest completed.")