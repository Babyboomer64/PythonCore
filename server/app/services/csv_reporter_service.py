# server/app/services/csv_reporter_service.py
# Thin service layer to orchestrate CsvReporter with loaded configs/adapters.
# Comments in English (as requested).

from typing import Optional, Dict, Any

from csv_reporter import CsvReporter
from csv_reporter_config import CsvReporterConfig


class CsvService:
    """
    A thin wrapper that composes:
      - a DB adapter (must implement the DBAdapter Protocol used by CsvReporter)
      - a CsvReporterConfig (queries + CSV configs)

    It exposes a single call `run_export(...)` that validates labels and delegates
    to CsvReporter.run(...).
    """

    def __init__(self, adapter, cfg: CsvReporterConfig) -> None:
        self._adapter = adapter
        self._cfg = cfg
        # Create a reporter bound to the adapter+config
        self._reporter = CsvReporter(adapter=adapter, config=cfg)

    def run_export(
        self,
        *,
        select_label: str,
        csv_config_label: str,
        out_path: str,
        params: Optional[Dict[str, Any]] = None,
        arraysize: int = 10_000,
    ) -> str:
        """
        Validate labels and execute the export. Returns the written path.
        Raises ValueError on unknown labels (router can map to HTTP 400).
        """
        if not self._cfg.has_query(select_label):
            raise ValueError(f"Unknown query label: {select_label}")

        if not self._cfg.has_csv_config(csv_config_label):
            raise ValueError(f"Unknown CSV config label: {csv_config_label}")

        return self._reporter.run(
            select_label=select_label,
            out_path=out_path,
            params=params or {},
            config_label=csv_config_label,
            arraysize=arraysize,
        )