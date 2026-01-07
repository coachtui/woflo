from __future__ import annotations

from datetime import date
from typing import Any

import asyncpg

from apps.api.app.core.security import Profile
from apps.api.app.models.pydantic.common import WorkOrderCreateRequest
from apps.api.app.services.audit_service import write_audit_log


async def create_work_order(
    pool: asyncpg.Pool,
    *,
    profile: Profile,
    req: WorkOrderCreateRequest,
) -> dict[str, Any]:
    row = await pool.fetchrow(
        """
        insert into public.work_orders (
          org_id, unit_id, asset_type, priority, due_date, customer_commitment_at,
          location, notes, status, parts_required
        )
        values ($1::uuid, $2::uuid, $3, $4, $5::date, $6::timestamptz, $7, $8, 'new', $9)
        returning id::text as id, status
        """,
        profile.org_id,
        req.unit_id,
        req.asset_type,
        req.priority,
        req.due_date,
        req.customer_commitment_at,
        req.location,
        req.notes,
        req.parts_required,
    )
    if row is None:
        raise RuntimeError("Failed to create work order")

    wo_id = row["id"]
    await write_audit_log(
        pool,
        profile=profile,
        entity_type="work_order",
        entity_id=wo_id,
        action="create",
        diff=req.model_dump(mode="json"),
    )

    return {"id": wo_id, "status": row["status"]}


async def list_work_orders(
    pool: asyncpg.Pool,
    *,
    profile: Profile,
    status: str | None,
    blocked_parts: bool | None,
) -> list[dict[str, Any]]:
    where = ["org_id = $1::uuid"]
    args: list[Any] = [profile.org_id]

    if status:
        # CTO example uses status=unscheduled.
        # MVP interpretation: unscheduled == new|triage.
        if status == "unscheduled":
            where.append("status in ('new','triage')")
        else:
            where.append("status = $%d" % (len(args) + 1))
            args.append(status)

    if blocked_parts is True:
        where.append("parts_required = true")
        where.append("parts_ready = false")

    sql = f"""
      select
        wo.id::text as id,
        wo.unit_id::text as unit_id,
        wo.asset_type,
        wo.priority,
        wo.due_date,
        wo.customer_commitment_at,
        wo.location,
        wo.notes,
        wo.status,
        wo.parts_required,
        wo.parts_status,
        wo.parts_ready,
        wo.parts_ready_at,
        wo.estimated_hours_low,
        wo.estimated_hours_high,
        wo.required_bay_type,
        (wo.parts_required and wo.parts_ready = false) as is_blocked_parts,
        (wo.due_date is not null and wo.due_date < current_date and wo.status not in ('done','canceled')) as is_overdue,
        exists (select 1 from public.ai_jobs aj where aj.work_order_id = wo.id and aj.status = 'succeeded') as has_ai_enrichment
      from public.work_orders wo
      where {' and '.join(where)}
      order by wo.priority desc, wo.due_date nulls last, wo.created_at desc
    """

    rows = await pool.fetch(sql, *args)
    return [dict(r) for r in rows]
