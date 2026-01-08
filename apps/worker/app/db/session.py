"""Database session management for worker."""

from __future__ import annotations

import logging
import os
import re
import socket
from urllib.parse import quote_plus, urlparse, urlunparse

import asyncpg


_pool: asyncpg.Pool | None = None
logger = logging.getLogger(__name__)


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


def test_dns_resolution(hostname: str) -> bool:
    """Test if hostname can be resolved via DNS."""
    try:
        result = socket.getaddrinfo(hostname, None)
        logger.info(f"✅ DNS resolution successful for {hostname}: {result[0][4][0]}")
        return True
    except socket.gaierror as e:
        logger.error(f"❌ DNS resolution failed for {hostname}: {e}")
        return False


async def get_pool() -> asyncpg.Pool:
    """Get or create database connection pool."""
    global _pool
    if _pool is None:
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            raise RuntimeError("DATABASE_URL is not set")
        
        # Fix URL encoding issues
        database_url = fix_database_url(database_url)
        
        # Parse and log connection details (without password)
        parsed = urlparse(database_url)
        logger.info(f"Connecting to database: {parsed.hostname}:{parsed.port or 5432}")
        
        # Test DNS resolution first
        if parsed.hostname:
            if not test_dns_resolution(parsed.hostname):
                logger.error(f"Cannot resolve hostname: {parsed.hostname}")
                logger.info("Possible solutions:")
                logger.info("1. Check if DATABASE_URL is correct in Railway variables")
                logger.info("2. Try using IPv4 address instead of hostname")
                logger.info("3. Check Railway networking/DNS settings")
                logger.info("4. Verify Supabase allows connections from Railway IPs")
                raise RuntimeError(f"DNS resolution failed for {parsed.hostname}")
        
        try:
            _pool = await asyncpg.create_pool(dsn=database_url, min_size=1, max_size=10)
            logger.info("✅ Database connection pool created successfully")
        except Exception as e:
            logger.error(f"❌ Failed to create database pool: {e}")
            raise
    
    return _pool


async def close_pool() -> None:
    """Close database connection pool."""
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None
