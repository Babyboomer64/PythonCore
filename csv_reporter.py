# csv_reporter.py
# -*- coding: utf-8 -*-
"""
csv_reporter.py
Generic, reusable CSV reporter that:
- pulls SQL & CSV settings from CsvReporterConfig,
- executes queries via a pluggable DB adapter (Protocol),
- writes CSV with flexible formatting (delimiter, quoting, encoding, decimal, etc.),
- resolves human-readable messages via the global language_service.

NOTE:
- Initialize the language service once in your application startup:
    from language_service import init_language
    init_language("messages.json", default_lang="DE", allowed_langs={"DE", "EN"})

- Provide a DB adapter that implements the DBAdapter Protocol below.
"""

from __future__ import annotations

import csv
import os
from datetime import datetime, date
from decimal import Decimal
from pathlib import Path
from typing import Protocol, Iterable, Optional, Dict, Any, Tuple

from language_service import get_language
from csv_reporter_config import CsvReporterConfig


# --------------------------------------------------------------------------- #
# DB Adapter Protocol
# --------------------------------------------------------------------------- #
class DBAdapter(Protocol):
    """
    Minimal interface a DB adapter must implement.
    It must execute SQL and return (headers, rows_iterable).

    - headers: list[str] with column names
    - rows:    iterable of tuples, fetched in chunks if desired
    """

    def execute(
        self,
        sql: str,
        params: Optional[Dict[str, Any]] = None,
        arraysize: int = 10_000,
    ) -> Tuple[list[str], Iterable[tuple]]:
        ...


