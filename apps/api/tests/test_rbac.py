import pytest

from app.core.errors import ForbiddenError
from app.core.security import Profile
from app.models.pydantic.common import TaskPatchRequest
from app.services.tasks_service import patch_task


class DummyPool:
    async def fetchrow(self, *_args, **_kwargs):
        # Used by tech-assignment check; by default return None.
        return None


@pytest.mark.asyncio
async def test_tech_cannot_update_non_status_fields():
    pool = DummyPool()
    profile = Profile(id="u", org_id="o", role="tech", email="e", display_name=None)

    with pytest.raises(ForbiddenError):
        await patch_task(
            pool,  # type: ignore[arg-type]
            profile=profile,
            task_id="t",
            req=TaskPatchRequest(required_skill="engine"),
        )
