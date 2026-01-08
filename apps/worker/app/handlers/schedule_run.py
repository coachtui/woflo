"""Schedule run job handler."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

import asyncpg

from app.scheduler.cp_sat_scheduler import run_scheduler
from app.scheduler.data_loader import load_schedule_input
from app.scheduler.persistence import save_schedule_result

logger = logging.getLogger(__name__)


async def handle_schedule_run(pool: asyncpg.Pool, job_id: str, payload: dict[str, Any]) -> None:
    """
    Handle schedule run job using OR-Tools CP-SAT scheduler.
    
    Args:
        pool: Database connection pool
        job_id: Job ID
        payload: Job payload containing schedule_run_id and parameters
    
    Raises:
        ValueError: If payload is invalid
        RuntimeError: If job processing fails
    """
    schedule_run_id = payload.get("schedule_run_id")
    if not schedule_run_id:
        raise ValueError("schedule_run_id is required in payload")
    
    org_id = payload.get("org_id")
    if not org_id:
        raise ValueError("org_id is required in payload")
    
    horizon_start_str = payload.get("horizon_start")
    horizon_end_str = payload.get("horizon_end")
    
    if not horizon_start_str or not horizon_end_str:
        raise ValueError("horizon_start and horizon_end are required")
    
    # Parse datetimes
    horizon_start = datetime.fromisoformat(horizon_start_str.replace("Z", "+00:00"))
    horizon_end = datetime.fromisoformat(horizon_end_str.replace("Z", "+00:00"))
    
    logger.info(
        "schedule_run_job_started",
        extra={
            "job_id": job_id,
            "schedule_run_id": schedule_run_id,
            "org_id": org_id,
            "horizon_start": horizon_start_str,
            "horizon_end": horizon_end_str,
        },
    )
    
    # Update status to running
    await pool.execute(
        """
        update public.schedule_runs
        set status = 'running', updated_at = now()
        where id = $1::uuid
        """,
        schedule_run_id,
    )
    
    try:
        # Load data
        input_data = await load_schedule_input(
            pool,
            org_id=org_id,
            schedule_run_id=schedule_run_id,
            horizon_start=horizon_start,
            horizon_end=horizon_end,
        )
        
        # Check if there are tasks to schedule
        if not input_data.tasks:
            logger.info(
                "no_tasks_to_schedule",
                extra={"schedule_run_id": schedule_run_id},
            )
            await pool.execute(
                """
                update public.schedule_runs
                set
                  status = 'succeeded',
                  task_count = 0,
                  updated_at = now()
                where id = $1::uuid
                """,
                schedule_run_id,
            )
            return
        
        # Check if there are resources
        if not input_data.technicians:
            raise RuntimeError("No technicians available for scheduling")
        
        if not input_data.bays:
            raise RuntimeError("No bays available for scheduling")
        
        # Run scheduler
        time_limit = payload.get("time_limit_seconds", 30)
        result = run_scheduler(input_data, time_limit_seconds=time_limit)
        
        # Save result
        await save_schedule_result(pool, schedule_run_id, result)
        
        logger.info(
            "schedule_run_job_completed",
            extra={
                "job_id": job_id,
                "schedule_run_id": schedule_run_id,
                "status": result.status,
                "task_count": len(result.items),
                "wall_time_ms": result.solver_wall_time_ms,
            },
        )
        
        if result.status != "succeeded":
            raise RuntimeError(
                f"Schedule failed: {result.infeasible_reason or 'unknown error'}"
            )
    
    except Exception as e:
        # Update schedule_runs to failed
        await pool.execute(
            """
            update public.schedule_runs
            set
              status = 'failed',
              infeasible_reason = $2,
              updated_at = now()
            where id = $1::uuid
            """,
            schedule_run_id,
            str(e),
        )
        raise
