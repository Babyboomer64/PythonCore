

# Router to provide a dummy job for testing background job execution.

import time
from fastapi import APIRouter
from ..services.job_manager import job_manager

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.post("/dummy")
def start_dummy_job(duration: int = 5):
    """
    Start a dummy job that simply sleeps for `duration` seconds.
    Returns the job_id immediately.
    """
    def dummy_task(seconds: int):
        time.sleep(seconds)
        return {"slept": seconds}

    job = job_manager.start_job(
        name=f"Dummy Job {duration}s",
        target=dummy_task,
        seconds=duration
    )
    return {"job_id": job.id, "status": job.status}