# --------------------------------------------------------------------------- #
# CSV Reporter
# --------------------------------------------------------------------------- #
class CsvReporter:
    """
    CSV Reporter that uses:
      - a DB adapter (for executing SQL),
      - a CsvReporterConfig (for SQL statements and CSV configs),
      - the global language_service for all messages.

    Usage pattern (example):
        reporter = CsvReporter(adapter=my_adapter, config=my_cfg)
        path = reporter.run(
            select_label="LPIS_POPULATION",
            out_path="/tmp/out.csv",
            params={"p_city": "Cologne"},
            config_label="NDL_STRICT",
            arraysize=20_000
        )
    """

    def __init__(self, adapter: DBAdapter, config: CsvReporterConfig) -> None:
        self._db = adapter
        self._cfg = config

    # ------------------------------ public API ------------------------------ #
    def run(
        self,
        *,
        select_label: str,
        out_path: str,
        params: Optional[Dict[str, Any]] = None,
        config_label: str = "MS_STANDARD",
        arraysize: int = 10_000,
    ) -> str:
        """
        Execute the query identified by `select_label`, stream rows,
        and write a CSV file to `out_path` using the CSV config identified by `config_label`.
        """
        # Resolve SQL and CSV config (raises localized KeyError if unknown)
        sql = self._cfg.get_query(select_label)
        csv_cfg = self._cfg.get_csv_config(config_label)

        headers, rows_iter = self._db.execute(sql, params=params or {}, arraysize=arraysize)
        return self._write_csv(headers, rows_iter, out_path, csv_cfg)

    # ------------------------------ internals ------------------------------- #
    def _write_csv(
        self,
        headers: list[str],
        rows: Iterable[tuple],
        out_path: str,
        cfg: Dict[str, Any],
    ) -> str:
        """
        Write CSV with the given headers and row-iterator using cfg.
        cfg keys (normalized by CsvReporterConfig):
          - delimiter (str, 1 char)
          - quotechar (str, 1 char)
          - quoting (str: QUOTE_MINIMAL | QUOTE_ALL | QUOTE_NONNUMERIC | QUOTE_NONE)
          - decimal ('.' or ',')
          - encoding ('utf-8', ...)
          - header (bool)
          - missing (str)
          - geometry_format (str, informational)
        """
        lang = get_language()

        # Prepare filesystem
        out_path = str(out_path)
        out_dir = os.path.dirname(os.path.abspath(out_path)) or "."
        try:
            os.makedirs(out_dir, exist_ok=True)
        except Exception as exc:
            # Label suggestion: ERR_OUTPUT_DIR_CREATE
            msg = lang.fmt("ERR_OUTPUT_DIR_CREATE", path=out_dir, message=str(exc)) \
                  if _has_label(lang, "ERR_OUTPUT_DIR_CREATE") \
                  else f"Failed to create output directory: {out_dir} ({exc})"
            raise OSError(msg) from exc

        # Map quoting string to csv constants
        quoting_name = cfg.get("quoting", "QUOTE_MINIMAL")
        quoting = getattr(csv, quoting_name, csv.QUOTE_MINIMAL)

        try:
            with open(out_path, "w", newline="", encoding=cfg.get("encoding", "utf-8")) as f:
                writer = csv.writer(
                    f,
                    delimiter=cfg.get("delimiter", ";"),
                    quotechar=cfg.get("quotechar", '"'),
                    quoting=quoting,
                )

                if cfg.get("header", True):
                    writer.writerow(headers)

                dec_sep = cfg.get("decimal", ".")
                missing = cfg.get("missing", "")

                for row in rows:
                    out_row = [self._to_cell_value(v, dec_sep, quoting) for v in row]
                    # Replace None placeholders with "missing"
                    out_row = [missing if v is None else v for v in out_row]
                    writer.writerow(out_row)

        except FileNotFoundError as exc:
            # Label suggestion: ERR_FILE_NOT_FOUND (already defined)
            msg = lang.fmt("ERR_FILE_NOT_FOUND", path=out_path) \
                  if _has_label(lang, "ERR_FILE_NOT_FOUND") \
                  else f"File not found: {out_path}"
            raise FileNotFoundError(msg) from exc

        except PermissionError as exc:
            # Label suggestion: ERR_NO_PERMISSION
            msg = lang.fmt("ERR_NO_PERMISSION", path=out_path, message=str(exc)) \
                  if _has_label(lang, "ERR_NO_PERMISSION") \
                  else f"No permission to write file: {out_path} ({exc})"
            raise PermissionError(msg) from exc

        except Exception as exc:
            # Label suggestion: ERR_WRITE_CSV_FAILED
            msg = lang.fmt("ERR_WRITE_CSV_FAILED", path=out_path, message=str(exc)) \
                  if _has_label(lang, "ERR_WRITE_CSV_FAILED") \
                  else f"Failed to write CSV '{out_path}': {exc}"
            raise RuntimeError(msg) from exc

        return out_path

    # Convert DB values to CSV cell values considering decimal and quoting mode
    def _to_cell_value(self, v: Any, dec_sep: str, quoting: int) -> Any:
        """
        Convert a single DB value into a CSV cell value:
        - None stays None (handled later to 'missing')
        - int/float: keep numeric for QUOTE_NONNUMERIC (writer will not quote)
                     otherwise convert to string, force decimal separator if needed
        - Decimal -> float
        - date/datetime -> ISO string
        - LOB-like -> read() if available
        - others -> str()
        """
        if v is None:
            return None

        if isinstance(v, bool):
            # keep bool as numeric 0/1 or as string? choose string by default
            return "1" if v else "0"

        if isinstance(v, (int, float)):
            if quoting == csv.QUOTE_NONNUMERIC:
                # keep as numeric so writer won't quote
                return v
            # stringify and enforce decimal separator if needed
            s = repr(float(v)) if isinstance(v, float) else str(v)
            if dec_sep != ".":
                s = s.replace(".", dec_sep)
            return s

        if isinstance(v, Decimal):
            # route through float to respect QUOTE_NONNUMERIC behavior
            f = float(v)
            if quoting == csv.QUOTE_NONNUMERIC:
                return f
            s = repr(f)
            if dec_sep != ".":
                s = s.replace(".", dec_sep)
            return s

        if isinstance(v, (date, datetime)):
            return v.isoformat(sep=" ")

        if hasattr(v, "read"):
            try:
                return v.read()
            except Exception:
                return str(v)

        return str(v)


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def _has_label(lang_catalog, label: str) -> bool:
    """Return True if the language catalog has the label for its default language."""
    try:
        # We only check existence; do not raise if missing
        lang_catalog.get_text(label, None, default=None)
        return True
    except Exception:
        return False