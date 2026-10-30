import os
import sqlite3
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "cooperative.db")

DEFAULT_COOPERATIVE_ID = 1
DEFAULT_COOPERATIVE_NAME = "General Cooperative Society"


def get_connection():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def _column_names(connection, table_name):
    rows = connection.execute(
        f"PRAGMA table_info({table_name})"
    ).fetchall()
    return {row["name"] for row in rows}


def _ensure_column(connection, table_name, column_name, definition):
    existing = _column_names(connection, table_name)
    if column_name not in existing:
        connection.execute(
            f"ALTER TABLE {table_name} ADD COLUMN {column_name} {definition}"
        )


def initialize_database():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS knowledge (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question TEXT NOT NULL,
            answer TEXT NOT NULL,
            language TEXT NOT NULL,
            category TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS enquiries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cooperative_id INTEGER NOT NULL DEFAULT 1,
            cooperative_name TEXT NOT NULL DEFAULT 'General Cooperative Society',
            name TEXT NOT NULL,
            question TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'Pending',
            reply TEXT NOT NULL DEFAULT '',
            replied_at TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            language TEXT NOT NULL,
            answer TEXT NOT NULL DEFAULT '',
            date TEXT NOT NULL
        )
    """)

    # Migrate an existing cooperative.db safely when older schema versions are present.
    _ensure_column(connection, "enquiries", "cooperative_id", "INTEGER NOT NULL DEFAULT 1")
    _ensure_column(connection, "enquiries", "cooperative_name", "TEXT NOT NULL DEFAULT 'General Cooperative Society'")
    _ensure_column(connection, "enquiries", "reply", "TEXT NOT NULL DEFAULT ''")
    _ensure_column(connection, "enquiries", "replied_at", "TEXT")
    _ensure_column(connection, "enquiries", "created_at", "TEXT NOT NULL DEFAULT ''")
    _ensure_column(connection, "enquiries", "updated_at", "TEXT NOT NULL DEFAULT ''")
    _ensure_column(connection, "enquiries", "answer", "TEXT NOT NULL DEFAULT ''")
    _ensure_column(connection, "enquiries", "date", "TEXT NOT NULL DEFAULT ''")

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    connection.execute(
        "UPDATE enquiries SET created_at = ? WHERE created_at = '' OR created_at IS NULL",
        (now,),
    )
    connection.execute(
        "UPDATE enquiries SET updated_at = created_at WHERE updated_at = '' OR updated_at IS NULL",
    )
    connection.execute(
        "UPDATE enquiries SET date = created_at WHERE date = '' OR date IS NULL",
    )
    connection.execute(
        "UPDATE enquiries SET answer = reply WHERE (answer = '' OR answer IS NULL) AND reply IS NOT NULL AND reply <> ''"
    )
    connection.execute(
        "UPDATE enquiries SET reply = answer WHERE (reply = '' OR reply IS NULL) AND answer IS NOT NULL AND answer <> ''"
    )

    connection.commit()
    connection.close()


# -------------------- Knowledge --------------------

def get_all_knowledge():
    connection = get_connection()
    rows = connection.execute("""
        SELECT id, question, answer, language, category
        FROM knowledge
        ORDER BY id DESC
    """).fetchall()
    connection.close()
    return [dict(row) for row in rows]


def get_knowledge(item_id):
    connection = get_connection()
    row = connection.execute("""
        SELECT id, question, answer, language, category
        FROM knowledge
        WHERE id = ?
    """, (item_id,)).fetchone()
    connection.close()
    return dict(row) if row else None


def add_knowledge(question, answer, language, category):
    connection = get_connection()
    cursor = connection.execute("""
        INSERT INTO knowledge (question, answer, language, category)
        VALUES (?, ?, ?, ?)
    """, (question, answer, language, category))
    connection.commit()
    new_id = cursor.lastrowid
    connection.close()
    return new_id


def update_knowledge(item_id, question, answer, language, category):
    connection = get_connection()
    cursor = connection.execute("""
        UPDATE knowledge
        SET question = ?, answer = ?, language = ?, category = ?
        WHERE id = ?
    """, (question, answer, language, category, item_id))
    connection.commit()
    updated = cursor.rowcount > 0
    connection.close()
    return updated


def delete_knowledge(item_id):
    connection = get_connection()
    cursor = connection.execute(
        "DELETE FROM knowledge WHERE id = ?",
        (item_id,),
    )
    connection.commit()
    deleted = cursor.rowcount > 0
    connection.close()
    return deleted


def search_knowledge(keyword="", language="", category=""):
    connection = get_connection()
    query = """
        SELECT id, question, answer, language, category
        FROM knowledge
        WHERE 1 = 1
    """
    params = []

    if keyword:
        query += """
            AND (question LIKE ? OR answer LIKE ? OR category LIKE ?)
        """
        value = f"%{keyword}%"
        params.extend([value, value, value])

    if language:
        query += " AND language = ?"
        params.append(language)

    if category:
        query += " AND category = ?"
        params.append(category)

    query += " ORDER BY id DESC"
    rows = connection.execute(query, params).fetchall()
    connection.close()
    return [dict(row) for row in rows]


# -------------------- Enquiries --------------------

def get_all_enquiries():
    connection = get_connection()
    rows = connection.execute("""
        SELECT
            id,
            cooperative_id,
            cooperative_name,
            name,
            question,
            status,
            reply,
            answer,
            language,
            created_at,
            updated_at,
            replied_at,
            date
        FROM enquiries
        ORDER BY id DESC
    """).fetchall()
    connection.close()
    return [dict(row) for row in rows]


def get_enquiry(enquiry_id):
    connection = get_connection()
    row = connection.execute("""
        SELECT
            id,
            cooperative_id,
            cooperative_name,
            name,
            question,
            status,
            reply,
            answer,
            language,
            created_at,
            updated_at,
            replied_at,
            date
        FROM enquiries
        WHERE id = ?
    """, (enquiry_id,)).fetchone()
    connection.close()
    return dict(row) if row else None


def add_enquiry(
    name,
    question,
    language="English",
    cooperative_id=DEFAULT_COOPERATIVE_ID,
    cooperative_name=DEFAULT_COOPERATIVE_NAME,
):
    connection = get_connection()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor = connection.execute("""
        INSERT INTO enquiries (
            cooperative_id,
            cooperative_name,
            name,
            question,
            status,
            reply,
            replied_at,
            created_at,
            updated_at,
            language,
            answer,
            date
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        cooperative_id,
        cooperative_name,
        name or "Anonymous",
        question,
        "Pending",
        "",
        None,
        now,
        now,
        language,
        "",
        now,
    ))

    connection.commit()
    new_id = cursor.lastrowid
    connection.close()
    return new_id


