from __future__ import annotations

from fastapi import APIRouter, Depends

from app.core.security import Profile, get_current_profile


router = APIRouter(prefix="/v1")


@router.get("/me")
async def me(profile: Profile = Depends(get_current_profile)) -> dict:
    """Return the authenticated user's resolved profile (from public.profiles)."""
    return {
        "id": profile.id,
        "org_id": profile.org_id,
        "role": profile.role,
        "email": profile.email,
        "display_name": profile.display_name,
    }
