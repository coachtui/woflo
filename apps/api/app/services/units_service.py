from __future__ import annotations

from typing import Any

import asyncpg

from apps.api.app.core.security import Profile
from apps.api.app.models.pydantic.common import UnitCreateRequest
from apps.api.app.services.audit_service import write_audit_log


async def create_unit(
    pool: asyncpg.Pool,
    *,
    profile: Profile,
    req: UnitCreateRequest,
) -> dict[str, Any]:
    row = await pool.fetchrow(
        """
        insert into public.units (org_id, unit_number, asset_type, customer_name_redacted)
        values ($1::uuid, $2, $3, $4)
        returning id::text as id, unit_number, asset_type, customer_name_redacted
        """,
        profile.org_id,
        req.unit_number,
        req.asset_type,
        req.customer_name_redacted,
    )
    if row is None:
        raise RuntimeError("Failed to create unit")

    await write_audit_log(
        pool,
        profile=profile,
        entity_type="unit",
        entity_id=row["id"],
        action="create",
        diff={"unit": req.model_dump(mode="json")},
        reason="create_unit",
    )
    return dict(row)


async def list_units(
    pool: asyncpg.Pool,
    *,
    profile: Profile,
) -> list[dict[str, Any]]:
    rows = await pool.fetch(
        """
        select id::text as id, unit_number, asset_type, customer_name_redacted
        from public.units
        where org_id = $1::uuid
        order by unit_number asc
        """,
        profile.org_id,
    )
    return [dict(r) for r in rows]
