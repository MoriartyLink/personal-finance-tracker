# database.py
import os
import sqlite3

# Get absolute path of the current directory
APP_DIR = os.path.dirname(os.path.abspath(__file__))

# Database file path (in the same folder as your .py files)
DB_FILE = os.path.join(APP_DIR, "expenses.db")
print("DB FILE PATH:", DB_FILE)
print("Exists?", os.path.exists(DB_FILE))

def init_db():
    if not os.path.exists(DB_FILE):
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                amount REAL,
                category TEXT,
                date TEXT
            )
        """)
        conn.commit()
        conn.close()
    else:
        print("Database file found:", DB_FILE)

def get_db_connection():
    return sqlite3.connect(DB_FILE)
