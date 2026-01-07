-- 0003_seed.sql
-- Seed data for ONE shop (dev/demo).
-- Safe to run multiple times: uses deterministic names, but IDs are generated.

do $$
declare
  v_org_id uuid;
  v_shift_id uuid;
  v_bay_general uuid;
  v_bay_welding uuid;
  v_unit_id uuid;
  v_wo_id uuid;
begin
  -- Organization
  insert into public.organizations (name, timezone)
  values ('Demo Diesel Shop', 'Pacific/Honolulu')
  on conflict do nothing;

  select id into v_org_id
  from public.organizations
  where name = 'Demo Diesel Shop'
  limit 1;

  -- Shift
  insert into public.shifts (org_id, name, start_time, end_time)
  values (v_org_id, 'Day Shift', '08:00', '17:00')
  on conflict do nothing;

  select id into v_shift_id
  from public.shifts
  where org_id = v_org_id and name = 'Day Shift'
  limit 1;

  -- Bays
  insert into public.bays (org_id, name, bay_type)
  values
    (v_org_id, 'Bay 1', 'heavy_lift'),
    (v_org_id, 'Bay 2', 'heavy_lift')
  on conflict do nothing;

  select id into v_bay_general
  from public.bays
  where org_id = v_org_id and name = 'Bay 1'
  limit 1;

  select id into v_bay_welding
  from public.bays
  where org_id = v_org_id and name = 'Weld Bay'
  limit 1;

  -- Bay hours (Mon-Fri 8-17)
  insert into public.bay_hours (org_id, bay_id, day_of_week, start_time, end_time)
  select v_org_id, b.id, d.day_of_week, '08:00'::time, '17:00'::time
  from public.bays b
  cross join (values (1),(2),(3),(4),(5)) as d(day_of_week)
  where b.org_id = v_org_id
  on conflict do nothing;

  -- Technicians
  insert into public.technicians (org_id, name, efficiency_multiplier, overtime_allowed, wip_limit)
  values
    (v_org_id, 'Alex', 1.1, true, 3),
    (v_org_id, 'Sam', 1.0, true, 3),
    (v_org_id, 'Jordan', 0.9, true, 2)
  on conflict do nothing;

  -- Skills
  insert into public.technician_skills (org_id, technician_id, skill, level, is_safety_critical)
  select v_org_id, t.id, s.skill, s.level, s.is_safety_critical
  from public.technicians t
  join (values
    ('Alex','engine',4,false),
    ('Alex','welding',3,false),
    ('Sam','electrical',4,true),
    ('Jordan','hydraulics',3,false)
  ) as s(name, skill, level, is_safety_critical)
  on t.org_id = v_org_id and t.name = s.name
  on conflict do nothing;

  -- Shift assignments
  insert into public.technician_shift_assignments (org_id, technician_id, shift_id, effective_from)
  select v_org_id, t.id, v_shift_id, current_date
  from public.technicians t
  where t.org_id = v_org_id
  on conflict do nothing;

  -- Unit + WO + tasks (simple demo)
  insert into public.units (org_id, unit_number, asset_type, customer_name_redacted)
  values (v_org_id, 'T-100', 'tractor', '[CUSTOMER]')
  on conflict do nothing;

  select id into v_unit_id
  from public.units
  where org_id = v_org_id and unit_number = 'T-100'
  limit 1;

  insert into public.work_orders (
    org_id, unit_id, asset_type, priority, due_date, customer_commitment_at,
    location, notes, status, parts_required, parts_status, parts_ready
  )
  values (
    v_org_id, v_unit_id, 'tractor', 4, current_date + 1,
    (now() + interval '1 day'),
    'shop', 'Driver reports loss of power under load; intermittent CEL.',
    'new', true, 'ordered', false
  )
  returning id into v_wo_id;

  insert into public.tasks (
    org_id, work_order_id, type, status,
    required_skill, required_skill_is_hard, required_bay_type,
    duration_minutes_low, duration_minutes_high
  )
  values
    (v_org_id, v_wo_id, 'diagnose', 'todo', 'engine', false, 'general', 60, 120),
    (v_org_id, v_wo_id, 'repair', 'todo', 'engine', false, 'heavy', 180, 300);

exception
  when unique_violation then
    -- Best-effort idempotency: ignore duplicates.
    null;
end;
$$;
