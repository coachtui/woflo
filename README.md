# Woflo — Diesel Shop Work Order Scheduler (MVP)

Monorepo implementing the CTO architecture:

- **Backend API**: Python + FastAPI (`apps/api`) deployed to Railway
- **Worker/Scheduler**: Python worker (`apps/worker`) deployed to Railway
- **DB/Auth/Storage**: Supabase Postgres + Auth + Storage
- **Web**: Next.js (planned)
- **Mobile**: Expo (planned)

## Repo layout

```text
/apps
  /api
  /worker
/packages
  /shared
/supabase
  /migrations
/docs
  backlog.md
  milestones_30_60_90.md
DECISION_LOG.md
```

## Local development

### 1) Create env file

```bash
cp .env.example .env
```

Required for most features:

- `DATABASE_URL` (Supabase Postgres or local Postgres)
- `SUPABASE_JWKS_URL` (Supabase project JWKS endpoint)
- `SUPABASE_SERVICE_ROLE_KEY` (server-side only)

LLM keys are only needed once Milestone D begins.

### Run API + worker (no Docker)

API:

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r apps/api/requirements.txt
uvicorn apps.api.main:app --reload --port 8000
```

Worker (separate terminal):

```bash
source .venv/bin/activate
pip install -r apps/worker/requirements.txt
python -m apps.worker.worker
```

## Deploy (Railway + Nixpacks)

We deploy two Railway services from this monorepo:

1) **api**
   - Root directory: repo root
   - Start command: provided by `apps/api/nixpacks.toml`
   - Required env vars (server-side):
     - `DATABASE_URL`
     - `SUPABASE_JWKS_URL`
     - `SUPABASE_SERVICE_ROLE_KEY`

2) **worker**
   - Root directory: repo root
   - Start command: provided by `apps/worker/nixpacks.toml`
   - Required env vars: same as api + `WORKER_ID`

Notes:
- Nixpacks will run the `pip install -r ...` commands from each service’s `nixpacks.toml`.
- Do **not** ship `SUPABASE_SERVICE_ROLE_KEY` or any LLM keys to frontend clients.

## Migrations

MVP uses **raw SQL migrations** committed under `supabase/migrations/`.
Applying migrations will be documented in Phase A.

## Deployment

Railway services:

- `api`: `uvicorn apps.api.main:app --host 0.0.0.0 --port $PORT`
- `worker`: `python -m apps.worker.worker`

## Docs

- `docs/milestones_30_60_90.md`
- `docs/backlog.md`
- `DECISION_LOG.md`
