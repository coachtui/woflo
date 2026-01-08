# Job Queue System (Milestone B)

## Overview

The job queue system provides async job processing with concurrency control, retry logic, and dead-letter behavior. It uses PostgreSQL's `FOR UPDATE SKIP LOCKED` to enable multiple workers to safely process jobs concurrently.

## Architecture

### Components

1. **Job Queue Table** (`public.job_queue`)
   - Stores jobs to be processed
   - Status: `queued`, `running`, `succeeded`, `failed`
   - Supports retry with exponential backoff
   - Dead-letter for permanently failed jobs

2. **API Service** (`apps/api/app/services/job_queue_service.py`)
   - `enqueue_job()` - Add jobs to the queue
   - `get_job_status()` - Check job status
   - `list_jobs()` - List jobs for an organization

3. **Worker** (`apps/worker/`)
   - Continuously polls for jobs
   - Uses `FOR UPDATE SKIP LOCKED` for safe concurrency
   - Processes jobs and updates status
   - Graceful shutdown on SIGTERM/SIGINT

4. **Job Handlers** (`apps/worker/app/handlers/`)
   - `ai_enrich` - AI enrichment (stub for Milestone D)
   - `schedule_run` - Scheduler execution (stub for Milestone C)

## Job Types

### ai_enrich
Enriches work orders with AI-generated task plans.

**Payload:**
```json
{
  "work_order_id": "uuid",
  "pipeline": "extract|classify|estimate|risk"
}
```

### schedule_run
Runs the OR-Tools scheduler to create a schedule.

**Payload:**
```json
{
  "schedule_run_id": "uuid",
  "horizon_start": "2026-01-07T00:00:00Z",
  "horizon_end": "2026-01-14T00:00:00Z"
}
```

## Concurrency Control

The system uses PostgreSQL's `FOR UPDATE SKIP LOCKED` to ensure safe concurrent processing:

```sql
select id
from public.job_queue
where status = 'queued' and run_after <= now()
order by run_after, created_at
limit 1
for update skip locked
```

This allows multiple workers to process different jobs simultaneously without conflicts.

## Retry Logic

Failed jobs are automatically retried with exponential backoff:

- **Attempt 1**: Immediate retry
- **Attempt 2**: Retry after 2 minutes
- **Attempt 3**: Retry after 4 minutes
- **Attempt 4+**: Retry after 8, 16, 32... minutes

After `max_attempts` (default: 3), jobs enter the dead-letter queue with `status='failed'`.

## API Endpoints

### POST /v1/jobs
Enqueue a new job (admin/dispatcher only).

**Request:**
```json
{
  "type": "ai_enrich",
  "payload": {
    "work_order_id": "123e4567-e89b-12d3-a456-426614174000"
  },
  "max_attempts": 3
}
```

**Response:**
```json
{
  "job_id": "789e4567-e89b-12d3-a456-426614174999"
}
```

### GET /v1/jobs/{job_id}
Get job status.

**Response:**
```json
{
  "id": "789e4567-e89b-12d3-a456-426614174999",
  "org_id": "...",
  "type": "ai_enrich",
  "payload": {...},
  "status": "succeeded",
  "run_after": "2026-01-07T00:00:00Z",
  "attempts": 1,
  "max_attempts": 3,
  "locked_at": null,
  "locked_by": null,
  "error": null,
  "created_at": "2026-01-07T00:00:00Z",
  "updated_at": "2026-01-07T00:00:05Z"
}
```

### GET /v1/jobs
List jobs for current organization.

**Query Parameters:**
- `status` - Filter by status (optional)
- `type` - Filter by type (optional)
- `limit` - Max results (default: 100, max: 1000)

## Worker Deployment

### Environment Variables

- `DATABASE_URL` - PostgreSQL connection string (required)
- `WORKER_ID` - Worker identifier (default: "worker-1")
- `POLL_INTERVAL_SECONDS` - Poll interval in seconds (default: 2)

### Running Locally

```bash
cd apps/worker
export DATABASE_URL="postgresql://..."
python worker.py
```

### Running Multiple Workers

For high throughput, run multiple worker instances:

```bash
# Terminal 1
WORKER_ID=worker-1 python worker.py

# Terminal 2
WORKER_ID=worker-2 python worker.py

# Terminal 3
WORKER_ID=worker-3 python worker.py
```

Each worker will safely claim and process different jobs.

### Railway Deployment

The worker is already configured for Railway deployment via `nixpacks.toml` and `start.sh`.

## Monitoring

### Check Queue Status

```sql
select status, count(*)
from public.job_queue
group by status;
```

### View Failed Jobs

```sql
select id, type, attempts, error, created_at
from public.job_queue
where status = 'failed'
order by created_at desc
limit 10;
```

### Worker Logs

Workers emit structured JSON logs:
- `worker_started` - Worker startup
- `job_processing_started` - Job claimed
- `job_processing_succeeded` - Job completed
- `job_processing_failed` - Job failed
- `job_retry_scheduled` - Job queued for retry
- `job_dead_letter` - Job permanently failed
- `worker_shutting_down` - Graceful shutdown

## Testing

### Enqueue a Test Job (API)

```bash
curl -X POST http://localhost:8000/v1/jobs \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "ai_enrich",
    "payload": {"work_order_id": "123e4567-e89b-12d3-a456-426614174000"},
    "max_attempts": 3
  }'
```

### Check Job Status

```bash
curl http://localhost:8000/v1/jobs/{job_id} \
  -H "Authorization: Bearer $TOKEN"
```

### Enqueue Directly (SQL)

```sql
insert into public.job_queue (org_id, type, payload, status, run_after, max_attempts)
values (
  'org-uuid'::uuid,
  'ai_enrich',
  '{"work_order_id": "wo-uuid"}'::jsonb,
  'queued',
  now(),
  3
);
```

## Next Steps

### Milestone C: Scheduler v1
Implement the `schedule_run` handler with OR-Tools CP-SAT:
- Load tasks, technicians, bays, constraints
- Build CP-SAT model
- Solve and store results
- Handle infeasible cases

### Milestone D: LLM Gateway
Implement the `ai_enrich` handler:
- Call Claude/GPT APIs
- Parse and validate responses
- Implement provider fallback
- Store enrichment results

## Troubleshooting

### Jobs stuck in "running" status

If a worker crashes while processing, jobs may be stuck in "running". Reset them:

```sql
update public.job_queue
set status = 'queued', locked_at = null, locked_by = null
where status = 'running'
  and locked_at < now() - interval '10 minutes';
```

### High retry rate

Check error messages:
```sql
select type, error, count(*)
from public.job_queue
where status = 'failed' or attempts > 1
group by type, error;
```

### Worker not processing jobs

1. Check DATABASE_URL is set
2. Verify database connectivity
3. Check worker logs for errors
4. Ensure jobs exist with `status='queued'` and `run_after <= now()`
