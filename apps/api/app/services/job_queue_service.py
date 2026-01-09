"""Job queue service for async job processing."""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from typing import Any
from uuid import UUID

import asyncpg


async def enqueue_job(
    pool: asyncpg.Pool,
    *,
    org_id: UUID | str,
    job_type: str,
    payload: dict[str, Any],
    run_after: datetime | None = None,
    max_attempts: int = 3,
) -> str:
    """
    Enqueue a job for async processing.

    Args:
        pool: Database connection pool
        org_id: Organization ID
        job_type: Job type (ai_enrich, schedule_run)
        payload: Job payload (must be JSON-serializable)
        run_after: Earliest time to run the job (defaults to now)
        max_attempts: Maximum number of retry attempts (default 3)

    Returns:
        Job ID (UUID as string)
    """
    if run_after is None:
        run_after = datetime.utcnow()

    # Serialize payload to JSON string for PostgreSQL jsonb column
    payload_json = json.dumps(payload)

    row = await pool.fetchrow(
        """
        insert into public.job_queue (org_id, type, payload, status, run_after, max_attempts)
        values ($1::uuid, $2, $3::jsonb, 'queued', $4::timestamptz, $5)
        returning id::text as id
        """,
        str(org_id),
        job_type,
        payload_json,
        run_after,
        max_attempts,
    )

    if row is None:
        raise RuntimeError("Failed to enqueue job")

    return row["id"]


async def get_job_status(
    pool: asyncpg.Pool,
    *,
    job_id: UUID | str,
    org_id: UUID | str,
) -> dict[str, Any] | None:
    """
    Get job status by ID.

    Args:
        pool: Database connection pool
        job_id: Job ID
        org_id: Organization ID (for RLS)

    Returns:
        Job record or None if not found
    """
    row = await pool.fetchrow(
        """
        select
          id::text as id,
          org_id::text as org_id,
          type,
          payload,
          status,
          run_after,
          attempts,
          max_attempts,
          locked_at,
          locked_by,
          error,
          created_at,
          updated_at
        from public.job_queue
        where id = $1::uuid and org_id = $2::uuid
        """,
        str(job_id),
        str(org_id),
    )

    return dict(row) if row else None


async def list_jobs(
    pool: asyncpg.Pool,
    *,
    org_id: UUID | str,
    status: str | None = None,
    job_type: str | None = None,
    limit: int = 100,
) -> list[dict[str, Any]]:
    """
    List jobs for an organization.

    Args:
        pool: Database connection pool
        org_id: Organization ID
        status: Filter by status (optional)
        job_type: Filter by job type (optional)
        limit: Maximum number of jobs to return

    Returns:
        List of job records
    """
    where = ["org_id = $1::uuid"]
    args: list[Any] = [str(org_id)]

    if status:
        where.append(f"status = ${len(args) + 1}")
        args.append(status)

    if job_type:
        where.append(f"type = ${len(args) + 1}")
        args.append(job_type)

    sql = f"""
        select
          id::text as id,
          org_id::text as org_id,
          type,
          payload,
          status,
          run_after,
          attempts,
          max_attempts,
          locked_at,
          locked_by,
          error,
          created_at,
          updated_at
        from public.job_queue
        where {' and '.join(where)}
        order by created_at desc
        limit ${len(args) + 1}
    """
    args.append(limit)

    rows = await pool.fetch(sql, *args)
    return [dict(r) for r in rows]
