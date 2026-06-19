from typing import List

from fastapi import APIRouter, HTTPException

from app.models.schemas import JobLogs, JobStatus
from app.services.process_manager import process_manager

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.get("/recent", response_model=List[JobStatus])
def list_recent_jobs():
    return process_manager.list_recent()


@router.get("/{job_id}", response_model=JobStatus)
def get_job(job_id: str):
    job = process_manager.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found")
    return job


@router.get("/{job_id}/logs", response_model=JobLogs)
def get_job_logs(job_id: str, tail: int = 200):
    job = process_manager.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found")
    return JobLogs(
        job_id=job_id,
        lines=process_manager.read_logs(job_id, tail=tail),
        status=job["status"],
    )
