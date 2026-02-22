#!/bin/bash
set -e
# Исправляем DATABASE_URL в docker-compose.yml: postgres -> admin
sed -i 's|DATABASE_URL=postgresql://postgres:|DATABASE_URL=postgresql://admin:|g' /opt/minitms/docker-compose.yml
grep "DATABASE_URL" /opt/minitms/docker-compose.yml
echo "COMPOSE_UPDATED"
