

# server/app/routers/jobs.py
# Router to query background jobs managed by JobManager.

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
import os
from ..services.job_manager import job_manager, Job

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.get("")
def list_jobs():
    """List all jobs with their status."""
    return job_manager.list_jobs()


@router.get("/{job_id}")
def get_job(job_id: str):
    """Get details for a single job."""
    job: Job | None = job_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    return {
        "id": job.id,
        "name": job.name,
        "status": job.status,
        "start_time": job.start_time.isoformat() if job.start_time else None,
        "end_time": job.end_time.isoformat() if job.end_time else None,
        "error": job.error,
        "result": job.result,
    }


# New endpoint: list only jobs that are currently RUNNING
@router.get("/active")
def list_active_jobs():
    """List only jobs that are currently RUNNING."""
    all_jobs = job_manager.list_jobs()
    active = {
        job_id: job
        for job_id, job in all_jobs.items()
        if job["status"] == "RUNNING"
    }
    return active


# Endpoint to download the file produced by a finished job
@router.get("/{job_id}/download")
def download_job_result(job_id: str):
    """
    Download the file produced by a finished job (expects job.result to be a filepath).
    """
    job: Job | None = job_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    if job.status != "SUCCESS":
        raise HTTPException(status_code=409, detail=f"Job {job_id} not finished (status={job.status})")
    if not isinstance(job.result, str):
        raise HTTPException(status_code=500, detail="Job result is not a filepath")
    file_path = os.path.abspath(job.result)
    if not os.path.exists(file_path) or not os.path.isfile(file_path):
        raise HTTPException(status_code=404, detail=f"File not found: {file_path}")
    return FileResponse(file_path, media_type="text/csv", filename=os.path.basename(file_path))