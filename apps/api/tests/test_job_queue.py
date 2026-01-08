"""Tests for job queue system (Milestone B)."""

import asyncio
import asyncpg
import pytest

from app.services.job_queue_service import enqueue_job, get_job_status, list_jobs


pytestmark = pytest.mark.asyncio


async def test_enqueue_and_get_job(db_pool: asyncpg.Pool, demo_org_id: str) -> None:
    """Test enqueueing a job and retrieving its status."""
    # Enqueue a job
    job_id = await enqueue_job(
        db_pool,
        org_id=demo_org_id,
        job_type="ai_enrich",
        payload={"work_order_id": "test-wo-id"},
        max_attempts=3,
    )
    
    assert job_id is not None
    
    # Get job status
    job = await get_job_status(db_pool, job_id=job_id, org_id=demo_org_id)
    
    assert job is not None
    assert job["id"] == job_id
    assert job["type"] == "ai_enrich"
    assert job["payload"]["work_order_id"] == "test-wo-id"
    assert job["status"] == "queued"
    assert job["attempts"] == 0
    assert job["max_attempts"] == 3


async def test_list_jobs(db_pool: asyncpg.Pool, demo_org_id: str) -> None:
    """Test listing jobs for an organization."""
    # Enqueue multiple jobs
    job_id_1 = await enqueue_job(
        db_pool,
        org_id=demo_org_id,
        job_type="ai_enrich",
        payload={"work_order_id": "wo-1"},
    )
    
    job_id_2 = await enqueue_job(
        db_pool,
        org_id=demo_org_id,
        job_type="schedule_run",
        payload={"schedule_run_id": "sr-1"},
    )
    
    # List all jobs
    jobs = await list_jobs(db_pool, org_id=demo_org_id)
    assert len(jobs) >= 2
    
    job_ids = [job["id"] for job in jobs]
    assert job_id_1 in job_ids
    assert job_id_2 in job_ids
    
    # Filter by type
    ai_jobs = await list_jobs(db_pool, org_id=demo_org_id, job_type="ai_enrich")
    assert all(job["type"] == "ai_enrich" for job in ai_jobs)
    
    # Filter by status
    queued_jobs = await list_jobs(db_pool, org_id=demo_org_id, status="queued")
    assert all(job["status"] == "queued" for job in queued_jobs)


async def test_job_org_isolation(db_pool: asyncpg.Pool, demo_org_id: str) -> None:
    """Test that jobs are isolated by organization."""
    # Create a second org
    org2_id = await db_pool.fetchval(
        """
        insert into public.organizations (name, timezone)
        values ('Test Org 2', 'America/New_York')
        returning id::text
        """
    )
    
    # Enqueue a job for org 1
    job_id_1 = await enqueue_job(
        db_pool,
        org_id=demo_org_id,
        job_type="ai_enrich",
        payload={"work_order_id": "wo-1"},
    )
    
    # Enqueue a job for org 2
    job_id_2 = await enqueue_job(
        db_pool,
        org_id=org2_id,
        job_type="ai_enrich",
        payload={"work_order_id": "wo-2"},
    )
    
    # Org 1 should not see org 2's job
    job = await get_job_status(db_pool, job_id=job_id_2, org_id=demo_org_id)
    assert job is None
    
    # Org 2 should not see org 1's job
    job = await get_job_status(db_pool, job_id=job_id_1, org_id=org2_id)
    assert job is None
    
    # Each org should see only their own jobs
    org1_jobs = await list_jobs(db_pool, org_id=demo_org_id)
    org1_job_ids = [job["id"] for job in org1_jobs]
    assert job_id_1 in org1_job_ids
    assert job_id_2 not in org1_job_ids
    
    org2_jobs = await list_jobs(db_pool, org_id=org2_id)
    org2_job_ids = [job["id"] for job in org2_jobs]
    assert job_id_2 in org2_job_ids
    assert job_id_1 not in org2_job_ids


async def test_concurrent_job_claiming(db_pool: asyncpg.Pool, demo_org_id: str) -> None:
    """Test that FOR UPDATE SKIP LOCKED prevents concurrent job claiming."""
    from app.queue_processor import claim_next_job
    
    # Enqueue a single job
    await enqueue_job(
        db_pool,
        org_id=demo_org_id,
        job_type="ai_enrich",
        payload={"work_order_id": "wo-concurrent"},
    )
    
    # Simulate two workers trying to claim the same job concurrently
    async def claim_job(worker_id: str) -> dict | None:
        return await claim_next_job(db_pool, worker_id)
    
    # Run both claims concurrently
    results = await asyncio.gather(
        claim_job("worker-1"),
        claim_job("worker-2"),
    )
    
    # Only one worker should have claimed the job
    claimed = [r for r in results if r is not None]
    assert len(claimed) == 1
    
    # The other worker should have gotten None
    not_claimed = [r for r in results if r is None]
    assert len(not_claimed) == 1
    
    # Verify the job is marked as running
    job_id = claimed[0]["id"]
    job = await get_job_status(db_pool, job_id=job_id, org_id=demo_org_id)
    assert job["status"] == "running"
    assert job["locked_by"] in ["worker-1", "worker-2"]


async def test_job_retry_logic(db_pool: asyncpg.Pool, demo_org_id: str) -> None:
    """Test job retry logic with exponential backoff."""
    from app.queue_processor import mark_job_failed
    
    # Enqueue a job
    job_id = await enqueue_job(
        db_pool,
        org_id=demo_org_id,
        job_type="ai_enrich",
        payload={"work_order_id": "wo-retry"},
        max_attempts=3,
    )
    
    # Simulate first failure (attempts = 1)
    await mark_job_failed(db_pool, job_id, "Test error 1", 1, 3)
    
    job = await get_job_status(db_pool, job_id=job_id, org_id=demo_org_id)
    assert job["status"] == "queued"  # Requeued for retry
    assert job["error"] == "Test error 1"
    
    # Simulate second failure (attempts = 2)
    await mark_job_failed(db_pool, job_id, "Test error 2", 2, 3)
    
    job = await get_job_status(db_pool, job_id=job_id, org_id=demo_org_id)
    assert job["status"] == "queued"  # Still requeued
    
    # Simulate third failure (attempts = 3, max reached)
    await mark_job_failed(db_pool, job_id, "Test error 3", 3, 3)
    
    job = await get_job_status(db_pool, job_id=job_id, org_id=demo_org_id)
    assert job["status"] == "failed"  # Dead letter
    assert job["error"] == "Test error 3"


async def test_job_success(db_pool: asyncpg.Pool, demo_org_id: str) -> None:
    """Test marking a job as succeeded."""
    from app.queue_processor import claim_next_job, mark_job_succeeded
    
    # Enqueue a job
    await enqueue_job(
        db_pool,
        org_id=demo_org_id,
        job_type="ai_enrich",
        payload={"work_order_id": "wo-success"},
    )
    
    # Claim the job
    job = await claim_next_job(db_pool, "test-worker")
    assert job is not None
    job_id = job["id"]
    
    # Mark as succeeded
    await mark_job_succeeded(db_pool, job_id)
    
    # Verify status
    job = await get_job_status(db_pool, job_id=job_id, org_id=demo_org_id)
    assert job["status"] == "succeeded"
    assert job["locked_at"] is None
    assert job["locked_by"] is None
