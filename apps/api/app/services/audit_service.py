from __future__ import annotations

import json
from typing import Any, Literal

import asyncpg

from app.core.security import Profile


EntityType = Literal["work_order", "task", "schedule", "parts", "ai_job"]
AuditAction = Literal[
    "create",
    "update",
    "delete",
    "lock",
    "unlock",
    "schedule_run",
    "override",
]


async def write_audit_log(
    pool: asyncpg.Pool,
    *,
    profile: Profile,
    entity_type: EntityType,
    entity_id: str,
    action: AuditAction,
    diff: dict[str, Any] | None = None,
    reason: str | None = None,
) -> None:
    # Serialize diff to JSON string for PostgreSQL jsonb column
    diff_json = json.dumps(diff) if diff is not None else None
    
    async with pool.acquire() as conn:
        await conn.execute(
            """
            insert into public.audit_log (org_id, actor_id, entity_type, entity_id, action, diff, reason)
            values ($1::uuid, $2::uuid, $3, $4::uuid, $5, $6::jsonb, $7)
            """,
            profile.org_id,
            profile.id,
            entity_type,
            entity_id,
            action,
            diff_json,
            reason,
        )
