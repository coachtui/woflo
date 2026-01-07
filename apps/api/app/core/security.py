from __future__ import annotations

import json
import time
from dataclasses import dataclass
from typing import Any, Literal

import httpx
import jwt
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from apps.api.app.core.config import settings
from apps.api.app.core.errors import AuthError, ForbiddenError
from apps.api.app.db.queries import fetchrow
from apps.api.app.db.session import get_pool


Role = Literal["admin", "dispatcher", "tech"]


@dataclass(frozen=True)
class Profile:
    id: str
    org_id: str
    role: Role
    email: str
    display_name: str | None


_bearer = HTTPBearer(auto_error=False)


class JWKSCache:
    def __init__(self) -> None:
        self._jwks: dict[str, Any] | None = None
        self._fetched_at: float = 0
        self.ttl_seconds: int = 60 * 60

    async def get_jwks(self) -> dict[str, Any]:
        if not settings.supabase_jwks_url:
            raise RuntimeError("SUPABASE_JWKS_URL is not set")

        now = time.time()
        if self._jwks is not None and (now - self._fetched_at) < self.ttl_seconds:
            return self._jwks

        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(settings.supabase_jwks_url)
            resp.raise_for_status()
            self._jwks = resp.json()
            self._fetched_at = now
            return self._jwks


_jwks_cache = JWKSCache()


async def verify_supabase_jwt(token: str) -> dict[str, Any]:
    """Verify Supabase JWT using JWKS.

    Assumption (MVP): verify signature + expiry; do not enforce `aud` beyond presence.
    """
    jwks = await _jwks_cache.get_jwks()

    try:
        header = jwt.get_unverified_header(token)
    except jwt.PyJWTError as e:
        raise AuthError(f"Invalid token header: {e}")

    kid = header.get("kid")
    keys = jwks.get("keys", [])
    key = next((k for k in keys if k.get("kid") == kid), None)
    if not key:
        raise AuthError("Signing key not found")

    public_key = jwt.algorithms.RSAAlgorithm.from_jwk(json.dumps(key))

    try:
        claims = jwt.decode(
            token,
            key=public_key,
            algorithms=[header.get("alg", "RS256")],
            options={"verify_aud": False},
        )
        return claims
    except jwt.ExpiredSignatureError:
        raise AuthError("Token expired")
    except jwt.PyJWTError as e:
        raise AuthError(f"Invalid token: {e}")


async def get_current_profile(
    creds: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> Profile:
    if creds is None or creds.scheme.lower() != "bearer":
        raise AuthError("Missing bearer token")

    claims = await verify_supabase_jwt(creds.credentials)
    user_id = claims.get("sub")
    if not user_id:
        raise AuthError("Token missing sub")

    pool = await get_pool()
    row = await fetchrow(
        pool,
        """
        select id::text, org_id::text, role, email, display_name
        from public.profiles
        where id = $1 and is_active = true
        """,
        user_id,
    )
    if not row:
        raise AuthError("Profile not found or inactive")

    role = row["role"]
    if role not in ("admin", "dispatcher", "tech"):
        raise AuthError("Invalid role")

    return Profile(
        id=row["id"],
        org_id=row["org_id"],
        role=role,
        email=row["email"],
        display_name=row["display_name"],
    )


def require_roles(*allowed: Role):
    async def _dep(profile: Profile = Depends(get_current_profile)) -> Profile:
        if profile.role not in allowed:
            raise ForbiddenError("Insufficient role")
        return profile

    return _dep
