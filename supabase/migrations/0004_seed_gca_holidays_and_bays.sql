-- 0004_seed_gca_holidays_and_bays.sql
-- Adds: 4-bay seed layout + 2026 GCA holiday calendar (shop-wide).
-- Source: 2026_gca_holidayschedule.pdf (provided).
--
-- Idempotency: best-effort via NOT EXISTS checks.

do $$
declare
  v_org_id uuid;
  v_tz text;
begin
  select id, timezone into v_org_id, v_tz
  from public.organizations
  where name = 'Demo Diesel Shop'
  limit 1;

  if v_org_id is null then
    raise notice 'Demo Diesel Shop not found; skipping seed adjustments.';
    return;
  end if;

  -- Ensure 4 bays exist (all heavy/lift)
  if not exists (select 1 from public.bays where org_id = v_org_id and name = 'Bay 3') then
    insert into public.bays (org_id, name, bay_type) values (v_org_id, 'Bay 3', 'heavy_lift');
  end if;

  if not exists (select 1 from public.bays where org_id = v_org_id and name = 'Bay 4') then
    insert into public.bays (org_id, name, bay_type) values (v_org_id, 'Bay 4', 'heavy_lift');
  end if;

  -- Bay hours (Mon-Fri 8-17) for newly added bays
  insert into public.bay_hours (org_id, bay_id, day_of_week, start_time, end_time)
  select v_org_id, b.id, d.day_of_week, '08:00'::time, '17:00'::time
  from public.bays b
  cross join (values (1),(2),(3),(4),(5)) as d(day_of_week)
  where b.org_id = v_org_id
    and b.name in ('Bay 3','Bay 4')
    and not exists (
      select 1 from public.bay_hours bh
      where bh.bay_id = b.id
        and bh.day_of_week = d.day_of_week
        and bh.start_time = '08:00'::time
        and bh.end_time = '17:00'::time
    );

  -- Helper: insert a full-day shop holiday (midnight-to-midnight in org timezone)
  -- NOTE: stored as UTC timestamptz.
  --
  -- 2026 GCA holidays (observed Independence Day: Friday July 3).
  with holiday_dates as (
    select * from (values
      ('2026-01-01'::date, 'New Year''s Day'),
      ('2026-01-19'::date, 'Martin Luther King Jr. Day'),
      ('2026-02-16'::date, 'President''s Day'),
      ('2026-03-26'::date, 'Prince Jonah Kuhio Day'),
      ('2026-04-03'::date, 'Good Friday'),
      ('2026-05-25'::date, 'Memorial Day'),
      ('2026-06-11'::date, 'King Kamehameha I Day'),
      ('2026-06-19'::date, 'Juneteenth'),
      ('2026-07-03'::date, 'Independence Day (Observed)'),
      ('2026-08-21'::date, 'Statehood Day'),
      ('2026-09-07'::date, 'Labor Day'),
      ('2026-10-12'::date, 'Columbus Day / Discoverer''s Day'),
      ('2026-11-03'::date, 'General Election Day'),
      ('2026-11-11'::date, 'Veterans'' Day'),
      ('2026-11-26'::date, 'Thanksgiving Day'),
      ('2026-12-25'::date, 'Christmas Day')
    ) as t(day, label)
  ), to_insert as (
    select
      v_org_id as org_id,
      null::uuid as technician_id,
      'holiday'::text as type,
      (hd.day::timestamp at time zone v_tz) as start_at,
      ((hd.day + 1)::timestamp at time zone v_tz) as end_at,
      hd.label as notes
    from holiday_dates hd
  )
  insert into public.calendar_events (org_id, technician_id, type, start_at, end_at, notes)
  select ti.org_id, ti.technician_id, ti.type, ti.start_at, ti.end_at, ti.notes
  from to_insert ti
  where not exists (
    select 1
    from public.calendar_events ce
    where ce.org_id = ti.org_id
      and ce.technician_id is null
      and ce.type = 'holiday'
      and ce.start_at = ti.start_at
      and ce.end_at = ti.end_at
  );

end;
$$;
