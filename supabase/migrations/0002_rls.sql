-- 0002_rls.sql
-- Enable RLS + policies per CTO outline.
-- Notes:
-- - Supabase `service_role` bypasses RLS (api/worker will use service role for server-side operations).
-- - Client access is constrained via these policies.

-- ---------- helper functions ----------
create or replace function public.current_org_id()
returns uuid
language sql
stable
security definer
set search_path = public
as $$
  select org_id from public.profiles where id = auth.uid();
$$;

create or replace function public.current_role()
returns text
language sql
stable
security definer
set search_path = public
as $$
  select role from public.profiles where id = auth.uid();
$$;

grant execute on function public.current_org_id() to authenticated;
grant execute on function public.current_role() to authenticated;

-- ---------- enable RLS everywhere ----------
alter table public.organizations enable row level security;
alter table public.profiles enable row level security;
alter table public.technicians enable row level security;
alter table public.technician_skills enable row level security;
alter table public.bays enable row level security;
alter table public.bay_hours enable row level security;
alter table public.shifts enable row level security;
alter table public.technician_shift_assignments enable row level security;
alter table public.calendar_events enable row level security;
alter table public.units enable row level security;
alter table public.work_orders enable row level security;
alter table public.tasks enable row level security;
alter table public.parts enable row level security;
alter table public.attachments enable row level security;
alter table public.schedule_runs enable row level security;
alter table public.schedule_items enable row level security;
alter table public.schedule_overrides enable row level security;
alter table public.ai_jobs enable row level security;
alter table public.ai_results enable row level security;
alter table public.audit_log enable row level security;
alter table public.job_queue enable row level security;

-- ---------- organizations ----------
drop policy if exists organizations_select on public.organizations;
create policy organizations_select
on public.organizations
for select
to authenticated
using (id = public.current_org_id());

drop policy if exists organizations_update_admin_dispatcher on public.organizations;
create policy organizations_update_admin_dispatcher
on public.organizations
for update
to authenticated
using (
  id = public.current_org_id()
  and public.current_role() in ('admin','dispatcher')
)
with check (
  id = public.current_org_id()
  and public.current_role() in ('admin','dispatcher')
);

-- ---------- profiles ----------
drop policy if exists profiles_select_self_or_admin_dispatcher on public.profiles;
create policy profiles_select_self_or_admin_dispatcher
on public.profiles
for select
to authenticated
using (
  id = auth.uid()
  or (
    org_id = public.current_org_id()
    and public.current_role() in ('admin','dispatcher')
  )
);

drop policy if exists profiles_update_admin_dispatcher on public.profiles;
create policy profiles_update_admin_dispatcher
on public.profiles
for update
to authenticated
using (
  org_id = public.current_org_id()
  and public.current_role() in ('admin','dispatcher')
)
with check (
  org_id = public.current_org_id()
  and public.current_role() in ('admin','dispatcher')
);

-- ---------- generic org-wide admin/dispatcher full access ----------
-- For MVP: grant admin/dispatcher full org access for most operational tables.
-- Tech access is limited and defined below per table.

-- technicians
drop policy if exists technicians_admin_dispatcher_all on public.technicians;
create policy technicians_admin_dispatcher_all
on public.technicians
for all
to authenticated
using (org_id = public.current_org_id() and public.current_role() in ('admin','dispatcher'))
with check (org_id = public.current_org_id() and public.current_role() in ('admin','dispatcher'));

-- technician_skills
drop policy if exists technician_skills_admin_dispatcher_all on public.technician_skills;
create policy technician_skills_admin_dispatcher_all
on public.technician_skills
for all
to authenticated
using (org_id = public.current_org_id() and public.current_role() in ('admin','dispatcher'))
with check (org_id = public.current_org_id() and public.current_role() in ('admin','dispatcher'));

-- bays
drop policy if exists bays_admin_dispatcher_all on public.bays;
create policy bays_admin_dispatcher_all
on public.bays
for all
to authenticated
using (org_id = public.current_org_id() and public.current_role() in ('admin','dispatcher'))
with check (org_id = public.current_org_id() and public.current_role() in ('admin','dispatcher'));

