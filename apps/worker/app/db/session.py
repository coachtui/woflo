"""Database session management for worker."""

from __future__ import annotations

import os
import re
from urllib.parse import quote_plus, urlparse, urlunparse

import asyncpg


_pool: asyncpg.Pool | None = None


def fix_database_url(url: str) -> str:
    """Fix DATABASE_URL by properly encoding password and removing quotes.
    
    Handles cases where:
    - Password has quotes around it (e.g., :'password'@)
    - Password contains special characters that need URL encoding
    """
    # Remove quotes from password if present (e.g., :'password'@ -> :password@)
    url = re.sub(r":\'([^\']+)\'@", r":\1@", url)
    
    # Parse URL to encode special characters in password
    try:
        parsed = urlparse(url)
        if parsed.password and ('#' in parsed.password or '@' in parsed.password):
            # Reconstruct URL with URL-encoded password
            netloc = f"{parsed.username}:{quote_plus(parsed.password)}@{parsed.hostname}"
            if parsed.port:
                netloc += f":{parsed.port}"
            fixed = urlunparse((
                parsed.scheme,
                netloc,
                parsed.path,
                parsed.params,
                parsed.query,
                parsed.fragment
            ))
            return fixed
    except Exception:
        pass
    
    return url


async def get_pool() -> asyncpg.Pool:
    """Get or create database connection pool."""
    global _pool
    if _pool is None:
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            raise RuntimeError("DATABASE_URL is not set")
        # Fix URL encoding issues
        database_url = fix_database_url(database_url)
        _pool = await asyncpg.create_pool(dsn=database_url, min_size=1, max_size=10)
    return _pool


async def close_pool() -> None:
    """Close database connection pool."""
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None
