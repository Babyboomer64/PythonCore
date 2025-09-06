# server/app/lifecycle.py
# Startup/shutdown orchestration: language init, config loading, DB adapter

import sqlite3
from pathlib import Path
from fastapi import FastAPI
from datetime import datetime

from language_service import init_language
from csv_reporter_config import CsvReporterConfig
from sqlite_adapter import SQLiteAdapter


class AppState:
    adapter: SQLiteAdapter | None = None
    cfg: CsvReporterConfig | None = None
    start_time: datetime | None = None


state = AppState()


def on_startup(app: FastAPI, settings) -> None:
    # Initialize language (domain-aware)
    init_language(
        settings.MESSAGES_PATH,
        default_lang=settings.DEFAULT_LANG,
        allowed_langs=settings.ALLOWED_LANGS,
        context=settings.LANGUAGE_CONTEXT,
        domain_aware=True,
    )

    # Load reporter configs (queries + csv configs)
    state.cfg = CsvReporterConfig.from_files(
        settings.QUERIES_PATH,
        settings.CSV_CONFIGS_PATH,
        overwrite=True,
    )

    # Connect SQLite (demo)
    # Tip: if DB doesn't exist, examples/init_sqlite_db.py can create/populate it.
    # We still connect here; if tables are missing, CSV routes can handle errors.
    db_path = Path(settings.SQLITE_DB_PATH)
    conn = sqlite3.connect(str(db_path), check_same_thread=False)
    state.adapter = SQLiteAdapter(conn)
    state.start_time = datetime.utcnow()


def on_shutdown(app: FastAPI) -> None:
    if state.adapter and getattr(state.adapter, "conn", None):
        try:
            state.adapter.conn.close()
        except Exception:
            pass