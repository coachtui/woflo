# Worker Service

Async job processor for Woflo using PostgreSQL-based queue with `FOR UPDATE SKIP LOCKED` for concurrency control.

## Quick Start

```bash
# Set environment variables
export DATABASE_URL="postgresql://user:pass@host:5432/db"
export WORKER_ID="worker-1"
export POLL_INTERVAL_SECONDS="2"

# Run worker
python worker.py
```

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DATABASE_URL` | Yes | - | PostgreSQL connection string |
| `WORKER_ID` | No | `worker-1` | Worker identifier for logging |
| `POLL_INTERVAL_SECONDS` | No | `2` | Seconds between job polls |

## Job Types

### ai_enrich
AI enrichment for work orders (stub - implemented in Milestone D)

### schedule_run
Schedule optimization with OR-Tools CP-SAT (stub - implemented in Milestone C)

## Features

- ✅ **Concurrency-safe**: Multiple workers can run simultaneously
- ✅ **Retry logic**: Exponential backoff (2^attempts minutes)
- ✅ **Dead-letter queue**: Failed jobs marked after max_attempts
- ✅ **Graceful shutdown**: Handles SIGTERM/SIGINT
- ✅ **Structured logging**: JSON logs for monitoring

## Architecture

```
┌──────────┐
│   API    │ ──enqueue──> job_queue table
└──────────┘                    │
                                │ FOR UPDATE SKIP LOCKED
                                ↓
                         ┌──────────┐
                         │ Worker 1 │ ──process──> Handler
                         └──────────┘
                         ┌──────────┐
                         │ Worker 2 │ ──process──> Handler
                         └──────────┘
                         ┌──────────┐
                         │ Worker N │ ──process──> Handler
                         └──────────┘
```

## Deployment

### Railway

Worker is pre-configured for Railway deployment:
- `nixpacks.toml` specifies Python 3.12
- `start.sh` runs the worker
- Set `DATABASE_URL` in Railway environment

### Local Development

```bash
cd apps/worker
pip install -r requirements.txt
python worker.py
```

## Monitoring

Watch worker logs:
```bash
tail -f worker.log | jq '.'
```

Check queue status (SQL):
```sql
select status, count(*) from public.job_queue group by status;
```

## Documentation

See [docs/job_queue.md](../../docs/job_queue.md) for full documentation.
