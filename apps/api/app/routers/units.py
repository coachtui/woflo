from __future__ import annotations

from fastapi import APIRouter, Depends

from apps.api.app.core.security import Profile, require_roles
from apps.api.app.db.session import get_pool
from apps.api.app.models.pydantic.common import UnitCreateRequest, UnitResponse
from apps.api.app.services.units_service import create_unit, list_units


router = APIRouter(prefix="/v1/units")


@router.post("", response_model=UnitResponse)
async def create_unit_endpoint(
    req: UnitCreateRequest,
    profile: Profile = Depends(require_roles("admin", "dispatcher")),
):
    pool = await get_pool()
    return await create_unit(pool, profile=profile, req=req)


@router.get("", response_model=list[UnitResponse])
async def list_units_endpoint(
    profile: Profile = Depends(require_roles("admin", "dispatcher")),
):
    pool = await get_pool()
    return await list_units(pool, profile=profile)
