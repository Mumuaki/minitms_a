#!/usr/bin/env bash
# Однократное исправление: подключить postgres и redis к сети backend, чтобы авторизация (500) работала.
# Запуск на VPS в каталоге проекта: bash scripts/vps-fix-backend-network.sh

set -e
NET="minitms_minitms-network"
for c in minitms-postgres minitms-redis; do
  if docker ps -q -f name="^${c}$" | grep -q .; then
    echo "Подключаем $c к $NET (если ещё не подключён)..."
    docker network connect "$NET" "$c" 2>/dev/null && echo "  OK" || echo "  уже в сети или ошибка"
  fi
done
echo "Перезапуск backend..."
docker compose restart backend
echo "Готово. Проверка логина: curl -s -X POST http://127.0.0.1:8000/api/v1/auth/login -d 'username=admin&password=admin'"
