# sqlite_adapter.py
# -*- coding: utf-8 -*-
"""
SQLite DB adapter implementing the DBAdapter Protocol expected by CsvReporter.
"""
from __future__ import annotations

import sqlite3
from typing import Optional, Dict, Any, Iterable

class SQLiteAdapter:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self.conn = conn

    def execute(
        self,
        sql: str,
        params: Optional[Dict[str, Any]] = None,
        arraysize: int = 10_000,
    ) -> tuple[list[str], Iterable[tuple]]:
        cur = self.conn.cursor()
        # sqlite3 supports named parameters like :city with dict, pass-through is fine.
        cur.execute(sql, params or {})
        headers = [c[0] for c in cur.description]

        def row_iter():
            try:
                while True:
                    rows = cur.fetchmany(arraysize)
                    if not rows:
                        break
                    for r in rows:
                        yield r
            finally:
                cur.close()

        return headers, row_iter()