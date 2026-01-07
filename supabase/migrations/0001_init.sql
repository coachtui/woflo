-- 0001_init.sql
-- Core schema per CTO spec.

create extension if not exists pgcrypto;

-- ---------- helpers ----------
create or replace function public.set_updated_at()
returns trigger
language plpgsql
as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

-- ---------- organizations ----------
create table if not exists public.organizations (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  timezone text not null,
  created_at timestamptz not null default now(),
  updated_at timestamptz
);

create index if not exists organizations_name_idx on public.organizations (name);

create trigger organizations_set_updated_at
before update on public.organizations
for each row execute function public.set_updated_at();

-- ---------- profiles ----------
create table if not exists public.profiles (
  id uuid primary key,
  org_id uuid not null references public.organizations(id) on delete cascade,
  email text not null,
  display_name text,
  role text not null check (role in ('admin','dispatcher','tech')),
  is_active boolean not null default true,
  created_at timestamptz not null default now(),
  updated_at timestamptz
);

create index if not exists profiles_org_role_idx on public.profiles (org_id, role);
create index if not exists profiles_email_idx on public.profiles (email);

create trigger profiles_set_updated_at
before update on public.profiles
for each row execute function public.set_updated_at();

-- ---------- technicians ----------
create table if not exists public.technicians (
  id uuid primary key default gen_random_uuid(),
  org_id uuid not null references public.organizations(id) on delete cascade,
  profile_id uuid unique null references public.profiles(id) on delete set null,
  name text not null,
  efficiency_multiplier numeric not null default 1.0,
  overtime_allowed boolean not null default true,
  wip_limit int not null default 3,
  created_at timestamptz not null default now(),
  updated_at timestamptz
);

create index if not exists technicians_org_name_idx on public.technicians (org_id, name);

create trigger technicians_set_updated_at
before update on public.technicians
for each row execute function public.set_updated_at();

-- ---------- technician_skills ----------
create table if not exists public.technician_skills (
  id uuid primary key default gen_random_uuid(),
  org_id uuid not null references public.organizations(id) on delete cascade,
  technician_id uuid not null references public.technicians(id) on delete cascade,
  skill text not null,
  level int not null check (level between 1 and 5),
  is_safety_critical boolean not null default false,
  created_at timestamptz not null default now(),
  updated_at timestamptz
);

create index if not exists technician_skills_org_tech_idx on public.technician_skills (org_id, technician_id);
create index if not exists technician_skills_org_skill_idx on public.technician_skills (org_id, skill);

create trigger technician_skills_set_updated_at
before update on public.technician_skills
for each row execute function public.set_updated_at();

-- ---------- bays ----------
create table if not exists public.bays (
  id uuid primary key default gen_random_uuid(),
  org_id uuid not null references public.organizations(id) on delete cascade,
  name text not null,
  bay_type text not null,
  capacity int not null default 1,
  is_active boolean not null default true,
  created_at timestamptz not null default now(),
  updated_at timestamptz
);

create index if not exists bays_org_bay_type_idx on public.bays (org_id, bay_type);
create index if not exists bays_org_active_idx on public.bays (org_id, is_active);

create trigger bays_set_updated_at
before update on public.bays
for each row execute function public.set_updated_at();

-- ---------- bay_hours ----------
create table if not exists public.bay_hours (
  id uuid primary key default gen_random_uuid(),
  org_id uuid not null references public.organizations(id) on delete cascade,
  bay_id uuid not null references public.bays(id) on delete cascade,
  day_of_week int not null check (day_of_week between 0 and 6),
  start_time time not null,
  end_time time not null,
  created_at timestamptz not null default now(),
  updated_at timestamptz,
  unique (bay_id, day_of_week, start_time, end_time)
);

create trigger bay_hours_set_updated_at
before update on public.bay_hours
for each row execute function public.set_updated_at();

-- ---------- shifts ----------
create table if not exists public.shifts (
  id uuid primary key default gen_random_uuid(),
  org_id uuid not null references public.organizations(id) on delete cascade,
  name text not null,
  start_time time not null,
  end_time time not null,
  created_at timestamptz not null default now(),
  updated_at timestamptz
);

