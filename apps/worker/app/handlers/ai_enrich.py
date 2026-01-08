"""AI enrichment job handler."""

from __future__ import annotations

import logging
from typing import Any

import asyncpg

logger = logging.getLogger(__name__)


async def handle_ai_enrich(pool: asyncpg.Pool, job_id: str, payload: dict[str, Any]) -> None:
    """
    Handle AI enrichment job.
    
    This is a stub implementation for Milestone B.
    Full implementation will be in Milestone D (LLM Gateway + enrichment pipeline).
    
    Args:
        pool: Database connection pool
        job_id: Job ID
        payload: Job payload containing work_order_id and other parameters
    
    Raises:
        ValueError: If payload is invalid
        RuntimeError: If job processing fails
    """
    work_order_id = payload.get("work_order_id")
    if not work_order_id:
        raise ValueError("work_order_id is required in payload")
    
    logger.info(
        "ai_enrich_job_started",
        extra={"job_id": job_id, "work_order_id": work_order_id},
    )
    
    # TODO (Milestone D): Implement AI enrichment pipeline
    # - Load work order details
    # - Call LLM provider (Claude/GPT)
    # - Parse and validate response
    # - Store ai_results
    # - Update work_order with enrichment
    
    logger.info(
        "ai_enrich_job_completed_stub",
        extra={"job_id": job_id, "work_order_id": work_order_id},
    )
