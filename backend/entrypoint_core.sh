#!/bin/bash
# entrypoint_core.sh — Core API (auth, users, fleet, vehicles)
# Запускает: миграции Alembic → создание admin → uvicorn main_core
set -e

echo "=== [core-api] Applying database migrations ==="
cd /workspace
alembic upgrade head

echo "=== [core-api] Ensuring administrator account ==="
cd /workspace/backend
python3 create_admin.py

echo "=== [core-api] Starting uvicorn on port 8001 ==="
exec uvicorn backend.main_.main_core:app --host 0.0.0.0 --port 8001
