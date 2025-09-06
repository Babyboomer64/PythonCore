# server/app/routers/admin.py
# Admin endpoints: token-protected shutdown

from fastapi import APIRouter, Header, HTTPException, status
import os, signal, threading, time
from datetime import datetime
from ..settings import Settings
from ..lifecycle import state
from csv_reporter_config import CsvReporterConfig

router = APIRouter(prefix="/admin", tags=["admin"])

def _verify_token(x_admin_token: str | None, settings: Settings):
    if not settings.ADMIN_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="ADMIN_TOKEN not configured on server"
        )
    if not x_admin_token or x_admin_token != settings.ADMIN_TOKEN:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid admin token")

def _shutdown_async():
    # Delay slightly to let the HTTP response flush before killing the process
    time.sleep(0.2)
    # Send SIGINT (Ctrl+C) to current process; uvicorn handles graceful shutdown
    os.kill(os.getpid(), signal.SIGINT)

@router.post("/shutdown")
def shutdown(x_admin_token: str | None = Header(default=None, alias="X-Admin-Token")):
    settings = Settings()
    _verify_token(x_admin_token, settings)
    threading.Thread(target=_shutdown_async, daemon=True).start()
    return {"status": "shutting down"}


# Info endpoint
@router.get("/info")
def info(x_admin_token: str | None = Header(default=None, alias="X-Admin-Token")):
    settings = Settings()
    _verify_token(x_admin_token, settings)

    start_time = getattr(state, "start_time", None)
    uptime = None
    if start_time:
        uptime = (datetime.utcnow() - start_time).total_seconds()

    return {
        "app_name": settings.APP_NAME,
        "env": settings.ENV,
        "version": "0.1.0",
        "start_time": start_time.isoformat() if start_time else None,
        "uptime_seconds": uptime
    }


# Reload config endpoint
@router.post("/reload-config")
def reload_config(x_admin_token: str | None = Header(default=None, alias="X-Admin-Token")):
    settings = Settings()
    _verify_token(x_admin_token, settings)

    try:
        state.cfg = CsvReporterConfig.from_files(
            settings.QUERIES_PATH,
            settings.CSV_CONFIGS_PATH,
            overwrite=True,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to reload config: {e}")

    return {
        "status": "reloaded",
        "timestamp": datetime.utcnow().isoformat(),
        "queries": state.cfg.list_query_labels(),
        "csv_configs": state.cfg.list_csv_config_labels()
    }