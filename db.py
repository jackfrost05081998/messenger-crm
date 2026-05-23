import sqlite3

def init_db():

    conn = sqlite3.connect("database.db")
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        psid TEXT PRIMARY KEY,
        first_seen TEXT,
        last_seen TEXT,
        messages_count INTEGER DEFAULT 0
    )
    """)

    conn.commit()
    conn.close()