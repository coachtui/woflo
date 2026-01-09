"""Schedule management endpoints."""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from app.core.security import get_current_profile, Profile, require_role
from app.db.session import get_pool
from app.services.schedule_service import (
    create_schedule_run,
    get_schedule_items,
    get_schedule_run,
    list_schedule_runs,
)


router = APIRouter(prefix="/v1/schedules", tags=["schedules"])


class CreateScheduleRunRequest(BaseModel):
    """Request to create a schedule run."""
    
    horizon_start: datetime = Field(..., description="Start of scheduling horizon")
    horizon_end: datetime = Field(..., description="End of scheduling horizon")
    trigger: str = Field("manual", description="Trigger type")


class CreateScheduleRunResponse(BaseModel):
    """Response for created schedule run."""
    
    id: str
    status: str
    job_id: str


@router.post("", response_model=CreateScheduleRunResponse)
async def create_schedule(
    req: CreateScheduleRunRequest,
    # TEMP: Remove auth for development - TODO: Add back for production
    # profile: Profile = Depends(require_role(["admin", "dispatcher"])),
) -> CreateScheduleRunResponse:
    """
    Create a new schedule run.
    
    This creates a schedule run record and enqueues a job for the worker
    to process using OR-Tools CP-SAT.
    
    Only admins and dispatchers can create schedules.
    """
    # TEMP: Mock profile for development
    profile = Profile(
        id="dev-user",
        organization_id="dev-org",
        role="admin",
        full_name="Dev User",
        email="dev@example.com"
    )
    
    pool = await get_pool()
    result = await create_schedule_run(
        pool,
        profile=profile,
        horizon_start=req.horizon_start,
        horizon_end=req.horizon_end,
        trigger=req.trigger,
    )
    
    return CreateScheduleRunResponse(**result)


@router.get("/{schedule_run_id}")
async def get_schedule(
    schedule_run_id: str,
    # TEMP: Remove auth for development - TODO: Add back for production
    # profile: Profile = Depends(get_current_profile),
) -> dict:
    """
    Get schedule run by ID.
    
    Returns schedule run metadata including solver stats and objective breakdown.
    """
    # TEMP: Mock profile for development
    profile = Profile(
        id="dev-user",
        organization_id="dev-org",
        role="admin",
        full_name="Dev User",
        email="dev@example.com"
    )
    
    pool = await get_pool()
    schedule_run = await get_schedule_run(
        pool,
        profile=profile,
        schedule_run_id=schedule_run_id,
    )
    
    if not schedule_run:
        raise HTTPException(status_code=404, detail="Schedule run not found")
    
    return schedule_run


@router.get("/{schedule_run_id}/items")
async def get_schedule_items_endpoint(
    schedule_run_id: str,
    # TEMP: Remove auth for development - TODO: Add back for production
    # profile: Profile = Depends(get_current_profile),
) -> list[dict]:
    """
    Get schedule items for a schedule run.
    
    Returns all task assignments with technician, bay, and time information.
    """
    # TEMP: Mock profile for development
    profile = Profile(
        id="dev-user",
        organization_id="dev-org",
        role="admin",
        full_name="Dev User",
        email="dev@example.com"
    )
    
    pool = await get_pool()
    
    # Verify schedule run exists
    schedule_run = await get_schedule_run(
        pool,
        profile=profile,
        schedule_run_id=schedule_run_id,
    )
    
    if not schedule_run:
        raise HTTPException(status_code=404, detail="Schedule run not found")
    
    items = await get_schedule_items(
        pool,
        profile=profile,
        schedule_run_id=schedule_run_id,
    )
    
    return items


@router.get("")
async def list_schedules(
    limit: int = Query(50, ge=1, le=200, description="Maximum number of runs"),
    # TEMP: Remove auth for development - TODO: Add back for production
    # profile: Profile = Depends(get_current_profile),
) -> list[dict]:
    """
    List schedule runs for the organization.
    
    Returns schedule runs ordered by creation time (newest first).
    """
    # TEMP: Mock profile for development
    profile = Profile(
        id="dev-user",
        organization_id="dev-org",
        role="admin",
        full_name="Dev User",
        email="dev@example.com"
    )
    
    pool = await get_pool()
    schedule_runs = await list_schedule_runs(
        pool,
        profile=profile,
        limit=limit,
    )
    
    return schedule_runs
