import pytest

from app.core.security import verify_supabase_jwt


@pytest.mark.asyncio
async def test_verify_supabase_jwt_requires_jwks_url(monkeypatch):
    # This test asserts we fail fast if JWKS URL is not set.
    from app.core import config

    monkeypatch.setattr(config.settings, "supabase_jwks_url", None)

    with pytest.raises(RuntimeError):
        await verify_supabase_jwt("not-a-real-token")