def answer_enquiry(enquiry_id, answer):
    connection = get_connection()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor = connection.execute("""
        UPDATE enquiries
        SET
            answer = ?,
            reply = ?,
            status = 'Answered',
            replied_at = ?,
            updated_at = ?
        WHERE id = ?
    """, (answer, answer, now, now, enquiry_id))

    connection.commit()
    updated = cursor.rowcount > 0
    connection.close()
    return updated


def delete_enquiry(enquiry_id):
    connection = get_connection()
    cursor = connection.execute(
        "DELETE FROM enquiries WHERE id = ?",
        (enquiry_id,),
    )
    connection.commit()
    deleted = cursor.rowcount > 0
    connection.close()
    return deleted


def search_enquiries(keyword="", status=""):
    connection = get_connection()
    query = """
        SELECT
            id,
            cooperative_id,
            cooperative_name,
            name,
            question,
            status,
            reply,
            answer,
            language,
            created_at,
            updated_at,
            replied_at,
            date
        FROM enquiries
        WHERE 1 = 1
    """
    params = []

    if keyword:
        query += """
            AND (
                name LIKE ?
                OR question LIKE ?
                OR language LIKE ?
                OR answer LIKE ?
                OR reply LIKE ?
            )
        """
        value = f"%{keyword}%"
        params.extend([value] * 5)

    if status:
        query += " AND status = ?"
        params.append(status)

    query += " ORDER BY id DESC"

    rows = connection.execute(query, params).fetchall()
    connection.close()
    return [dict(row) for row in rows]


# -------------------- Statistics --------------------

def get_knowledge_count():
    connection = get_connection()
    value = connection.execute("SELECT COUNT(*) AS total FROM knowledge").fetchone()["total"]
    connection.close()
    return value


def get_enquiry_count():
    connection = get_connection()
    value = connection.execute("SELECT COUNT(*) AS total FROM enquiries").fetchone()["total"]
    connection.close()
    return value


def get_pending_enquiry_count():
    connection = get_connection()
    value = connection.execute(
        "SELECT COUNT(*) AS total FROM enquiries WHERE status = 'Pending'"
    ).fetchone()["total"]
    connection.close()
    return value


def get_answered_enquiry_count():
    connection = get_connection()
    value = connection.execute(
        "SELECT COUNT(*) AS total FROM enquiries WHERE status = 'Answered'"
    ).fetchone()["total"]
    connection.close()
    return value


initialize_database()


if __name__ == "__main__":
    print("Database initialized:", DB_PATH)
    print("Knowledge records:", get_knowledge_count())
    print("Enquiry records:", get_enquiry_count())
    print("Pending enquiries:", get_pending_enquiry_count())
    print("Answered enquiries:", get_answered_enquiry_count())