-- bay_hours
drop policy if exists bay_hours_admin_dispatcher_all on public.bay_hours;
create policy bay_hours_admin_dispatcher_all
on public.bay_hours
for all
to authenticated
using (org_id = public.current_org_id() and public.current_role() in ('admin','dispatcher'))
with check (org_id = public.current_org_id() and public.current_role() in ('admin','dispatcher'));

-- shifts
drop policy if exists shifts_admin_dispatcher_all on public.shifts;
create policy shifts_admin_dispatcher_all
on public.shifts
for all
to authenticated
using (org_id = public.current_org_id() and public.current_role() in ('admin','dispatcher'))
with check (org_id = public.current_org_id() and public.current_role() in ('admin','dispatcher'));

-- technician_shift_assignments
drop policy if exists tech_shift_assignments_admin_dispatcher_all on public.technician_shift_assignments;
create policy tech_shift_assignments_admin_dispatcher_all
on public.technician_shift_assignments
for all
to authenticated
using (org_id = public.current_org_id() and public.current_role() in ('admin','dispatcher'))
with check (org_id = public.current_org_id() and public.current_role() in ('admin','dispatcher'));

-- calendar_events
drop policy if exists calendar_events_admin_dispatcher_all on public.calendar_events;
create policy calendar_events_admin_dispatcher_all
on public.calendar_events
for all
to authenticated
using (org_id = public.current_org_id() and public.current_role() in ('admin','dispatcher'))
with check (org_id = public.current_org_id() and public.current_role() in ('admin','dispatcher'));

-- units
drop policy if exists units_admin_dispatcher_all on public.units;
create policy units_admin_dispatcher_all
on public.units
for all
to authenticated
using (org_id = public.current_org_id() and public.current_role() in ('admin','dispatcher'))
with check (org_id = public.current_org_id() and public.current_role() in ('admin','dispatcher'));

-- work_orders
drop policy if exists work_orders_admin_dispatcher_all on public.work_orders;
create policy work_orders_admin_dispatcher_all
on public.work_orders
for all
to authenticated
using (org_id = public.current_org_id() and public.current_role() in ('admin','dispatcher'))
with check (org_id = public.current_org_id() and public.current_role() in ('admin','dispatcher'));

-- tasks
drop policy if exists tasks_admin_dispatcher_all on public.tasks;
create policy tasks_admin_dispatcher_all
on public.tasks
for all
to authenticated
using (org_id = public.current_org_id() and public.current_role() in ('admin','dispatcher'))
with check (org_id = public.current_org_id() and public.current_role() in ('admin','dispatcher'));

-- parts
drop policy if exists parts_admin_dispatcher_all on public.parts;
create policy parts_admin_dispatcher_all
on public.parts
for all
to authenticated
using (org_id = public.current_org_id() and public.current_role() in ('admin','dispatcher'))
with check (org_id = public.current_org_id() and public.current_role() in ('admin','dispatcher'));

-- attachments
drop policy if exists attachments_admin_dispatcher_all on public.attachments;
create policy attachments_admin_dispatcher_all
on public.attachments
for all
to authenticated
using (org_id = public.current_org_id() and public.current_role() in ('admin','dispatcher'))
with check (org_id = public.current_org_id() and public.current_role() in ('admin','dispatcher'));

-- schedule_runs
drop policy if exists schedule_runs_admin_dispatcher_select on public.schedule_runs;
create policy schedule_runs_admin_dispatcher_select
on public.schedule_runs
for select
to authenticated
using (org_id = public.current_org_id() and public.current_role() in ('admin','dispatcher'));

-- schedule_items
drop policy if exists schedule_items_admin_dispatcher_all on public.schedule_items;
create policy schedule_items_admin_dispatcher_all
on public.schedule_items
for all
to authenticated
using (org_id = public.current_org_id() and public.current_role() in ('admin','dispatcher'))
with check (org_id = public.current_org_id() and public.current_role() in ('admin','dispatcher'));

-- schedule_overrides
drop policy if exists schedule_overrides_admin_dispatcher_all on public.schedule_overrides;
create policy schedule_overrides_admin_dispatcher_all
on public.schedule_overrides
for all
to authenticated
using (org_id = public.current_org_id() and public.current_role() in ('admin','dispatcher'))
with check (org_id = public.current_org_id() and public.current_role() in ('admin','dispatcher'));

