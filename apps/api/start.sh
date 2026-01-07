#!/usr/bin/env bash
set -euo pipefail

# Railway/Railpack entrypoint for API service.
# Assumes Railway service Root Directory is set to `apps/api`.

exec uvicorn apps.api.main:app --host 0.0.0.0 --port "${PORT:-8000}"
