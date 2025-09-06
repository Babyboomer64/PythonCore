# init_sqlite_db.py
# -*- coding: utf-8 -*-
"""
Creates a small SQLite database with demo data for the CSV reporter.
"""
import sqlite3
from pathlib import Path

DB_PATH = "test.db"

DDL = """
CREATE TABLE IF NOT EXISTS customers (
    customer_id INTEGER PRIMARY KEY,
    name        TEXT NOT NULL,
    city        TEXT NOT NULL,
    created_at  TEXT NOT NULL
);
"""

DEMO_ROWS = [
    (1, "Alice", "Cologne", "2025-09-05 10:00:00"),
    (2, "Bob",   "Vienna",  "2025-09-05 11:00:00"),
    (3, "Cara",  "Cologne", "2025-09-06 08:00:00"),
    (4, "Dave",  "Cologne", "2025-09-06 12:00:00"),
    (5, "Eve",   "Vienna",  "2025-09-06 13:30:00")
]

def main() -> None:
    p = Path(DB_PATH)
    conn = sqlite3.connect(p.as_posix())
    try:
        conn.execute(DDL)
        # idempotent insert for demo: clear and reinsert
        conn.execute("DELETE FROM customers")
        conn.executemany("INSERT INTO customers(customer_id, name, city, created_at) VALUES (?,?,?,?)", DEMO_ROWS)
        conn.commit()
        print(f"SQLite DB ready at: {p.resolve()}")
    finally:
        conn.close()

if __name__ == "__main__":
    main()