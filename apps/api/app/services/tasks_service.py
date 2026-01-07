from __future__ import annotations

from typing import Any

import asyncpg

from apps.api.app.core.errors import ForbiddenError
from apps.api.app.core.security import Profile
from apps.api.app.models.pydantic.common import TaskCreateReplaceRequest, TaskPatchRequest
from apps.api.app.services.audit_service import write_audit_log


async def replace_task_plan(
    pool: asyncpg.Pool,
    *,
    profile: Profile,
    work_order_id: str,
    req: TaskCreateReplaceRequest,
) -> list[dict[str, Any]]:
    # MVP: replace by deleting existing tasks (not done/in_progress) and inserting new.
    async with pool.acquire() as conn:
        async with conn.transaction():
            await conn.execute(
                """
                delete from public.tasks
                where org_id = $1::uuid and work_order_id = $2::uuid and status in ('todo','scheduled','blocked')
                """,
                profile.org_id,
                work_order_id,
            )

            created: list[dict[str, Any]] = []
            for t in req.tasks:
                row = await conn.fetchrow(
                    """
                    insert into public.tasks (
                      org_id, work_order_id, type, status,
                      duration_minutes_low, duration_minutes_high
                    )
                    values ($1::uuid, $2::uuid, $3, 'todo', $4, $5)
                    returning id::text as id
                    """,
                    profile.org_id,
                    work_order_id,
                    t.type,
                    t.duration_minutes_low,
                    t.duration_minutes_high,
                )
                created.append({"id": row["id"]})

    await write_audit_log(
        pool,
        profile=profile,
        entity_type="task",
        entity_id=work_order_id,
        action="update",
        diff={"task_plan": req.model_dump(mode="json")},
        reason="replace_task_plan",
    )

    # Return full task rows
    rows = await pool.fetch(
        """
        select
          id::text as id,
          work_order_id::text as work_order_id,
          type,
          status,
          required_skill,
          required_skill_is_hard,
          required_bay_type,
          earliest_start,
          latest_finish,
          duration_minutes_low,
          duration_minutes_high,
          lock_flag,
          locked_tech_id::text as locked_tech_id,
          locked_bay_id::text as locked_bay_id,
          locked_start_at,
          locked_end_at
        from public.tasks
        where org_id = $1::uuid and work_order_id = $2::uuid
        order by created_at asc
        """,
        profile.org_id,
        work_order_id,
    )
    return [dict(r) for r in rows]


async def patch_task(
    pool: asyncpg.Pool,
    *,
    profile: Profile,
    task_id: str,
    req: TaskPatchRequest,
) -> dict[str, Any]:
    # Tech can ONLY update status for now (MVP). Dispatcher/admin can update all fields.
    if profile.role == "tech":
        allowed = {"status"}
        provided = {k for k, v in req.model_dump(exclude_none=True).items()}
        if not provided.issubset(allowed):
            raise ForbiddenError("Tech may only update task status")

        # Additionally ensure tech is assigned to this task (via schedule_items).
        assigned = await pool.fetchrow(
            """
            select 1
            from public.schedule_items si
            join public.technicians t on t.id = si.technician_id
            where si.task_id = $1::uuid
              and t.profile_id = $2::uuid
            limit 1
            """,
            task_id,
            profile.id,
        )
        if not assigned:
            raise ForbiddenError("Tech is not assigned to this task")

    fields = req.model_dump(exclude_none=True)
    if not fields:
        raise ValueError("No fields to update")

    set_clauses = []
    args: list[Any] = [profile.org_id, task_id]
    idx = 3
    for k, v in fields.items():
        set_clauses.append(f"{k} = ${idx}")
        args.append(v)
        idx += 1

    sql = f"""
      update public.tasks
      set {', '.join(set_clauses)}
      where org_id = $1::uuid and id = $2::uuid
      returning
        id::text as id,
        work_order_id::text as work_order_id,
        type,
        status,
        required_skill,
        required_skill_is_hard,
        required_bay_type,
        earliest_start,
        latest_finish,
        duration_minutes_low,
        duration_minutes_high,
        lock_flag,
        locked_tech_id::text as locked_tech_id,
        locked_bay_id::text as locked_bay_id,
        locked_start_at,
        locked_end_at
    """

    row = await pool.fetchrow(sql, *args)
    if row is None:
        raise ValueError("Task not found")

    await write_audit_log(
        pool,
        profile=profile,
        entity_type="task",
        entity_id=task_id,
        action="update",
        diff=fields,
    )

    return dict(row)
