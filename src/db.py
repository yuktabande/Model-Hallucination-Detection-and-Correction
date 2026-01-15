import sqlite3

def init_db(path="data/processed/chunks.db"):
    conn = sqlite3.connect(path)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chunks (
            id INTEGER PRIMARY KEY,
            paper_id TEXT,
            chunk TEXT,
            chunk_type TEXT,
            source TEXT,
            year INTEGER,
            authors TEXT,
            venue TEXT,
            page INTEGER,
            metadata TEXT
        );
    """)

    conn.commit()
    return conn