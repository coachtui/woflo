"""Job queue processor with concurrency control."""

from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Any, Callable

import asyncpg

from app.handlers.ai_enrich import handle_ai_enrich
from app.handlers.schedule_run import handle_schedule_run

logger = logging.getLogger(__name__)


# Job handler registry
JOB_HANDLERS: dict[str, Callable[[asyncpg.Pool, str, dict[str, Any]], Any]] = {
    "ai_enrich": handle_ai_enrich,
    "schedule_run": handle_schedule_run,
}


async def claim_next_job(
    pool: asyncpg.Pool,
    worker_id: str,
) -> dict[str, Any] | None:
    """
    Claim the next available job using FOR UPDATE SKIP LOCKED.
    
    This ensures multiple workers can safely process jobs concurrently
    without conflicts.
    
    Args:
        pool: Database connection pool
        worker_id: Worker identifier
    
    Returns:
        Job record or None if no jobs available
    """
    async with pool.acquire() as conn:
        async with conn.transaction():
            row = await conn.fetchrow(
                """
                update public.job_queue
                set
                  status = 'running',
                  locked_at = now(),
                  locked_by = $1,
                  attempts = attempts + 1,
                  updated_at = now()
                where id = (
                  select id
                  from public.job_queue
                  where status = 'queued'
                    and run_after <= now()
                  order by run_after, created_at
                  limit 1
                  for update skip locked
                )
                returning
                  id::text as id,
                  org_id::text as org_id,
                  type,
                  payload,
                  attempts,
                  max_attempts
                """,
                worker_id,
            )
    
    return dict(row) if row else None


async def mark_job_succeeded(pool: asyncpg.Pool, job_id: str) -> None:
    """
    Mark job as succeeded.
    
    Args:
        pool: Database connection pool
        job_id: Job ID
    """
    await pool.execute(
        """
        update public.job_queue
        set
          status = 'succeeded',
          locked_at = null,
          locked_by = null,
          updated_at = now()
        where id = $1::uuid
        """,
        job_id,
    )


async def mark_job_failed(
    pool: asyncpg.Pool,
    job_id: str,
    error: str,
    attempts: int,
    max_attempts: int,
) -> None:
    """
    Mark job as failed or requeue for retry.
    
    Implements retry logic with exponential backoff and dead-letter behavior.
    If attempts < max_attempts, requeue. Otherwise, mark as permanently failed.
    
    Args:
        pool: Database connection pool
        job_id: Job ID
        error: Error message
        attempts: Current attempt count
        max_attempts: Maximum allowed attempts
    """
    if attempts < max_attempts:
        # Requeue with exponential backoff: 2^attempts minutes
        backoff_minutes = 2 ** attempts
        logger.info(
            "job_retry_scheduled",
            extra={
                "job_id": job_id,
                "attempts": attempts,
                "max_attempts": max_attempts,
                "backoff_minutes": backoff_minutes,
            },
        )
        
        await pool.execute(
            """
            update public.job_queue
            set
              status = 'queued',
              run_after = now() + ($3 || ' minutes')::interval,
              locked_at = null,
              locked_by = null,
              error = $2,
              updated_at = now()
            where id = $1::uuid
            """,
            job_id,
            error,
            str(backoff_minutes),
        )
    else:
        # Dead letter: permanently failed
        logger.error(
            "job_dead_letter",
            extra={
                "job_id": job_id,
                "attempts": attempts,
                "max_attempts": max_attempts,
                "error": error,
            },
        )
        
        await pool.execute(
            """
            update public.job_queue
            set
              status = 'failed',
              locked_at = null,
              locked_by = null,
              error = $2,
              updated_at = now()
            where id = $1::uuid
            """,
            job_id,
            error,
        )


async def process_job(pool: asyncpg.Pool, worker_id: str) -> bool:
    """
    Process a single job from the queue.
    
    Returns True if a job was processed, False if no jobs available.
    
    Args:
        pool: Database connection pool
        worker_id: Worker identifier
    
    Returns:
        True if job was processed, False if no jobs available
    """
    job = await claim_next_job(pool, worker_id)
    
    if not job:
        return False
    
    job_id = job["id"]
    job_type = job["type"]
    payload = job["payload"]
    attempts = job["attempts"]
    max_attempts = job["max_attempts"]
    
    # Parse payload if it's a string (from database JSON column)
    if isinstance(payload, str):
        payload = json.loads(payload)
    
    logger.info(
        "job_processing_started",
        extra={
            "job_id": job_id,
            "job_type": job_type,
            "attempts": attempts,
            "worker_id": worker_id,
        },
    )
    
    try:
        # Dispatch to appropriate handler
        handler = JOB_HANDLERS.get(job_type)
        if not handler:
            raise ValueError(f"Unknown job type: {job_type}")
        
        await handler(pool, job_id, payload)
        
        # Mark as succeeded
        await mark_job_succeeded(pool, job_id)
        
        logger.info(
            "job_processing_succeeded",
            extra={"job_id": job_id, "job_type": job_type, "worker_id": worker_id},
        )
        
    except Exception as e:
        error_msg = f"{type(e).__name__}: {str(e)}"
        
        logger.error(
            "job_processing_failed",
            extra={
                "job_id": job_id,
                "job_type": job_type,
                "error": error_msg,
                "attempts": attempts,
                "worker_id": worker_id,
            },
            exc_info=True,
        )
        
        # Mark as failed or requeue
        await mark_job_failed(pool, job_id, error_msg, attempts, max_attempts)
    
    return True
