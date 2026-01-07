from __future__ import annotations

from fastapi import APIRouter, Depends

from apps.api.app.core.security import Profile, require_roles
from apps.api.app.db.session import get_pool
from apps.api.app.models.pydantic.common import TechnicianCreateRequest, TechnicianResponse
from apps.api.app.services.technicians_service import create_technician, list_technicians


router = APIRouter(prefix="/v1/technicians")


@router.post("", response_model=TechnicianResponse)
async def create_technician_endpoint(
    req: TechnicianCreateRequest,
    profile: Profile = Depends(require_roles("admin", "dispatcher")),
):
    pool = await get_pool()
    return await create_technician(pool, profile=profile, req=req)


@router.get("", response_model=list[TechnicianResponse])
async def list_technicians_endpoint(
    profile: Profile = Depends(require_roles("admin", "dispatcher")),
):
    pool = await get_pool()
    return await list_technicians(pool, profile=profile)
