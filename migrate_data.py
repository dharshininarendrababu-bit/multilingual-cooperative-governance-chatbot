import json
from database import get_connection, initialize_database


# =========================================================
# MIGRATE DATA.JSON TO DATABASE
# =========================================================

def migrate_data():

    print("=" * 60)
    print("MULTILINGUAL KNOWLEDGE DATA MIGRATION")
    print("=" * 60)

    # Make sure database exists
    initialize_database()

    # Read data.json
    try:

        with open(
            "data.json",
            "r",
            encoding="utf-8"
        ) as file:

            data = json.load(file)

    except FileNotFoundError:

        print("\nERROR: data.json not found.")
        return

    except json.JSONDecodeError as error:

        print(
            "\nERROR: Invalid JSON format."
        )

        print(error)
        return


    connection = get_connection()
    cursor = connection.cursor()

    inserted = 0
    skipped = 0
    failed = 0


    # =====================================================
    # PROCESS RECORDS
    # =====================================================

    for item in data:

        question = str(
            item.get(
                "question",
                ""
            )
        ).strip()

        answer = str(
            item.get(
                "answer",
                ""
            )
        ).strip()

        language = str(
            item.get(
                "language",
                "English"
            )
        ).strip()

        category = str(
            item.get(
                "category",
                "General"
            )
        ).strip()


        # -------------------------------------------------
        # CHECK REQUIRED VALUES
        # -------------------------------------------------

        if not question or not answer:

            failed += 1

            print(
                "SKIPPED - Missing question/answer:",
                question
            )

            continue


        try:

            # -------------------------------------------------
            # DUPLICATE CHECK
            # -------------------------------------------------

            cursor.execute(
                """
                SELECT id
                FROM knowledge
                WHERE question = ?
                  AND language = ?
                """,
                (
                    question,
                    language
                )
            )

            existing = cursor.fetchone()


            if existing:

                skipped += 1

                continue


            # -------------------------------------------------
            # INSERT
            # -------------------------------------------------

            cursor.execute(
                """
                INSERT INTO knowledge
                (
                    question,
                    answer,
                    language,
                    category
                )
                VALUES (?, ?, ?, ?)
                """,
                (
                    question,
                    answer,
                    language,
                    category
                )
            )

            inserted += 1


        except Exception as error:

            failed += 1

            print(
                "FAILED:",
                question
            )

            print(
                "ERROR:",
                error
            )


    connection.commit()
    connection.close()


    # =====================================================
    # RESULT
    # =====================================================

    print("")
    print("=" * 60)
    print("MIGRATION COMPLETED")
    print("=" * 60)

    print(
        "Total JSON records :",
        len(data)
    )

    print(
        "Inserted           :",
        inserted
    )

    print(
        "Skipped duplicates  :",
        skipped
    )

    print(
        "Failed              :",
        failed
    )

    print("=" * 60)


# =========================================================
# PROGRAM START
# =========================================================

if __name__ == "__main__":

    migrate_data()