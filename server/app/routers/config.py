# server/app/routers/config.py
# Expose available query and CSV-config labels.

from fastapi import APIRouter, Depends
from csv_reporter_config import CsvReporterConfig
from ..deps import get_config

router = APIRouter(prefix="/config", tags=["config"])

@router.get("/queries")
def list_queries(cfg: CsvReporterConfig = Depends(get_config)):
    return {"labels": cfg.list_query_labels()}

@router.get("/csv-configs")
def list_csv_configs(cfg: CsvReporterConfig = Depends(get_config)):
    return {"labels": cfg.list_csv_config_labels()} 
