from __future__ import annotations

from typing import Any

import asyncpg


async def fetchrow(pool: asyncpg.Pool, query: str, *args: Any) -> asyncpg.Record | None:
    async with pool.acquire() as conn:
        return await conn.fetchrow(query, *args)


async def fetch(pool: asyncpg.Pool, query: str, *args: Any) -> list[asyncpg.Record]:
    async with pool.acquire() as conn:
        rows = await conn.fetch(query, *args)
        return list(rows)


async def execute(pool: asyncpg.Pool, query: str, *args: Any) -> str:
    async with pool.acquire() as conn:
        return await conn.execute(query, *args)


async def execute_fetchrow(pool: asyncpg.Pool, query: str, *args: Any) -> asyncpg.Record:
    async with pool.acquire() as conn:
        return await conn.fetchrow(query, *args)
