from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from apps.api.app.core.security import Profile, require_roles
from apps.api.app.db.session import get_pool
from apps.api.app.models.pydantic.common import WorkOrderCreateRequest, WorkOrderCreateResponse, WorkOrderListItem
from apps.api.app.services.work_orders_service import create_work_order, list_work_orders


router = APIRouter(prefix="/v1/work-orders")


@router.post("", response_model=WorkOrderCreateResponse)
async def create(
    req: WorkOrderCreateRequest,
    profile: Profile = Depends(require_roles("admin", "dispatcher")),
):
    pool = await get_pool()
    data = await create_work_order(pool, profile=profile, req=req)
    return data


@router.get("", response_model=list[WorkOrderListItem])
async def list_endpoint(
    status: str | None = Query(default=None),
    blocked_parts: bool | None = Query(default=None),
    profile: Profile = Depends(require_roles("admin", "dispatcher")),
):
    pool = await get_pool()
    items = await list_work_orders(pool, profile=profile, status=status, blocked_parts=blocked_parts)
    return items
