#!/bin/bash
# entrypoint_service.sh — универсальный entrypoint для лёгких сервисов
# Использует переменную SERVICE_MODULE для указания модуля и SERVICE_PORT для порта.
# Используется: cargo-engine, integration-hub, celery-worker, celery-beat
#
# Пример использования в docker-compose.prod.yml:
#   environment:
#     SERVICE_MODULE: backend.main_.main_cargo:app
#     SERVICE_PORT: 8002
set -e

: "${SERVICE_MODULE:?SERVICE_MODULE must be set (e.g. backend.main_cargo:app)}"
: "${SERVICE_PORT:?SERVICE_PORT must be set (e.g. 8002)}"

echo "=== [service] Starting uvicorn: ${SERVICE_MODULE} on port ${SERVICE_PORT} ==="
exec uvicorn "${SERVICE_MODULE}" --host 0.0.0.0 --port "${SERVICE_PORT}"
