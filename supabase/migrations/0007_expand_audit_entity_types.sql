-- 0007_expand_audit_entity_types.sql
-- Expand audit_log.entity_type check constraint to include admin-managed entities.
-- Additive change (does not relax audit coverage).

do $$
begin
  -- Find and drop the existing check constraint (name is system-generated unless specified).
  -- In our 0001 migration it is unnamed; Postgres will have created a constraint name.
  -- We locate it dynamically.
  if exists (
    select 1
    from pg_constraint c
    join pg_class t on t.oid = c.conrelid
    join pg_namespace n on n.oid = t.relnamespace
    where n.nspname = 'public'
      and t.relname = 'audit_log'
      and c.contype = 'c'
      and pg_get_constraintdef(c.oid) like '%entity_type%'
  ) then
    execute (
      select format('alter table public.audit_log drop constraint %I', c.conname)
      from pg_constraint c
      join pg_class t on t.oid = c.conrelid
      join pg_namespace n on n.oid = t.relnamespace
      where n.nspname = 'public'
        and t.relname = 'audit_log'
        and c.contype = 'c'
        and pg_get_constraintdef(c.oid) like '%entity_type%'
      limit 1
    );
  end if;

  alter table public.audit_log
    add constraint audit_log_entity_type_check
    check (
      entity_type in (
        'work_order','task','schedule','parts','ai_job',
        'unit','technician','bay','calendar_event','shift'
      )
    );
end;
$$;
