# Milestones (CTO 30/60/90)

This is a direct mapping of the CTO 30/60/90 plan into deliverables.

## First 30 days — MVP core scheduling

### Milestone A: Data model + auth + CRUD
Deliverables:
- Supabase schema + SQL migrations + RLS + seed data
- FastAPI JWT verification (Supabase JWKS) → `profiles` lookup
- CRUD: work orders, tasks, techs, bays, calendar events
- Audit log for all mutating endpoints

Acceptance criteria:
- Dispatcher can create a WO + tasks.
- Tech can log in and see only their assigned tasks.
- Audit log records create/update.

### Milestone B: Queue + worker skeleton
Deliverables:
- `job_queue` table + enqueue helper
- Worker loop using `FOR UPDATE SKIP LOCKED`
- Retries + dead-letter behavior

Acceptance criteria:
- Worker handles concurrency using SKIP LOCKED.
- Failed jobs set `status=failed` with error.

### Milestone C: Scheduler v1
Deliverables:
- OR-Tools CP-SAT model:
  - no-overlap tech/bay
  - dependencies
  - parts gate
  - due date penalty
  - lock support
- Writes `schedule_runs` + `schedule_items` + objective breakdown

Acceptance criteria:
- 50-task scenario solves ≤10s locally.
- Locked tasks remain fixed.
- `schedule_runs.objective_breakdown` populated.

## Days 31–60 — AI enrichment + dispatcher UI

### Milestone D: LLM Gateway + enrichment pipeline
Deliverables:
- Pydantic schemas + prompt files + redaction
- Provider routing: Anthropic → repair → OpenAI fallback → needs_review
- Auto task plan generation

Acceptance criteria:
- ≥90% golden set produces valid outputs.
- Invalid outputs route to needs_review.

### Milestone E: Dispatcher dashboard v1 (Next.js)
Deliverables:
- Schedule board + queue + detail view
- Drag-drop move/lock + reopt
- Explain panel for `schedule_items.why`

Acceptance criteria:
- Drag-drop writes override and updates schedule.
- Explain panel shows reasons.

## Days 61–90 — Tech mobile + reoptimization + integrations

### Milestone F: Tech mobile app v1 (Expo)
Deliverables:
- Today list + task detail + attachments upload

Acceptance criteria:
- Tech can update status and upload photos.

### Milestone G: Fast re-optimization
Deliverables:
- Warm start from last schedule
- Partial reopt around changed items (locks respected)

Acceptance criteria:
- Single-change reopt ≤10s on 200 tasks.

### Milestone H: Integration adapter + CSV + webhook prototype
Deliverables:
- CSV import/export endpoints
- Webhook endpoint (signed secret)

Acceptance criteria:
- Import 100 WOs from CSV and schedule them.