-- ai_jobs
drop policy if exists ai_jobs_admin_dispatcher_select on public.ai_jobs;
create policy ai_jobs_admin_dispatcher_select
on public.ai_jobs
for select
to authenticated
using (org_id = public.current_org_id() and public.current_role() in ('admin','dispatcher'));

-- ai_results (IMPORTANT: tech has NO access, so tech cannot access raw LLM responses)
drop policy if exists ai_results_admin_dispatcher_select on public.ai_results;
create policy ai_results_admin_dispatcher_select
on public.ai_results
for select
to authenticated
using (org_id = public.current_org_id() and public.current_role() in ('admin','dispatcher'));

-- audit_log
drop policy if exists audit_log_admin_dispatcher_select on public.audit_log;
create policy audit_log_admin_dispatcher_select
on public.audit_log
for select
to authenticated
using (org_id = public.current_org_id() and public.current_role() in ('admin','dispatcher'));

-- job_queue: no client access (intentionally). Worker/API use service role.

-- ---------- TECH access policies ----------
-- Tech can only see schedule items assigned to them.
drop policy if exists schedule_items_tech_select_own on public.schedule_items;
create policy schedule_items_tech_select_own
on public.schedule_items
for select
to authenticated
using (
  org_id = public.current_org_id()
  and public.current_role() = 'tech'
  and exists (
    select 1
    from public.technicians t
    where t.id = schedule_items.technician_id
      and t.profile_id = auth.uid()
  )
);

-- Tech can read tasks assigned to them (via schedule_items)
drop policy if exists tasks_tech_select_assigned on public.tasks;
create policy tasks_tech_select_assigned
on public.tasks
for select
to authenticated
using (
  org_id = public.current_org_id()
  and public.current_role() = 'tech'
  and exists (
    select 1
    from public.schedule_items si
    join public.technicians t on t.id = si.technician_id
    where si.task_id = tasks.id
      and t.profile_id = auth.uid()
  )
);

-- Tech can read work orders that have tasks assigned to them.
drop policy if exists work_orders_tech_select_assigned on public.work_orders;
create policy work_orders_tech_select_assigned
on public.work_orders
for select
to authenticated
using (
  org_id = public.current_org_id()
  and public.current_role() = 'tech'
  and exists (
    select 1
    from public.tasks ta
    join public.schedule_items si on si.task_id = ta.id
    join public.technicians t on t.id = si.technician_id
    where ta.work_order_id = work_orders.id
      and t.profile_id = auth.uid()
  )
);

-- Tech can read parts for work orders assigned to them.
drop policy if exists parts_tech_select_assigned on public.parts;
create policy parts_tech_select_assigned
on public.parts
for select
to authenticated
using (
  org_id = public.current_org_id()
  and public.current_role() = 'tech'
  and exists (
    select 1
    from public.work_orders wo
    join public.tasks ta on ta.work_order_id = wo.id
    join public.schedule_items si on si.task_id = ta.id
    join public.technicians t on t.id = si.technician_id
    where wo.id = parts.work_order_id
      and t.profile_id = auth.uid()
  )
);

-- Tech can insert attachments they upload.
drop policy if exists attachments_tech_insert_own on public.attachments;
create policy attachments_tech_insert_own
on public.attachments
for insert
to authenticated
with check (
  org_id = public.current_org_id()
  and public.current_role() = 'tech'
  and uploaded_by = auth.uid()
);

-- Tech can read attachments linked to tasks/work orders assigned to them.
drop policy if exists attachments_tech_select_assigned on public.attachments;
create policy attachments_tech_select_assigned
on public.attachments
for select
to authenticated
using (
  org_id = public.current_org_id()
  and public.current_role() = 'tech'
  and (
    (
      task_id is not null
      and exists (
        select 1
        from public.schedule_items si
        join public.technicians t on t.id = si.technician_id
        where si.task_id = attachments.task_id
          and t.profile_id = auth.uid()
      )
    )
    or (
      work_order_id is not null
      and exists (
        select 1
        from public.tasks ta
        join public.schedule_items si on si.task_id = ta.id
        join public.technicians t on t.id = si.technician_id
        where ta.work_order_id = attachments.work_order_id
          and t.profile_id = auth.uid()
      )
    )
  )
);
