# server/app/routers/csv.py
# CSV export endpoint using the CsvService.
# Comments in English (as requested).

from pathlib import Path
from typing import Optional, Dict

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
import os

from ..deps import get_adapter, get_config
from ..services.csv_reporter_service import CsvService
from ..services.job_manager import job_manager


router = APIRouter(prefix="/csv", tags=["csv"])


class ExportRequest(BaseModel):
    select_label: str = Field(..., min_length=1)
    csv_config_label: str = Field(..., min_length=1)
    out_path: str
    params: Optional[Dict[str, str]] = None
    arraysize: int = 10_000
    background: bool = False


@router.post("/export")
def export_csv(
    req: ExportRequest,
    adapter = Depends(get_adapter),
    cfg = Depends(get_config),
):
    service = CsvService(adapter=adapter, cfg=cfg)

    if req.background:
        job = job_manager.start_job(
            name=f"CSV Export {req.select_label}",
            target=service.run_export,
            select_label=req.select_label,
            csv_config_label=req.csv_config_label,
            out_path=req.out_path,
            params=req.params,
            arraysize=req.arraysize,
        )
        return {"job_id": job.id, "status": job.status}

    try:
        written = service.run_export(
            select_label=req.select_label,
            csv_config_label=req.csv_config_label,
            out_path=req.out_path,
            params=req.params,
            arraysize=req.arraysize,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return {"written": str(Path(written).resolve())}


@router.get("/download")
def download_csv(path: str):
    """
    Download a CSV file by absolute or relative path.
    """
    file_path = os.path.abspath(path)
    if not os.path.exists(file_path) or not os.path.isfile(file_path):
        raise HTTPException(status_code=404, detail=f"File not found: {file_path}")
    return FileResponse(file_path, media_type="text/csv", filename=os.path.basename(file_path))