# Backlog (Jira-style)

This backlog mirrors the CTO’s vertical-slice delivery order (A → G). Each story should ship end-to-end when feasible.

## Epic A — Supabase schema + RLS + seed data

### Story A1 — Create SQL migrations for core schema
Tasks:
- Add raw SQL migration(s) for all tables defined in CTO spec
- Add indexes + constraints

Acceptance criteria:
- `supabase/migrations` contains ordered SQL scripts
- Migrations apply cleanly on empty Postgres

### Story A2 — Enable RLS + core policies
Tasks:
- Enable RLS on all core tables
- Policies:
  - org partitioning via `profiles.org_id`
  - dispatcher/admin full org access
  - tech access limited to assigned tasks/schedule
  - restrict `ai_results.raw_response`

Acceptance criteria:
- Cross-org reads/writes prevented
- Tech cannot view other tech schedules
- Tech cannot access raw LLM responses

### Story A3 — Seed data for one shop
Tasks:
- Insert one org, sample bays, shifts, technicians, skills

Acceptance criteria:
- Seed script loads and can schedule sample tasks later

## Epic B — FastAPI core endpoints

### Story B1 — FastAPI service skeleton + health + OpenAPI
Acceptance criteria:
- `/health` returns OK
- OpenAPI served at `/docs`

### Story B2 — Supabase JWT verification + RBAC
Acceptance criteria:
- API rejects invalid JWT
- Role mapping enforced for dispatcher/admin/tech

### Story B3 — CRUD: work orders + tasks
Acceptance criteria:
- `POST /v1/work-orders` creates WO
- `POST /v1/work-orders/{wo_id}/tasks` creates/replaces tasks
- Tech can update only assigned task statuses

### Story B4 — CRUD: techs + bays + calendar events
Acceptance criteria:
- Dispatcher/admin can manage resources

> **Deprioritized**: Bays + PTO/training calendar endpoints are deferred per delivery owner direction.

### Story B5 — Audit log on all mutations
Acceptance criteria:
- Each create/update/delete writes `audit_log`

## Epic C — AI enrichment pipeline

### Story C1 — LLM Gateway with schema validation + fallback
Acceptance criteria:
- Invalid JSON triggers one repair retry
- Second failure triggers OpenAI fallback
- Third failure routes to `needs_review`

### Story C2 — Async AI enrich job via DB queue
Acceptance criteria:
- API enqueues job; worker processes; results persist

## Epic D — Scheduler worker

### Story D1 — DB queue schedule_run job + locking
Acceptance criteria:
- Enqueue schedule run; worker writes `schedule_runs` + `schedule_items`
- Locked tasks never moved

### Story D2 — CP-SAT constraints + objective breakdown
Acceptance criteria:
- Objective breakdown stored per run
- INFEASIBLE runs store readable `infeasible_reason`

### Story D3 — Explainability payload
Acceptance criteria:
- Each schedule item has `why.penalty_contributions`

## Epic E — Dispatcher Web (Next.js)

### Story E1 — Auth + schedule board + WO queue
Acceptance criteria:
- Dispatcher can see schedule + queue

### Story E2 — Drag-drop move/lock + reopt
Acceptance criteria:
- Move creates override; schedule updates within 2s

## Epic F — Tech Mobile (Expo)

### Story F1 — Today view + task updates + photos
Acceptance criteria:
- Tech can update status and upload attachments

## Epic G — Integrations

### Story G1 — CSV import/export
Acceptance criteria:
- Import 100 WOs; export date range

### Story G2 — Webhook adapter stub
Acceptance criteria:
- Signed endpoint accepts inbound WO updates (stub)
