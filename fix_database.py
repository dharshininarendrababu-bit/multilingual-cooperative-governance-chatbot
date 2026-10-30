import sqlite3
import os
from datetime import datetime


# =========================================================
# DATABASE PATH
# =========================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DB_PATH = os.path.join(
    BASE_DIR,
    "cooperative.db"
)


# =========================================================
# DATABASE FIX
# =========================================================

def fix_database():

    print("\n" + "=" * 60)
    print("       COOPERATIVE CHATBOT DATABASE FIX")
    print("=" * 60)

    print("\nDatabase:")
    print(DB_PATH)


    # -----------------------------------------------------
    # CHECK DATABASE FILE
    # -----------------------------------------------------

    if not os.path.exists(DB_PATH):

        print("\nERROR: cooperative.db not found!")
        return


    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()


    try:

        # -------------------------------------------------
        # CHECK ENQUIRIES TABLE
        # -------------------------------------------------

        cursor.execute(
            "PRAGMA table_info(enquiries)"
        )

        columns = cursor.fetchall()

        existing_columns = [
            column[1]
            for column in columns
        ]


        print("\nCurrent enquiries columns:")

        for column in existing_columns:

            print(" -", column)


        # -------------------------------------------------
        # ADD LANGUAGE
        # -------------------------------------------------

        if "language" not in existing_columns:

            print("\nAdding missing column: language")

            cursor.execute("""
                ALTER TABLE enquiries
                ADD COLUMN language TEXT DEFAULT 'English'
            """)

            print("✓ language added")

        else:

            print("\n✓ language already exists")


        # -------------------------------------------------
        # ADD ANSWER
        # -------------------------------------------------

        if "answer" not in existing_columns:

            print("\nAdding missing column: answer")

            cursor.execute("""
                ALTER TABLE enquiries
                ADD COLUMN answer TEXT DEFAULT ''
            """)

            print("✓ answer added")

        else:

            print("✓ answer already exists")


        # -------------------------------------------------
        # ADD DATE
        # -------------------------------------------------

        if "date" not in existing_columns:

            print("\nAdding missing column: date")

            cursor.execute("""
                ALTER TABLE enquiries
                ADD COLUMN date TEXT DEFAULT ''
            """)

            print("✓ date added")

        else:

            print("✓ date already exists")


        # -------------------------------------------------
        # COMMIT CHANGES
        # -------------------------------------------------

        connection.commit()


        # -------------------------------------------------
        # UPDATE EMPTY DATE VALUES
        # -------------------------------------------------

        cursor.execute("""
            UPDATE enquiries
            SET date = ?
            WHERE date IS NULL OR date = ''
        """, (
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        ))


        connection.commit()


        # -------------------------------------------------
        # UPDATE EMPTY ANSWER VALUES
        # -------------------------------------------------

        cursor.execute("""
            UPDATE enquiries
            SET answer = ''
            WHERE answer IS NULL
        """)

        connection.commit()


        # -------------------------------------------------
        # UPDATE EMPTY LANGUAGE VALUES
        # -------------------------------------------------

        cursor.execute("""
            UPDATE enquiries
            SET language = 'English'
            WHERE language IS NULL OR language = ''
        """)

        connection.commit()


        # -------------------------------------------------
        # FINAL TABLE CHECK
        # -------------------------------------------------

        cursor.execute(
            "PRAGMA table_info(enquiries)"
        )

        updated_columns = cursor.fetchall()


        final_columns = [
            column[1]
            for column in updated_columns
        ]


        print("\n" + "=" * 60)
        print("       UPDATED ENQUIRIES TABLE")
        print("=" * 60)


        for column in updated_columns:

            print(
                f" - {column[1]} ({column[2]})"
            )


        # -------------------------------------------------
        # REQUIRED COLUMNS
        # -------------------------------------------------

        required_columns = [
            "id",
            "name",
            "question",
            "language",
            "answer",
            "status",
            "date"
        ]


        print("\n" + "=" * 60)
        print("       REQUIRED COLUMN CHECK")
        print("=" * 60)


        missing_columns = []


        for column in required_columns:

            if column in final_columns:

                print(
                    f" ✓ {column}"
                )

            else:

                print(
                    f" ✗ {column} MISSING"
                )

                missing_columns.append(column)


        # -------------------------------------------------
        # FINAL RESULT
        # -------------------------------------------------

        print("\n" + "=" * 60)


        if len(missing_columns) == 0:

            print(
                "DATABASE FIX COMPLETED SUCCESSFULLY!"
            )

            print(
                "All required enquiry columns are available."
            )

        else:

            print(
                "WARNING: Some columns are still missing:"
            )

            for column in missing_columns:

                print(
                    " -", column
                )


        print("=" * 60)


    except sqlite3.Error as error:

        print("\nDATABASE ERROR:")
        print(error)


    finally:

        connection.close()

        print("\nDatabase connection closed.")


# =========================================================
# PROGRAM START
# =========================================================

if __name__ == "__main__":

    fix_database()