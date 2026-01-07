-- 0006_profiles_autoprovision.sql
-- Auto-provision `public.profiles` from `auth.users`.
-- Decision: assign all new users to org "Demo Diesel Shop" with role = 'tech' (safest default).
--
-- IMPORTANT SECURITY NOTE:
-- - This is a single-tenant bootstrap convenience.
-- - For multi-org prod, replace with explicit invites / org assignment workflow.

create or replace function public.handle_new_user()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
declare
  v_org_id uuid;
  v_email text;
  v_display_name text;
begin
  select id into v_org_id
  from public.organizations
  where name = 'Demo Diesel Shop'
  limit 1;

  if v_org_id is null then
    -- No org to attach user to; do nothing.
    return new;
  end if;

  v_email := coalesce(new.email, '');
  v_display_name := null;
  begin
    v_display_name := nullif((new.raw_user_meta_data->>'full_name'), '');
  exception when others then
    v_display_name := null;
  end;

  insert into public.profiles (id, org_id, email, display_name, role, is_active)
  values (new.id, v_org_id, v_email, v_display_name, 'tech', true)
  on conflict (id) do update
    set org_id = excluded.org_id,
        email = excluded.email,
        display_name = excluded.display_name,
        role = excluded.role,
        is_active = true;

  return new;
end;
$$;

drop trigger if exists on_auth_user_created on auth.users;
create trigger on_auth_user_created
after insert on auth.users
for each row execute procedure public.handle_new_user();
