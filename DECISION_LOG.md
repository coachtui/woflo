# Decision Log

This file records implementation decisions made to fill gaps while staying within CTO intent.

## 2026-01-06 — Repo scaffolding decisions

1) **Monorepo packaging**
   - Decision: keep each service as a Python package under `apps/` and share code through `packages/shared`.
   - Rationale: matches CTO layout and keeps Railway deploys simple.

2) **Migrations approach**
   - Decision: use raw SQL migrations in `supabase/migrations/` for MVP.
   - Rationale: explicitly specified by CTO.

3) **Local parity**
   - Decision (updated): local workflow runs directly on host Python (no Docker). Deploys use Railway **Nixpacks**.
   - Rationale: Docker is not available in this environment; Nixpacks is preferred for Railway deploy.

4) **Python version**
   - Decision: Railway deploy uses Python **3.12** (Nixpacks). Local dev may run Python 3.9+.
   - Rationale: CTO wants modern stack on Railway; local machines may lag.

4b) **Pydantic typing compatibility for local Python <3.10**
   - Decision: include `eval-type-backport` so Pydantic can evaluate `str | None` style annotations when running tests under Python 3.9.
   - Options considered:
     - Add backport dependency (chosen)
     - Rewrite all annotations to `typing.Optional[...]` (more churn)
   - Rollback plan: remove dependency once local tooling standardizes on Python 3.10+.

5) **Raw LLM response storage**
   - Decision: keep `ai_results.raw_response` as specified, but plan to enforce access via RLS policies + role checks. If column-level restriction proves insufficient, we will split raw responses into a separate table restricted to dispatcher/admin only.
   - Rationale: CTO requires strict access; Supabase RLS is row-level, so we may need a separate table to fully enforce.

6) **Supabase JWT verification strategy (API)**
   - Decision: verify Supabase JWTs via `SUPABASE_JWKS_URL` (cached) using PyJWT, then load the user’s `profiles` row.
   - Options considered:
     - JWKS verification (chosen)
     - Supabase Auth introspection endpoint (not chosen; more moving parts)
   - Why chosen: matches CTO spec (JWKS) and keeps API stateless.
   - Expected impact: consistent auth behavior across services; minimal latency due to JWKS caching.
   - Rollback plan: swap to introspection if JWKS changes unexpectedly.

7) **Phase B scope adjustment: deprioritize Bays + PTO endpoints**
   - Decision: per delivery owner direction, skip implementing Bays CRUD and PTO/training calendar management endpoints for MVP Phase B.
   - Options considered:
     - Implement full CTO Milestone A CRUD surface (bays + calendar events) now
     - Defer bays + PTO management and focus on WO/Tasks + auth (chosen)
   - Why chosen: reduces MVP scope and keeps delivery focused; holidays will be treated as standard GCA holidays (handled later as static config or seed data).
   - Expected impact: scheduler will initially run without bay constraints and without PTO exceptions until Phase D introduces those constraints.
   - Rollback plan: add `admin` endpoints + calendar event CRUD later without breaking existing API.

8) **Auto-provision profiles on Supabase Auth signup (MVP)**
   - Decision: add a DB trigger on `auth.users` insert to upsert a `public.profiles` row.
   - Defaults:
     - org: `Demo Diesel Shop`
     - role: `tech`
   - Why chosen: simplest safe default that unblocks API usage without manually inserting profiles.
   - Expected impact: any new auth signup becomes a tech in the demo org.
   - Rollback plan: remove/replace trigger when we introduce invites / org assignment.

9) **Job queue implementation (Milestone B)**
   - Decision: use PostgreSQL `FOR UPDATE SKIP LOCKED` for concurrent job processing
   - Options considered:
     - Redis queue with workers (external dependency)
     - PostgreSQL-based queue (chosen)
     - Message broker like RabbitMQ (too complex for MVP)
   - Why chosen:
     - No additional infrastructure required
     - ACID guarantees from PostgreSQL
     - Simple deployment (worker just needs DATABASE_URL)
     - Natural fit with existing asyncpg stack
   - Implementation details:
     - Exponential backoff retry: 2^attempts minutes
     - Dead-letter after max_attempts (default: 3)
     - Graceful shutdown on SIGTERM/SIGINT
     - Job handlers are stubs for Milestone C (scheduler) and D (AI enrichment)
   - Expected impact: enables async job processing for scheduler and AI enrichment
   - Rollback plan: if PostgreSQL queue becomes a bottleneck (unlikely at <10k jobs/day), migrate to dedicated queue service

10) **OR-Tools CP-SAT scheduler (Milestone C)**
   - Decision: use Google OR-Tools CP-SAT solver for constraint-based scheduling
   - Options considered:
     - Custom greedy heuristic (too simplistic for complex constraints)
     - OR-Tools CP-SAT (chosen)
     - Commercial solvers like Gurobi (cost prohibitive)
     - Genetic algorithms (unpredictable solution quality)
   - Why chosen:
     - Free, open-source, production-ready
     - Native support for no-overlap, time windows, assignments
     - Proven performance on scheduling problems
     - Rich constraint modeling capabilities
     - Good documentation and Python API
   - Implementation details:
     - Time horizon converted to minutes for integer domain
     - Optional intervals for tech/bay assignment flexibility
     - Locked tasks modeled as fixed intervals that block resources
     - Soft constraints (skills, parts) via penalty variables
     - Hard constraints (bay type) via allowed assignments
     - Objective minimizes: due date penalties + priority penalties + skill mismatch + parts not ready
     - 30-second default time limit (configurable)
     - Detailed infeasibility analysis when no solution found
   - Expected impact: automated optimal scheduling respecting all constraints
   - Rollback plan: if CP-SAT proves too slow (>30s for typical problems), consider simplifying model or using heuristics for initial solution
