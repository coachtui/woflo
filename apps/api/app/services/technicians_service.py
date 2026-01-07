from __future__ import annotations

from typing import Any

import asyncpg

from apps.api.app.core.security import Profile
from apps.api.app.models.pydantic.common import TechnicianCreateRequest
from apps.api.app.services.audit_service import write_audit_log


async def create_technician(
    pool: asyncpg.Pool,
    *,
    profile: Profile,
    req: TechnicianCreateRequest,
) -> dict[str, Any]:
    row = await pool.fetchrow(
        """
        insert into public.technicians (org_id, name, efficiency_multiplier, overtime_allowed, wip_limit)
        values ($1::uuid, $2, $3, $4, $5)
        returning id::text as id, profile_id::text as profile_id, name, efficiency_multiplier, overtime_allowed, wip_limit
        """,
        profile.org_id,
        req.name,
        req.efficiency_multiplier,
        req.overtime_allowed,
        req.wip_limit,
    )
    if row is None:
        raise RuntimeError("Failed to create technician")

    await write_audit_log(
        pool,
        profile=profile,
        entity_type="technician",
        entity_id=row["id"],
        action="create",
        diff={"technician": req.model_dump(mode="json")},
        reason="create_technician",
    )
    return dict(row)


async def list_technicians(pool: asyncpg.Pool, *, profile: Profile) -> list[dict[str, Any]]:
    rows = await pool.fetch(
        """
        select id::text as id, profile_id::text as profile_id, name, efficiency_multiplier, overtime_allowed, wip_limit
        from public.technicians
        where org_id = $1::uuid
        order by name asc
        """,
        profile.org_id,
    )
    return [dict(r) for r in rows]
