#!/bin/bash
# Quick start script for local development

# Working Supabase connection string
export DATABASE_URL='postgresql://postgres.zntsvromhguedtqsewro:ClarkKent198sm@aws-1-us-west-1.pooler.supabase.com:5432/postgres'

echo "🚀 Starting Woflo local development environment..."
echo ""
echo "DATABASE_URL set to: ${DATABASE_URL:0:50}..."
echo ""
echo "To start services, open 3 terminals and run:"
echo ""
echo "Terminal 1 - API (port 8000):"
echo "  cd apps/api && source ../../.venv/bin/activate && uvicorn main:app --host 0.0.0.0 --port 8000 --reload"
echo ""
echo "Terminal 2 - Web (port 3000):"
echo "  cd apps/web && npm run dev"
echo ""
echo "Terminal 3 - Worker (background):"
echo "  cd apps/worker && source ../../.venv/bin/activate && python worker.py"
echo ""
echo "Access URLs:"
echo "  - Web:  http://localhost:3000"
echo "  - API:  http://localhost:8000"
echo "  - Docs: http://localhost:8000/docs"
echo ""