create trigger shifts_set_updated_at
before update on public.shifts
for each row execute function public.set_updated_at();

-- ---------- technician_shift_assignments ----------
create table if not exists public.technician_shift_assignments (
  id uuid primary key default gen_random_uuid(),
  org_id uuid not null references public.organizations(id) on delete cascade,
  technician_id uuid not null references public.technicians(id) on delete cascade,
  shift_id uuid not null references public.shifts(id) on delete cascade,
  effective_from date not null,
  effective_to date null,
  created_at timestamptz not null default now(),
  updated_at timestamptz
);

create index if not exists tech_shift_assignments_tech_from_idx
  on public.technician_shift_assignments (technician_id, effective_from);

create trigger technician_shift_assignments_set_updated_at
before update on public.technician_shift_assignments
for each row execute function public.set_updated_at();

-- ---------- calendar_events ----------
create table if not exists public.calendar_events (
  id uuid primary key default gen_random_uuid(),
  org_id uuid not null references public.organizations(id) on delete cascade,
  technician_id uuid null references public.technicians(id) on delete cascade,
  type text not null check (type in ('pto','training','holiday','sick')),
  start_at timestamptz not null,
  end_at timestamptz not null,
  notes text,
  created_at timestamptz not null default now(),
  updated_at timestamptz
);

create index if not exists calendar_events_org_tech_start_idx on public.calendar_events (org_id, technician_id, start_at);

create trigger calendar_events_set_updated_at
before update on public.calendar_events
for each row execute function public.set_updated_at();

-- ---------- units ----------
create table if not exists public.units (
  id uuid primary key default gen_random_uuid(),
  org_id uuid not null references public.organizations(id) on delete cascade,
  unit_number text not null,
  asset_type text not null,
  customer_name_redacted text,
  created_at timestamptz not null default now(),
  updated_at timestamptz
);

create index if not exists units_org_unit_number_idx on public.units (org_id, unit_number);

create trigger units_set_updated_at
before update on public.units
for each row execute function public.set_updated_at();

-- ---------- work_orders ----------
create table if not exists public.work_orders (
  id uuid primary key default gen_random_uuid(),
  org_id uuid not null references public.organizations(id) on delete cascade,
  unit_id uuid not null references public.units(id) on delete restrict,
  asset_type text not null,
  job_category text,
  priority int not null check (priority between 1 and 5),
  due_date date,
  customer_commitment_at timestamptz,
  location text not null check (location in ('shop','field')),
  notes text,
  status text not null check (status in ('new','triage','scheduled','in_progress','blocked_parts','done','canceled')),
  parts_required boolean not null default false,
  parts_status text not null default 'unknown' check (parts_status in ('unknown','not_ordered','ordered','partial','ready')),
  parts_ready boolean not null default false,
  parts_ready_at timestamptz,
  estimated_hours_low numeric,
  estimated_hours_high numeric,
  required_bay_type text,
  required_tools jsonb,
  dependencies jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz
);

create index if not exists work_orders_org_status_idx on public.work_orders (org_id, status);
create index if not exists work_orders_org_priority_due_idx on public.work_orders (org_id, priority desc, due_date);
create index if not exists work_orders_org_parts_ready_idx on public.work_orders (org_id, parts_ready);

create trigger work_orders_set_updated_at
before update on public.work_orders
for each row execute function public.set_updated_at();

-- ---------- tasks ----------
create table if not exists public.tasks (
  id uuid primary key default gen_random_uuid(),
  org_id uuid not null references public.organizations(id) on delete cascade,
  work_order_id uuid not null references public.work_orders(id) on delete cascade,
  type text not null check (type in ('diagnose','repair','qa_test','road_test','cleanup','paperwork')),
  status text not null check (status in ('todo','scheduled','in_progress','done','blocked')),
  required_skill text,
  required_skill_is_hard boolean not null default false,
  required_bay_type text,
  required_tools jsonb,
  earliest_start timestamptz,
  latest_finish timestamptz,
  duration_minutes_low int not null,
  duration_minutes_high int not null,
  lock_flag boolean not null default false,
  locked_tech_id uuid null references public.technicians(id) on delete set null,
  locked_bay_id uuid null references public.bays(id) on delete set null,
  locked_start_at timestamptz,
  locked_end_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz
);

