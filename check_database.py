from database import initialize_database, get_all_knowledge


# =========================================================
# CHECK DATABASE
# =========================================================

def check_database():

    print("=" * 60)
    print("COOPERATIVE CHATBOT - DATABASE CHECK")
    print("=" * 60)

    # -----------------------------------------------------
    # Step 1: Initialize Database
    # -----------------------------------------------------

    try:

        initialize_database()

        print("[OK] Database initialized successfully.")

    except Exception as error:

        print("[ERROR] Database initialization failed.")
        print("Reason:", error)

        return


    # -----------------------------------------------------
    # Step 2: Read Knowledge Records
    # -----------------------------------------------------

    try:

        records = get_all_knowledge()

    except Exception as error:

        print("[ERROR] Could not read knowledge records.")
        print("Reason:", error)

        return


    # -----------------------------------------------------
    # Step 3: Display Total Records
    # -----------------------------------------------------

    print()

    print(
        f"Total knowledge records: {len(records)}"
    )

    print()


    # -----------------------------------------------------
    # Step 4: Check Empty Database
    # -----------------------------------------------------

    if not records:

        print(
            "No knowledge records found."
        )

        print()
        print(
            "Please run migrate_data.py first."
        )

        return


    # -----------------------------------------------------
    # Step 5: Display All Records
    # -----------------------------------------------------

    print("-" * 60)

    for record in records:

        print(
            f"ID       : {record['id']}"
        )

        print(
            f"Question : {record['question']}"
        )

        print(
            f"Answer   : {record['answer']}"
        )

        print(
            f"Language : {record['language']}"
        )

        print(
            f"Category : {record['category']}"
        )

        print("-" * 60)


    # -----------------------------------------------------
    # Step 6: Database Summary
    # -----------------------------------------------------

    print()

    print("=" * 60)
    print("DATABASE SUMMARY")
    print("=" * 60)

    print(
        f"Total Records : {len(records)}"
    )

    print(
        "Status        : Database is working"
    )

    print("=" * 60)

    print()
    print(
        "Database check completed successfully."
    )


# =========================================================
# MAIN
# =========================================================

if __name__ == "__main__":

    check_database()