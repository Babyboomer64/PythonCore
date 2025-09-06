

# server/app/services/job_manager.py
# Simple in-process Job Manager using threads.
# Comments in English as requested.

import threading
import uuid
from datetime import datetime
from typing import Any, Callable, Dict, Optional


class JobStatus:
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    ERROR = "ERROR"


class Job:
    def __init__(self, name: str, target: Callable, *args, **kwargs) -> None:
        self.id: str = str(uuid.uuid4())
        self.name: str = name
        self.status: str = JobStatus.PENDING
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        self.error: Optional[str] = None
        self.result: Optional[Any] = None

        self._target = target
        self._args = args
        self._kwargs = kwargs
        self._thread: Optional[threading.Thread] = None

    def run(self) -> None:
        self.status = JobStatus.RUNNING
        self.start_time = datetime.utcnow()
        try:
            self.result = self._target(*self._args, **self._kwargs)
            self.status = JobStatus.SUCCESS
        except Exception as e:
            self.error = str(e)
            self.status = JobStatus.ERROR
        finally:
            self.end_time = datetime.utcnow()

    def start(self) -> None:
        self._thread = threading.Thread(target=self.run, daemon=True)
        self._thread.start()


class JobManager:
    """Singleton-like manager to handle in-process jobs."""

    def __init__(self) -> None:
        self._jobs: Dict[str, Job] = {}
        self._lock = threading.Lock()

    def start_job(self, name: str, target: Callable, *args, **kwargs) -> Job:
        job = Job(name, target, *args, **kwargs)
        with self._lock:
            self._jobs[job.id] = job
        job.start()
        return job

    def get_job(self, job_id: str) -> Optional[Job]:
        with self._lock:
            return self._jobs.get(job_id)

    def list_jobs(self) -> Dict[str, Dict[str, Any]]:
        with self._lock:
            return {
                job_id: {
                    "name": job.name,
                    "status": job.status,
                    "start_time": job.start_time.isoformat() if job.start_time else None,
                    "end_time": job.end_time.isoformat() if job.end_time else None,
                    "error": job.error,
                }
                for job_id, job in self._jobs.items()
            }


# Global instance
job_manager = JobManager()