"""Schedule persistence service."""

from __future__ import annotations

import logging
from typing import Any

import asyncpg

from app.scheduler.models import ScheduleResult

logger = logging.getLogger(__name__)


async def save_schedule_result(
    pool: asyncpg.Pool,
    schedule_run_id: str,
    result: ScheduleResult,
) -> None:
    """
    Save schedule result to database.
    
    Args:
        pool: Database connection pool
        schedule_run_id: Schedule run ID
        result: Schedule result to save
    """
    logger.info(
        "saving_schedule_result",
        extra={
            "schedule_run_id": schedule_run_id,
            "status": result.status,
            "item_count": len(result.items),
        },
    )
    
    async with pool.acquire() as conn:
        async with conn.transaction():
            # Update schedule_runs
            if result.status == "succeeded":
                await conn.execute(
                    """
                    update public.schedule_runs
                    set
                      status = 'succeeded',
                      solver_wall_time_ms = $2,
                      objective_value = $3,
                      objective_breakdown = $4::jsonb,
                      task_count = $5,
                      updated_at = now()
                    where id = $1::uuid
                    """,
                    schedule_run_id,
                    result.solver_wall_time_ms,
                    result.objective_value,
                    result.objective_breakdown.to_dict() if result.objective_breakdown else None,
                    len(result.items),
                )
            elif result.status == "infeasible":
                await conn.execute(
                    """
                    update public.schedule_runs
                    set
                      status = 'failed',
                      solver_status = 'INFEASIBLE',
                      solver_wall_time_ms = $2,
                      infeasible_reason = $3,
                      updated_at = now()
                    where id = $1::uuid
                    """,
                    schedule_run_id,
                    result.solver_wall_time_ms,
                    result.infeasible_reason,
                )
            else:
                await conn.execute(
                    """
                    update public.schedule_runs
                    set
                      status = 'failed',
                      solver_wall_time_ms = $2,
                      infeasible_reason = $3,
                      updated_at = now()
                    where id = $1::uuid
                    """,
                    schedule_run_id,
                    result.solver_wall_time_ms,
                    result.infeasible_reason,
                )
            
            # Delete old schedule items for this run
            await conn.execute(
                """
                delete from public.schedule_items
                where schedule_run_id = $1::uuid
                """,
                schedule_run_id,
            )
            
            # Insert new schedule items
            if result.items:
                # Get org_id from schedule_run
                org_id = await conn.fetchval(
                    """
                    select org_id::text from public.schedule_runs
                    where id = $1::uuid
                    """,
                    schedule_run_id,
                )
                
                # Prepare values for bulk insert
                values = [
                    (
                        org_id,
                        schedule_run_id,
                        item.task_id,
                        item.technician_id,
                        item.bay_id,
                        item.start_at,
                        item.end_at,
                        item.is_locked,
                        item.why,
                    )
                    for item in result.items
                ]
                
                await conn.executemany(
                    """
                    insert into public.schedule_items (
                      org_id, schedule_run_id, task_id, technician_id, bay_id,
                      start_at, end_at, is_locked, why
                    )
                    values ($1::uuid, $2::uuid, $3::uuid, $4::uuid, $5::uuid, $6, $7, $8, $9::jsonb)
                    """,
                    values,
                )
                
                logger.info(
                    "schedule_items_saved",
                    extra={"schedule_run_id": schedule_run_id, "count": len(values)},
                )
            
            # Update task statuses to 'scheduled'
            if result.items:
                task_ids = [item.task_id for item in result.items]
                await conn.execute(
                    """
                    update public.tasks
                    set status = 'scheduled', updated_at = now()
                    where id = any($1::uuid[])
                      and status = 'todo'
                    """,
                    task_ids,
                )
    
    logger.info("schedule_result_saved", extra={"schedule_run_id": schedule_run_id})
