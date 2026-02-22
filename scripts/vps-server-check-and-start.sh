#!/usr/bin/env bash
# Запуск на VPS (89.167.70.67): проверка и запуск backend + frontend.
# Использование: на сервере в каталоге проекта выполнить: bash scripts/vps-server-check-and-start.sh

set -e
cd "$(dirname "$0")/.."
# Docker Compose V2 (docker compose) или старый docker-compose
if docker compose version &>/dev/null; then
  COMPOSE="docker compose -f docker-compose.vps.yml"
elif command -v docker-compose &>/dev/null; then
  COMPOSE="docker-compose -f docker-compose.vps.yml"
else
  echo "Ошибка: нужен 'docker compose' или 'docker-compose'. Установите: apt install docker-compose-plugin"
  exit 1
fi

if [ ! -f "docker-compose.vps.yml" ]; then
  echo "Ошибка: в каталоге $(pwd) нет docker-compose.vps.yml. Скопируйте его из репозитория или выполните git pull."
  exit 1
fi

echo "=== MiniTMS VPS: проверка и запуск ==="

# Проверка Docker
if ! command -v docker &>/dev/null; then
  echo "Ошибка: Docker не установлен."
  exit 1
fi
if ! docker info &>/dev/null; then
  echo "Ошибка: Docker не запущен или нет прав."
  exit 1
fi

# Статус контейнеров
BACKEND_NAME="minitms-backend"
FRONTEND_NAME="minitms-frontend"
backend_up=$(docker ps -q -f name="^${BACKEND_NAME}$" 2>/dev/null | wc -l)
frontend_up=$(docker ps -q -f name="^${FRONTEND_NAME}$" 2>/dev/null | wc -l)

if [ "$backend_up" -eq 1 ] && [ "$frontend_up" -eq 1 ]; then
  echo "Контейнеры backend и frontend уже запущены."
else
  echo "Запуск сервисов: $COMPOSE up -d --build"
  $COMPOSE up -d --build
  echo "Ожидание старта (15 сек)..."
  sleep 15
fi

# Проверка backend (health)
echo ""
echo "--- Проверка backend (http://127.0.0.1:8000/health) ---"
if curl -sf --connect-timeout 5 http://127.0.0.1:8000/health >/dev/null; then
  echo "Backend: OK"
  curl -s http://127.0.0.1:8000/health | head -1
else
  echo "Backend: не отвечает. Логи: $COMPOSE logs --tail=30 backend"
  $COMPOSE logs --tail=30 backend
  exit 1
fi

# Проверка frontend (порт 3000)
echo ""
echo "--- Проверка frontend (http://127.0.0.1:3000/) ---"
if curl -sf --connect-timeout 5 -o /dev/null http://127.0.0.1:3000/; then
  echo "Frontend: OK"
else
  echo "Frontend: не отвечает. Логи: $COMPOSE logs --tail=30 frontend"
  $COMPOSE logs --tail=30 frontend
  exit 1
fi

echo ""
echo "=== Готово. Приложение доступно:"
echo "  Frontend: http://89.167.70.67:3000"
echo "  Backend API: http://89.167.70.67:8000"
echo "  API Docs:   http://89.167.70.67:8000/docs"
