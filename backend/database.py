import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_PATH = os.path.join(BASE_DIR, "careline.db")

def get_connection():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def create_tables():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS admins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            department TEXT,
            doctor_rating INTEGER,
            cleanliness_rating INTEGER,
            service_rating INTEGER,
            comments TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    feedback_columns = {
        row["name"] for row in cursor.execute("PRAGMA table_info(feedback)")
    }
    for column, definition in (
        ("patient_name", "TEXT NOT NULL DEFAULT ''"),
        ("ratings_json", "TEXT NOT NULL DEFAULT '{}'"),
        ("created_at", "TEXT NOT NULL DEFAULT ''"),
        ("sentiment", "TEXT NOT NULL DEFAULT 'Neutral'"),
        ("sentiment_score", "REAL NOT NULL DEFAULT 0"),
        ("is_demo", "INTEGER NOT NULL DEFAULT 0"),
    ):
        if column not in feedback_columns:
            cursor.execute(f"ALTER TABLE feedback ADD COLUMN {column} {definition}")

    conn.commit()
    conn.close()
    print("CARELINE database created successfully!")

if __name__ == "__main__":
    create_tables()
    
