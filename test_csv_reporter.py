# test_csv_reporter.py
# -*- coding: utf-8 -*-
"""
Test app for CsvReporter using a single domain-aware messages.json.

Behavior:
- If no args: print catalogs of available query/config labels (localized headings) and usage.
- Else: run the selected query using SQLite adapter and write CSV.

CLI:
    python test_csv_reporter.py <query_label> <csv_config_label> <out_path> [key=value ...]

Examples:
    python test_csv_reporter.py ALL_CUSTOMERS NDL_STRICT out.csv
    python test_csv_reporter.py CUSTOMERS_BY_CITY NDL_STRICT out_cologne.csv city=Cologne
"""
from __future__ import annotations

import sys
import sqlite3
from pathlib import Path
from typing import Dict

from language_service import (
    init_language, set_language_context, text, fmt, add_domain_file
)
from csv_reporter_config import CsvReporterConfig
from csv_reporter import CsvReporter
from sqlite_adapter import SQLiteAdapter

DB_PATH = "test.db"
MESSAGES_PATH = "messages.json"
QUERIES_PATH = "queries.json"
CSV_CONFIGS_PATH = "csv_configs.json"

def parse_kv_args(args: list[str]) -> Dict[str, str]:
    """Parse key=value pairs from CLI tail into a dict."""
    out: Dict[str, str] = {}
    for a in args:
        if "=" in a:
            k, v = a.split("=", 1)
            out[k.strip()] = v.strip()
    return out

def print_catalogs(cfg: CsvReporterConfig) -> None:
    """Print available query and CSV-config labels with localized headings."""
    print(text("CATALOG_QUERIES_HEADER"))
    q_labels = cfg.list_query_labels()
    if q_labels:
        for lbl in q_labels:
            print(f"  - {lbl}")
    else:
        print(text("CATALOG_EMPTY_LIST"))

    print("\n" + text("CATALOG_CSV_CONFIGS_HEADER"))
    c_labels = cfg.list_csv_config_labels()
    if c_labels:
        for lbl in c_labels:
            print(f"  - {lbl}")
    else:
        print(text("CATALOG_EMPTY_LIST"))

    print("\n" + text("USAGE_TEST_CSV_REPORTER"))
    print(text("EXAMPLES_TEST_CSV_REPORTER"))
    print("")

def main() -> None:
    init_language(
        MESSAGES_PATH,
        default_lang="DE",
        allowed_langs={"DE", "EN"},
        context="GLOBAL.CSV",
        domain_aware=True
    )

    # Load queries & csv configs
    cfg = CsvReporterConfig.from_files(QUERIES_PATH, CSV_CONFIGS_PATH, overwrite=True)

    # No args -> show catalogs
    if len(sys.argv) == 1:
        print_catalogs(cfg)
        sys.exit(0)

    if len(sys.argv) < 4:
        print(text("USAGE_TEST_CSV_REPORTER"))
        sys.exit(1)

    query_label = sys.argv[1]
    csv_label = sys.argv[2]
    out_path = sys.argv[3]
    params = parse_kv_args(sys.argv[4:])

    # DB adapter
    if not Path(DB_PATH).exists():
        # Switch context to DATABASE for DB-specific messages (optional)
        set_language_context("GLOBAL.DATABASE.SQLITE")
        print(fmt("SQLITE_DB_MISSING", path=DB_PATH))
        sys.exit(2)

    conn = sqlite3.connect(DB_PATH)
    adapter = SQLiteAdapter(conn)

    try:
        reporter = CsvReporter(adapter=adapter, config=cfg)
        # Back to CSV context for reporter outputs (optional)
        set_language_context("GLOBAL.CSV")
        out_csv = reporter.run(
            select_label=query_label,
            out_path=out_path,
            params=params,
            config_label=csv_label,
            arraysize=10_000
        )
        print(fmt("CSV_WRITTEN", path=str(Path(out_csv).resolve())))
    finally:
        conn.close()

if __name__ == "__main__":
    main()