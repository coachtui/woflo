from __future__ import annotations

from fastapi import APIRouter, Depends

from app.core.security import Profile, get_current_profile, require_roles
from app.db.session import get_pool
from app.models.pydantic.common import TaskCreateReplaceRequest, TaskPatchRequest, TaskResponse
from app.services.tasks_service import list_tasks, patch_task, replace_task_plan


router = APIRouter(prefix="/v1")


@router.get("/tasks", response_model=list[TaskResponse])
async def list_tasks_endpoint(
    # TEMP: Remove auth for development - TODO: Add back for production
    # profile: Profile = Depends(get_current_profile),
):
    # TEMP: Mock profile for development (using real org from DB)
    profile = Profile(
        id="00000000-0000-0000-0000-000000000001",
        org_id="c6cd5638-d905-4673-9124-c957725acd00",  # Demo Diesel Shop
        role="admin",
        email="dev@example.com",
        display_name="Dev User"
    )
    
    pool = await get_pool()
    rows = await list_tasks(pool, profile=profile)
    return rows


@router.post("/work-orders/{work_order_id}/tasks", response_model=list[TaskResponse])
async def create_or_replace_tasks(
    work_order_id: str,
    req: TaskCreateReplaceRequest,
    # TEMP: Remove auth for development - TODO: Add back for production
    # profile: Profile = Depends(require_roles("admin", "dispatcher")),
):
    # TEMP: Mock profile for development (using real org from DB)
    profile = Profile(
        id="00000000-0000-0000-0000-000000000001",
        org_id="c6cd5638-d905-4673-9124-c957725acd00",  # Demo Diesel Shop
        role="admin",
        email="dev@example.com",
        display_name="Dev User"
    )
    
    pool = await get_pool()
    rows = await replace_task_plan(pool, profile=profile, work_order_id=work_order_id, req=req)
    return rows


@router.patch("/tasks/{task_id}", response_model=TaskResponse)
async def patch_task_endpoint(
    task_id: str,
    req: TaskPatchRequest,
    # TEMP: Remove auth for development - TODO: Add back for production
    # profile: Profile = Depends(get_current_profile),
):
    # TEMP: Mock profile for development (using real org from DB)
    profile = Profile(
        id="00000000-0000-0000-0000-000000000001",
        org_id="c6cd5638-d905-4673-9124-c957725acd00",  # Demo Diesel Shop
        role="admin",
        email="dev@example.com",
        display_name="Dev User"
    )
    
    # Service layer enforces tech-only limitations.
    pool = await get_pool()
    row = await patch_task(pool, profile=profile, task_id=task_id, req=req)
    return row
