# csv_reporter_config.py
# -*- coding: utf-8 -*-
"""
csv_reporter_config.py
Container for SQL queries & CSV configurations with granular getter/setter,
catalog functions, loading from JSON files, and a convenience constructor.

All human-readable strings are referenced via language labels and resolved
through the global language service to keep code text-free and translatable.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Any

from language_service import get_language  # global LanguageCatalog accessor


class CsvReporterConfig:
    def __init__(self) -> None:
        # Label -> SQL string
        self._queries: Dict[str, str] = {}
        # Label -> CSV config dict
        self._csv_configs: Dict[str, Dict[str, Any]] = {}

    # -------------------- QUERIES: setter / getter / catalog --------------------
    def set_query(self, label: str, sql: str, *, overwrite: bool = True) -> None:
        """Add or replace an SQL query under a label. overwrite=False prevents replacing."""
        if not isinstance(sql, str) or not sql.strip():
            # Use localized error text
            msg = get_language().get_text("ERR_SQL_EMPTY")
            raise ValueError(msg)
        if not overwrite and label in self._queries:
            return
        self._queries[label] = sql

    def get_query(self, label: str) -> str:
        """Return the SQL string for a label or raise KeyError if missing."""
        try:
            return self._queries[label]
        except KeyError as exc:
            msg = get_language().fmt("ERR_UNKNOWN_QUERY_LABEL", q_label=label)
            raise KeyError(msg) from exc

    def list_query_labels(self) -> list[str]:
        """Return a sorted list of all query labels."""
        return sorted(self._queries.keys())

    # ---------------- CSV CONFIGS: setter / getter / catalog -------------------
    def set_csv_config(self, label: str, cfg: Dict[str, Any], *, overwrite: bool = True) -> None:
        """Add or replace a CSV config under a label (with validation/normalization)."""
        if not isinstance(cfg, dict):
            msg = get_language().get_text("ERR_CSV_CONFIG_TYPE")
            raise ValueError(msg)
        if not overwrite and label in self._csv_configs:
            return
        self._csv_configs[label] = self._normalize_csv_config(cfg)

    def get_csv_config(self, label: str) -> Dict[str, Any]:
        """Return the CSV config dict for a label or raise KeyError if missing."""
        try:
            return self._csv_configs[label]
        except KeyError as exc:
            msg = get_language().fmt("ERR_UNKNOWN_CSV_CONFIG_LABEL", c_label=label)
            raise KeyError(msg) from exc

    def list_csv_config_labels(self) -> list[str]:
        """Return a sorted list of all CSV config labels."""
        return sorted(self._csv_configs.keys())

    # -------------------------- Load from JSON files ---------------------------
    def load_queries_from_file(self, file_path: str | Path, *, overwrite: bool = True) -> int:
        """
        Load queries from a JSON file (Dict[str, str]) and insert them.
        Returns the number of imported/overwritten entries.
        """
        data = self._load_json_dict(file_path)
        count = 0
        for k, v in data.items():
            if not isinstance(k, str) or not isinstance(v, str):
                msg = get_language().fmt(
                    "ERR_INVALID_QUERY_ENTRY",
                    key_type=type(k).__name__,
                    value_type=type(v).__name__,
                )
                raise ValueError(msg)
            existed = k in self._queries
            if not existed or overwrite:
                self._queries[k] = v
                count += 1
        return count

    def load_csv_configs_from_file(self, file_path: str | Path, *, overwrite: bool = True) -> int:
        """
        Load CSV configs from a JSON file (Dict[str, Dict]) and insert them.
        Returns the number of imported/overwritten entries.
        """
        data = self._load_json_dict(file_path)
        count = 0
        for k, v in data.items():
            if not isinstance(k, str) or not isinstance(v, dict):
                msg = get_language().fmt(
                    "ERR_INVALID_CSV_ENTRY",
                    key_type=type(k).__name__,
                    value_type=type(v).__name__,
                )
                raise ValueError(msg)
            existed = k in self._csv_configs
            if not existed or overwrite:
                self._csv_configs[k] = self._normalize_csv_config(v)
                count += 1
        return count

    # --------------------- Convenience constructor -----------------------------
    @classmethod
    def from_files(cls,
                   queries_path: str | Path,
                   csv_configs_path: str | Path,
                   *,
                   overwrite: bool = True) -> "CsvReporterConfig":
        """
        Build a CsvReporterConfig by loading both queries and CSV configs from files.
        Both JSON files must contain a top-level object (dict).
        """
        inst = cls()
        inst.load_queries_from_file(queries_path, overwrite=overwrite)
        inst.load_csv_configs_from_file(csv_configs_path, overwrite=overwrite)
        return inst

    # ------------------------------ Internals ----------------------------------
    @staticmethod
    def _load_json_dict(file_path: str | Path) -> Dict[str, Any]:
        p = Path(file_path)
        if not p.exists():
            msg = get_language().fmt("ERR_FILE_NOT_FOUND", path=str(p))
            raise FileNotFoundError(msg)
        with p.open("r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            msg = get_language().get_text("ERR_JSON_MUST_BE_OBJECT")
            raise ValueError(msg)
        return data

    @staticmethod
    def _normalize_csv_config(cfg: Dict[str, Any]) -> Dict[str, Any]:
        """
        Set defaults & normalize 'quoting' (as string, e.g. 'QUOTE_MINIMAL').
        Enforce basic keys, pass through extra keys as-is.
        """
        out = dict(cfg)  # shallow copy
        out.setdefault("delimiter", ";")
        out.setdefault("quotechar", '"')
        out.setdefault("quoting", "QUOTE_MINIMAL")  # QUOTE_MINIMAL | QUOTE_ALL | QUOTE_NONNUMERIC | QUOTE_NONE
        out.setdefault("decimal", ".")
        out.setdefault("encoding", "utf-8")
        out.setdefault("header", True)
        out.setdefault("missing", "")
        out.setdefault("geometry_format", "WKT")

        # light validation
        if not isinstance(out["delimiter"], str) or len(out["delimiter"]) != 1:
            raise ValueError(get_language().get_text("ERR_DELIMITER_INVALID"))
        if not isinstance(out["quotechar"], str) or len(out["quotechar"]) != 1:
            raise ValueError(get_language().get_text("ERR_QUOTECHAR_INVALID"))
        if out["quoting"] not in {"QUOTE_MINIMAL", "QUOTE_ALL", "QUOTE_NONNUMERIC", "QUOTE_NONE"}:
            raise ValueError(get_language().get_text("ERR_QUOTING_INVALID"))
        if out["decimal"] not in {".", ","}:
            raise ValueError(get_language().get_text("ERR_DECIMAL_INVALID"))

        return out
    