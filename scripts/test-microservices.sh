#!/bin/bash
# scripts/test-microservices.sh
# Скрипт для проверки работоспособности всех микросервисов MiniTMS

echo "=== [Test] Checking MiniTMS Microservices Status ==="

# 1. Проверка Docker контейнеров
echo -n "Checking Docker container states... "
UNHEALTHY=$(docker compose -f docker-compose.prod.yml ps | grep -E "unhealthy|exited" || true)
if [ -z "$UNHEALTHY" ]; then
    echo "OK (All containers running/healthy)"
else
    echo "ERROR (Some containers are not healthy):"
    echo "$UNHEALTHY"
fi

echo "----------------------------------------------------"

# 2. Проверка Health-endpoints через Gateway
GATEWAY_URL="http://localhost:8000"
echo "Testing endpoints through Gateway ($GATEWAY_URL):"

check_endpoint() {
    local name=$1
    local url=$2
    echo -n "  - $name: "
    STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$url")
    if [ "$STATUS" == "200" ]; then
        echo "OK (200)"
    else
        echo "FAILED (Status: $STATUS) - $url"
    fi
}

check_endpoint "Gateway Health" "$GATEWAY_URL/health"
check_endpoint "Core API" "$GATEWAY_URL/api/v1/auth/login" # Проверка роутинга на core-api (405 т.к. GET, но 200 на /health если есть)
check_endpoint "Core API Health" "http://localhost:8001/health"
check_endpoint "Cargo Engine Health" "http://localhost:8002/health"
check_endpoint "Scraping Worker Health" "http://localhost:8003/health"
check_endpoint "Integration Hub Health" "http://localhost:8004/health"

echo "----------------------------------------------------"

# 3. Проверка Frontend
echo -n "Checking Frontend (:80)... "
FE_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:80")
if [ "$FE_STATUS" == "200" ]; then
    echo "OK (200)"
else
    echo "FAILED (Status: $FE_STATUS)"
fi

echo "=== Test Completed ==="
