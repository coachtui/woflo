from __future__ import annotations

from fastapi import APIRouter, Depends

from app.core.security import Profile, get_current_profile, require_roles
from app.db.session import get_pool
from app.models.pydantic.common import TaskCreateReplaceRequest, TaskPatchRequest, TaskResponse
from app.services.tasks_service import patch_task, replace_task_plan


router = APIRouter(prefix="/v1")


@router.post("/work-orders/{work_order_id}/tasks", response_model=list[TaskResponse])
async def create_or_replace_tasks(
    work_order_id: str,
    req: TaskCreateReplaceRequest,
    profile: Profile = Depends(require_roles("admin", "dispatcher")),
):
    pool = await get_pool()
    rows = await replace_task_plan(pool, profile=profile, work_order_id=work_order_id, req=req)
    return rows


@router.patch("/tasks/{task_id}", response_model=TaskResponse)
async def patch_task_endpoint(
    task_id: str,
    req: TaskPatchRequest,
    profile: Profile = Depends(get_current_profile),
):
    # Service layer enforces tech-only limitations.
    pool = await get_pool()
    row = await patch_task(pool, profile=profile, task_id=task_id, req=req)
    return row
