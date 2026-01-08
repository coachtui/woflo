# Railway Deployment Setup

## Environment Variables

### Critical: DATABASE_URL Format

When setting `DATABASE_URL` in Railway, **do NOT include quotes** around the password, even if it contains special characters.

### ✅ CORRECT Format:
```
postgresql://postgres.zntsvromhguedtqsewro:%23ClarkKent198@aws-1-us-west-1.pooler.supabase.com:6543/postgres
```

### ❌ WRONG Format (will cause parsing errors):
```
postgresql://postgres.zntsvromhguedtqsewro:'#ClarkKent198'@aws-1-us-west-1.pooler.supabase.com:6543/postgres
```

## Required Environment Variables

### Worker Service

```bash
DATABASE_URL=postgresql://postgres.zntsvromhguedtqsewro:%23ClarkKent198@aws-1-us-west-1.pooler.supabase.com:6543/postgres
WORKER_ID=railway-worker-1
POLL_INTERVAL_SECONDS=2
```

### API Service

```bash
DATABASE_URL=postgresql://postgres.zntsvromhguedtqsewro:%23ClarkKent198@aws-1-us-west-1.pooler.supabase.com:6543/postgres
SUPABASE_URL=https://zntsvromhguedtqsewro.supabase.co
SUPABASE_JWKS_URL=https://zntsvromhguedtqsewro.supabase.co/auth/v1/.well-known/jwks.json
SUPABASE_SERVICE_ROLE_KEY=<your-service-role-key>
```

### Web Service

```bash
NEXT_PUBLIC_SUPABASE_URL=https://zntsvromhguedtqsewro.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=<your-anon-key>
NEXT_PUBLIC_API_URL=https://your-api-service.up.railway.app
```

## Special Characters in Passwords

If your password contains special characters, they must be URL-encoded:

| Character | URL Encoded |
|-----------|-------------|
| `#`       | `%23`       |
| `@`       | `%40`       |
| `:`       | `%3A`       |
| `/`       | `%2F`       |
| `?`       | `%3F`       |
| `&`       | `%26`       |
| `=`       | `%3D`       |
| `+`       | `%2B`       |
| `%`       | `%25`       |
| ` ` (space) | `%20`     |

## Build Configuration

The worker service includes optimizations in `nixpacks.toml`:

- `--no-cache-dir` - Reduces memory during build
- `--prefer-binary` - Uses pre-compiled wheels (faster for ortools)
- Extended build timeout for large packages

## Deployment Steps

1. **Push your code:**
   ```bash
   git add .
   git commit -m "fix: Railway deployment configuration"
   git push
   ```

2. **Set environment variables in Railway:**
   - Go to each service in Railway dashboard
   - Navigate to "Variables" tab
   - Add the environment variables listed above
   - **Important:** Copy-paste without quotes

3. **Redeploy:**
   - Railway will auto-deploy on push
   - Or manually trigger deployment from dashboard

## Troubleshooting

### Build Timeout
If the worker build times out:
- Check that `nixpacks.toml` has the optimizations
- Verify Railway build logs show `--prefer-binary` flag
- Contact Railway support to increase timeout limits

### Database Connection Errors

#### 1. "ValueError: invalid literal for int()"
- Check DATABASE_URL doesn't have quotes around password
- Verify special characters are URL-encoded
- Test the URL format locally first

#### 2. "[Errno -2] Name or service not known" (DNS Error)
This means Railway cannot resolve the Supabase hostname. **This is the most common issue.**

**Solutions:**

**A. Check DATABASE_URL is Set in Railway**
- Go to Railway Worker service → Variables
- Verify DATABASE_URL exists and is correct
- Redeploy if you just added it

**B. Use Supabase IPv6 Mode (RECOMMENDED)**
Supabase supports IPv6 which Railway handles better:

1. Go to Supabase Dashboard → Settings → Database
2. Look for "IPv6" or network settings
3. Enable IPv6 if available
4. Use the IPv6-enabled connection string

**C. Use Railway's Private Networking**
If you deployed Supabase on Railway:
- Use Railway's private networking (${{POSTGRES_SERVICE.DATABASE_URL}})
- This bypasses public DNS entirely

**D. Check Supabase Connection Pooler Settings**
Instead of direct connection, try the **Session Pooler**:

```bash
# Session mode pooler (port 6543)
DATABASE_URL=postgresql://postgres:%23ClarkKent198@aws-1-us-west-1.pooler.supabase.com:6543/postgres?pgbouncer=true
```

**E. Verify Railway Can Reach External Databases**
Test from Railway shell:
```bash
# In Railway service → Shell
nslookup db.zntsvromhguedtqsewro.supabase.co
ping db.zntsvromhguedtqsewro.supabase.co
```

**F. Alternative: Use Supabase Connection Pooling**
Supabase offers transaction and session pooling which may have better network connectivity:

```bash
# Transaction pooler - use for short connections
postgresql://postgres:password@aws-1-us-west-1.pooler.supabase.com:6543/postgres

# Direct - use for long-running services (default)
postgresql://postgres:password@db.project-ref.supabase.co:5432/postgres
```

**G. Contact Support**
If DNS continues to fail:
1. Contact Railway support - DNS issues are usually on their end
2. Ask about egress/firewall rules for external database connections
3. Check Railway status page for networking incidents

### Worker Not Processing Jobs
1. Check worker logs for startup errors
2. Verify DATABASE_URL is correct
3. Ensure job_queue table exists (run migrations)
4. Check WORKER_ID is unique per instance

## Testing Locally

To test the DATABASE_URL format locally:

```bash
cd apps/worker
export DATABASE_URL='postgresql://postgres:#ClarkKent198@db.zntsvromhguedtqsewro.supabase.co:5432/postgres'
source ../../.venv/bin/activate
python worker.py
```

If it connects successfully locally, it will work on Railway.