create index if not exists tasks_org_work_order_idx on public.tasks (org_id, work_order_id);
create index if not exists tasks_org_status_idx on public.tasks (org_id, status);
create index if not exists tasks_org_required_bay_type_idx on public.tasks (org_id, required_bay_type);

create trigger tasks_set_updated_at
before update on public.tasks
for each row execute function public.set_updated_at();

-- ---------- parts ----------
create table if not exists public.parts (
  id uuid primary key default gen_random_uuid(),
  org_id uuid not null references public.organizations(id) on delete cascade,
  work_order_id uuid not null references public.work_orders(id) on delete cascade,
  name text not null,
  qty int not null,
  eta_at timestamptz,
  status text not null check (status in ('needed','ordered','received','canceled')),
  reserved boolean not null default false,
  created_at timestamptz not null default now(),
  updated_at timestamptz
);

create index if not exists parts_org_work_order_idx on public.parts (org_id, work_order_id);
create index if not exists parts_org_status_eta_idx on public.parts (org_id, status, eta_at);

create trigger parts_set_updated_at
before update on public.parts
for each row execute function public.set_updated_at();

-- ---------- attachments ----------
create table if not exists public.attachments (
  id uuid primary key default gen_random_uuid(),
  org_id uuid not null references public.organizations(id) on delete cascade,
  work_order_id uuid null references public.work_orders(id) on delete cascade,
  task_id uuid null references public.tasks(id) on delete cascade,
  bucket text not null,
  path text not null,
  content_type text,
  uploaded_by uuid not null,
  created_at timestamptz not null default now(),
  updated_at timestamptz
);

create index if not exists attachments_org_work_order_idx on public.attachments (org_id, work_order_id);
create index if not exists attachments_org_task_idx on public.attachments (org_id, task_id);

create trigger attachments_set_updated_at
before update on public.attachments
for each row execute function public.set_updated_at();

-- ---------- schedule_runs ----------
create table if not exists public.schedule_runs (
  id uuid primary key default gen_random_uuid(),
  org_id uuid not null references public.organizations(id) on delete cascade,
  horizon_start timestamptz not null,
  horizon_end timestamptz not null,
  status text not null check (status in ('queued','running','succeeded','failed','canceled')),
  trigger text not null check (trigger in ('manual','auto_parts','auto_callout','auto_hot_job','override')),
  locked_task_count int not null default 0,
  task_count int not null default 0,
  solver_wall_time_ms int,
  objective_value numeric,
  objective_breakdown jsonb,
  solver_status text,
  infeasible_reason text,
  created_by uuid,
  created_at timestamptz not null default now(),
  updated_at timestamptz
);

create index if not exists schedule_runs_org_created_at_idx on public.schedule_runs (org_id, created_at desc);
create index if not exists schedule_runs_org_status_idx on public.schedule_runs (org_id, status);

create trigger schedule_runs_set_updated_at
before update on public.schedule_runs
for each row execute function public.set_updated_at();

-- ---------- schedule_items ----------
create table if not exists public.schedule_items (
  id uuid primary key default gen_random_uuid(),
  org_id uuid not null references public.organizations(id) on delete cascade,
  schedule_run_id uuid not null references public.schedule_runs(id) on delete cascade,
  task_id uuid not null references public.tasks(id) on delete cascade,
  technician_id uuid not null references public.technicians(id) on delete cascade,
  bay_id uuid not null references public.bays(id) on delete cascade,
  start_at timestamptz not null,
  end_at timestamptz not null,
  is_locked boolean not null default false,
  why jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz
);

create index if not exists schedule_items_org_tech_start_idx on public.schedule_items (org_id, technician_id, start_at);
create index if not exists schedule_items_org_bay_start_idx on public.schedule_items (org_id, bay_id, start_at);

create trigger schedule_items_set_updated_at
before update on public.schedule_items
for each row execute function public.set_updated_at();

