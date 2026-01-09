from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from app.core.security import Profile, require_roles
from app.db.session import get_pool
from app.models.pydantic.common import WorkOrderCreateRequest, WorkOrderCreateResponse, WorkOrderListItem
from app.services.work_orders_service import create_work_order, list_work_orders


router = APIRouter(prefix="/v1/work-orders")


@router.post("", response_model=WorkOrderCreateResponse)
async def create(
    req: WorkOrderCreateRequest,
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
    data = await create_work_order(pool, profile=profile, req=req)
    return data


@router.get("", response_model=list[WorkOrderListItem])
async def list_endpoint(
    status: str | None = Query(default=None),
    blocked_parts: bool | None = Query(default=None),
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
    items = await list_work_orders(pool, profile=profile, status=status, blocked_parts=blocked_parts)
    return items
