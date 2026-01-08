"""Data loader for scheduler."""

from __future__ import annotations

import logging
from datetime import datetime

import asyncpg

from app.scheduler.models import (
    Bay,
    ScheduleInput,
    Task,
    Technician,
    WorkOrder,
)

logger = logging.getLogger(__name__)


async def load_schedule_input(
    pool: asyncpg.Pool,
    org_id: str,
    schedule_run_id: str,
    horizon_start: datetime,
    horizon_end: datetime,
) -> ScheduleInput:
    """
    Load all data needed for scheduling.
    
    Args:
        pool: Database connection pool
        org_id: Organization ID
        schedule_run_id: Schedule run ID
        horizon_start: Start of scheduling horizon
        horizon_end: End of scheduling horizon
    
    Returns:
        ScheduleInput with all loaded data
    """
    logger.info(
        "loading_schedule_data",
        extra={
            "org_id": org_id,
            "schedule_run_id": schedule_run_id,
            "horizon_start": horizon_start,
            "horizon_end": horizon_end,
        },
    )
    
    # Load tasks (only todo/scheduled status)
    task_rows = await pool.fetch(
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
        where org_id = $1::uuid
          and status in ('todo', 'scheduled')
        order by created_at
        """,
        org_id,
    )
    
    tasks = [Task.from_row(dict(row)) for row in task_rows]
    logger.info("loaded_tasks", extra={"count": len(tasks)})
    
    # Load technicians
    tech_rows = await pool.fetch(
        """
        select
          id::text as id,
          name,
          efficiency_multiplier,
          wip_limit
        from public.technicians
        where org_id = $1::uuid
        order by name
        """,
        org_id,
    )
    
    # Load technician skills
    skill_rows = await pool.fetch(
        """
        select
          technician_id::text as technician_id,
          skill
        from public.technician_skills
        where org_id = $1::uuid
        order by technician_id, skill
        """,
        org_id,
    )
    
    # Group skills by technician
    tech_skills: dict[str, list[str]] = {}
    for row in skill_rows:
        tech_id = row["technician_id"]
        if tech_id not in tech_skills:
            tech_skills[tech_id] = []
        tech_skills[tech_id].append(row["skill"])
    
    technicians = [
        Technician.from_row(dict(row), tech_skills.get(row["id"], []))
        for row in tech_rows
    ]
    logger.info("loaded_technicians", extra={"count": len(technicians)})
    
    # Load bays
    bay_rows = await pool.fetch(
        """
        select
          id::text as id,
          name,
          bay_type,
          capacity,
          is_active
        from public.bays
        where org_id = $1::uuid
          and is_active = true
        order by name
        """,
        org_id,
    )
    
    bays = [Bay.from_row(dict(row)) for row in bay_rows]
    logger.info("loaded_bays", extra={"count": len(bays)})
    
    # Load work orders for the tasks
    work_order_ids = list(set(t.work_order_id for t in tasks))
    
    if work_order_ids:
        wo_rows = await pool.fetch(
            """
            select
              id::text as id,
              priority,
              due_date,
              parts_ready
            from public.work_orders
            where org_id = $1::uuid
              and id = any($2::uuid[])
            """,
            org_id,
            work_order_ids,
        )
        
        work_orders = {
            row["id"]: WorkOrder.from_row(dict(row))
            for row in wo_rows
        }
    else:
        work_orders = {}
    
    logger.info("loaded_work_orders", extra={"count": len(work_orders)})
    
    return ScheduleInput(
        org_id=org_id,
        schedule_run_id=schedule_run_id,
        horizon_start=horizon_start,
        horizon_end=horizon_end,
        tasks=tasks,
        technicians=technicians,
        bays=bays,
        work_orders=work_orders,
    )
