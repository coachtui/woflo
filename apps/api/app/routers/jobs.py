"""Job queue management endpoints."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from app.core.security import get_current_profile, Profile, require_role
from app.db.session import get_pool
from app.services.job_queue_service import enqueue_job, get_job_status, list_jobs


router = APIRouter(prefix="/v1/jobs", tags=["jobs"])


class EnqueueJobRequest(BaseModel):
    """Request to enqueue a job."""
    
    type: str = Field(..., description="Job type (ai_enrich, schedule_run)")
    payload: dict[str, Any] = Field(..., description="Job payload (JSON)")
    max_attempts: int = Field(3, ge=1, le=10, description="Maximum retry attempts")


class EnqueueJobResponse(BaseModel):
    """Response for enqueued job."""
    
    job_id: str = Field(..., description="Job ID")


class JobStatusResponse(BaseModel):
    """Job status response."""
    
    id: str
    org_id: str
    type: str
    payload: dict[str, Any]
    status: str
    run_after: str
    attempts: int
    max_attempts: int
    locked_at: str | None
    locked_by: str | None
    error: str | None
    created_at: str
    updated_at: str | None


@router.post("", response_model=EnqueueJobResponse)
async def create_job(
    req: EnqueueJobRequest,
    profile: Profile = Depends(require_role(["admin", "dispatcher"])),
) -> EnqueueJobResponse:
    """
    Enqueue a job for async processing.
    
    Only admins and dispatchers can enqueue jobs.
    """
    # Validate job type
    valid_types = ["ai_enrich", "schedule_run"]
    if req.type not in valid_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid job type. Must be one of: {', '.join(valid_types)}",
        )
    
    pool = await get_pool()
    job_id = await enqueue_job(
        pool,
        org_id=profile.org_id,
        job_type=req.type,
        payload=req.payload,
        max_attempts=req.max_attempts,
    )
    
    return EnqueueJobResponse(job_id=job_id)


@router.get("/{job_id}", response_model=JobStatusResponse)
async def get_job(
    job_id: str,
    profile: Profile = Depends(get_current_profile),
) -> JobStatusResponse:
    """
    Get job status by ID.
    
    Users can only access jobs in their organization.
    """
    pool = await get_pool()
    job = await get_job_status(pool, job_id=job_id, org_id=profile.org_id)
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return JobStatusResponse(**job)


@router.get("", response_model=list[JobStatusResponse])
async def list_org_jobs(
    status: str | None = Query(None, description="Filter by status"),
    type: str | None = Query(None, description="Filter by type"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of jobs"),
    profile: Profile = Depends(get_current_profile),
) -> list[JobStatusResponse]:
    """
    List jobs for the current organization.
    
    Users can filter by status and type.
    """
    pool = await get_pool()
    jobs = await list_jobs(
        pool,
        org_id=profile.org_id,
        status=status,
        job_type=type,
        limit=limit,
    )
    
    return [JobStatusResponse(**job) for job in jobs]
