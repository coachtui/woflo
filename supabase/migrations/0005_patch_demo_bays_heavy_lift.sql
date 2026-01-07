-- 0005_patch_demo_bays_heavy_lift.sql
-- You said: "keep them all heavy/lift".
-- This patch updates the demo org bays to `bay_type='heavy_lift'`.
-- Safe to run multiple times.

do $$
declare
  v_org_id uuid;
begin
  select id into v_org_id
  from public.organizations
  where name = 'Demo Diesel Shop'
  limit 1;

  if v_org_id is null then
    raise notice 'Demo Diesel Shop not found; skipping bay patch.';
    return;
  end if;

  update public.bays
  set bay_type = 'heavy_lift'
  where org_id = v_org_id;
end;
$$;
