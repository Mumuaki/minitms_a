#!/bin/bash
# Создаёт первого администратора.
# Пароль НИКОГДА не хранится в репозитории — задайте его в переменной окружения.
#
#   ADMIN_PASSWORD='...' ./create_admin.sh
#
set -e

: "${ADMIN_PASSWORD:?Задайте ADMIN_PASSWORD (пароль администратора)}"
ADMIN_EMAIL="${ADMIN_EMAIL:-admin@minitms.local}"

docker exec -e ADMIN_PASSWORD="$ADMIN_PASSWORD" -e ADMIN_EMAIL="$ADMIN_EMAIL" \
  minitms-core-api python3 create_admin.py
