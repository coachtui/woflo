"""Schedule service for API."""

from __future__ import annotations

from datetime import datetime
from typing import Any

import asyncpg

from app.core.security import Profile
from app.services.audit_service import write_audit_log
from app.services.job_queue_service import enqueue_job


async def create_schedule_run(
    pool: asyncpg.Pool,
    *,
    profile: Profile,
    horizon_start: datetime,
    horizon_end: datetime,
    trigger: str = "manual",
) -> dict[str, Any]:
    """
    Create a new schedule run and enqueue job.
    
    Args:
        pool: Database connection pool
        profile: User profile
        horizon_start: Start of scheduling horizon
        horizon_end: End of scheduling horizon
        trigger: Trigger type (manual, auto_parts, auto_callout, etc.)
    
    Returns:
        Created schedule run with job_id
    """
    # Count locked tasks
    locked_task_count = await pool.fetchval(
        """
        select count(*)
        from public.tasks
        where org_id = $1::uuid
          and lock_flag = true
          and status in ('todo', 'scheduled')
        """,
        profile.org_id,
    )
    
    # Create schedule_run
    row = await pool.fetchrow(
        """
        insert into public.schedule_runs (
          org_id, horizon_start, horizon_end, status, trigger,
          locked_task_count, created_by
        )
        values ($1::uuid, $2, $3, 'queued', $4, $5, $6::uuid)
        returning id::text as id, status
        """,
        profile.org_id,
        horizon_start,
        horizon_end,
        trigger,
        locked_task_count or 0,
        profile.id,
    )
    
    if not row:
        raise RuntimeError("Failed to create schedule run")
    
    schedule_run_id = row["id"]
    
    # Enqueue job
    job_id = await enqueue_job(
        pool,
        org_id=profile.org_id,
        job_type="schedule_run",
        payload={
            "schedule_run_id": schedule_run_id,
            "org_id": profile.org_id,
            "horizon_start": horizon_start.isoformat(),
            "horizon_end": horizon_end.isoformat(),
            "time_limit_seconds": 30,
        },
        max_attempts=1,  # Don't retry scheduling failures
    )
    
    # Write audit log
    await write_audit_log(
        pool,
        profile=profile,
        entity_type="schedule",
        entity_id=schedule_run_id,
        action="schedule_run",
        diff={
            "horizon_start": horizon_start.isoformat(),
            "horizon_end": horizon_end.isoformat(),
            "trigger": trigger,
        },
    )
    
    return {
        "id": schedule_run_id,
        "status": row["status"],
        "job_id": job_id,
    }


async def get_schedule_run(
    pool: asyncpg.Pool,
    *,
    profile: Profile,
    schedule_run_id: str,
) -> dict[str, Any] | None:
    """
    Get schedule run by ID.
    
    Args:
        pool: Database connection pool
        profile: User profile
        schedule_run_id: Schedule run ID
    
    Returns:
        Schedule run record or None
    """
    row = await pool.fetchrow(
        """
        select
          id::text as id,
          org_id::text as org_id,
          horizon_start,
          horizon_end,
          status,
          trigger,
          locked_task_count,
          task_count,
          solver_wall_time_ms,
          objective_value,
          objective_breakdown,
          solver_status,
          infeasible_reason,
          created_by::text as created_by,
          created_at,
          updated_at
        from public.schedule_runs
        where id = $1::uuid and org_id = $2::uuid
        """,
        schedule_run_id,
        profile.org_id,
    )
    
    return dict(row) if row else None


async def list_schedule_runs(
    pool: asyncpg.Pool,
    *,
    profile: Profile,
    limit: int = 50,
) -> list[dict[str, Any]]:
    """
    List schedule runs for organization.
    
    Args:
        pool: Database connection pool
        profile: User profile
        limit: Maximum number of runs to return
    
    Returns:
        List of schedule runs
    """
    rows = await pool.fetch(
        """
        select
          id::text as id,
          org_id::text as org_id,
          horizon_start,
          horizon_end,
          status,
          trigger,
          locked_task_count,
          task_count,
          solver_wall_time_ms,
          objective_value,
          objective_breakdown,
          solver_status,
          infeasible_reason,
          created_by::text as created_by,
          created_at,
          updated_at
        from public.schedule_runs
        where org_id = $1::uuid
        order by created_at desc
        limit $2
        """,
        profile.org_id,
        limit,
    )
    
    return [dict(r) for r in rows]


async def get_schedule_items(
    pool: asyncpg.Pool,
    *,
    profile: Profile,
    schedule_run_id: str,
) -> list[dict[str, Any]]:
    """
    Get schedule items for a schedule run.
    
    Args:
        pool: Database connection pool
        profile: User profile
        schedule_run_id: Schedule run ID
    
    Returns:
        List of schedule items
    """
    rows = await pool.fetch(
        """
        select
          si.id::text as id,
          si.task_id::text as task_id,
          si.technician_id::text as technician_id,
          si.bay_id::text as bay_id,
          si.start_at,
          si.end_at,
          si.is_locked,
          si.why,
          t.type as task_type,
          t.work_order_id::text as work_order_id,
          tech.name as technician_name,
          b.name as bay_name
        from public.schedule_items si
        join public.tasks t on t.id = si.task_id
        join public.technicians tech on tech.id = si.technician_id
        join public.bays b on b.id = si.bay_id
        where si.schedule_run_id = $1::uuid
          and si.org_id = $2::uuid
        order by si.start_at, tech.name
        """,
        schedule_run_id,
        profile.org_id,
    )
    
    return [dict(r) for r in rows]