-- ---------- schedule_overrides ----------
create table if not exists public.schedule_overrides (
  id uuid primary key default gen_random_uuid(),
  org_id uuid not null references public.organizations(id) on delete cascade,
  task_id uuid not null references public.tasks(id) on delete cascade,
  action text not null check (action in ('move','assign','unassign','lock','unlock')),
  from_value jsonb,
  to_value jsonb,
  reason text,
  created_by uuid,
  created_at timestamptz not null default now(),
  updated_at timestamptz
);

create index if not exists schedule_overrides_org_task_created_idx
  on public.schedule_overrides (org_id, task_id, created_at desc);

create trigger schedule_overrides_set_updated_at
before update on public.schedule_overrides
for each row execute function public.set_updated_at();

-- ---------- ai_jobs ----------
create table if not exists public.ai_jobs (
  id uuid primary key default gen_random_uuid(),
  org_id uuid not null references public.organizations(id) on delete cascade,
  work_order_id uuid not null references public.work_orders(id) on delete cascade,
  status text not null check (status in ('queued','running','succeeded','failed','needs_review')),
  pipeline text not null,
  step text not null check (step in ('extract','classify','estimate','risk')),
  provider text,
  model text,
  prompt_version text,
  input_redacted text,
  error text,
  created_at timestamptz not null default now(),
  updated_at timestamptz
);

create index if not exists ai_jobs_org_work_order_created_idx on public.ai_jobs (org_id, work_order_id, created_at desc);
create index if not exists ai_jobs_org_status_idx on public.ai_jobs (org_id, status);

create trigger ai_jobs_set_updated_at
before update on public.ai_jobs
for each row execute function public.set_updated_at();

-- ---------- ai_results ----------
create table if not exists public.ai_results (
  id uuid primary key default gen_random_uuid(),
  org_id uuid not null references public.organizations(id) on delete cascade,
  ai_job_id uuid not null references public.ai_jobs(id) on delete cascade,
  work_order_id uuid not null references public.work_orders(id) on delete cascade,
  result jsonb not null,
  raw_response jsonb,
  confidence numeric,
  created_at timestamptz not null default now(),
  updated_at timestamptz
);

create index if not exists ai_results_org_work_order_idx on public.ai_results (org_id, work_order_id);
create index if not exists ai_results_org_ai_job_idx on public.ai_results (org_id, ai_job_id);

create trigger ai_results_set_updated_at
before update on public.ai_results
for each row execute function public.set_updated_at();

-- ---------- audit_log ----------
create table if not exists public.audit_log (
  id uuid primary key default gen_random_uuid(),
  org_id uuid not null references public.organizations(id) on delete cascade,
  actor_id uuid not null,
  entity_type text not null check (entity_type in ('work_order','task','schedule','parts','ai_job')),
  entity_id uuid not null,
  action text not null check (action in ('create','update','delete','lock','unlock','schedule_run','override')),
  diff jsonb,
  reason text,
  created_at timestamptz not null default now()
);

create index if not exists audit_log_org_created_at_idx on public.audit_log (org_id, created_at desc);
create index if not exists audit_log_org_entity_idx on public.audit_log (org_id, entity_type, entity_id);

-- ---------- job_queue ----------
create table if not exists public.job_queue (
  id uuid primary key default gen_random_uuid(),
  org_id uuid not null references public.organizations(id) on delete cascade,
  type text not null check (type in ('ai_enrich','schedule_run')),
  payload jsonb not null,
  status text not null check (status in ('queued','running','succeeded','failed')),
  run_after timestamptz not null default now(),
  attempts int not null default 0,
  max_attempts int not null default 3,
  locked_at timestamptz,
  locked_by text,
  error text,
  created_at timestamptz not null default now(),
  updated_at timestamptz
);

create index if not exists job_queue_status_run_after_idx on public.job_queue (status, run_after);
create index if not exists job_queue_org_status_idx on public.job_queue (org_id, status);

create trigger job_queue_set_updated_at
before update on public.job_queue
for each row execute function public.set_updated_at();
