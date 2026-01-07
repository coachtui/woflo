#!/usr/bin/env bash
set -euo pipefail

# Railway/Railpack entrypoint for Worker service.
# Assumes Railway service Root Directory is set to `apps/worker`.

exec python worker.py
