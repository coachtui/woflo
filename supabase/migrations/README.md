# Supabase migrations

MVP uses raw SQL migrations executed in order:

1) `0001_init.sql` — tables, indexes, triggers
2) `0002_rls.sql` — RLS + policies
3) `0003_seed.sql` — demo seed data
4) `0004_seed_gca_holidays_and_bays.sql` — add 4 bays + 2026 GCA holidays (optional)
5) `0005_patch_demo_bays_heavy_lift.sql` — update demo org bays to heavy_lift (run if seed already applied)
6) `0006_profiles_autoprovision.sql` — trigger: auth.users → public.profiles (Demo org, role tech)
7) `0007_expand_audit_entity_types.sql` — allow auditing unit/technician/etc

## Applying migrations

### Option A (recommended for now): Supabase SQL editor
1) Open your Supabase project → **SQL Editor**
2) Paste each file in order and run

### Option B: psql (requires network access + DATABASE_URL)
```bash
export DATABASE_URL='postgresql://...'
psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f supabase/migrations/0001_init.sql
psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f supabase/migrations/0002_rls.sql
psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f supabase/migrations/0003_seed.sql
psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f supabase/migrations/0004_seed_gca_holidays_and_bays.sql
psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f supabase/migrations/0005_patch_demo_bays_heavy_lift.sql
psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f supabase/migrations/0006_profiles_autoprovision.sql
psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f supabase/migrations/0007_expand_audit_entity_types.sql
```
