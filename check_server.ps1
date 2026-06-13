# MiniTMS Server Diagnostic Script
# Проверяет все компоненты MiniTMS на удалённом VPS (Docker Compose)

$SERVER = "89.167.70.67"
$USER = "root"
$COMPOSE_FILE = "docker-compose.prod.yml"
$PROJECT_DIR = "/opt/minitms"

[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  MiniTMS Server Diagnostic Tool" -ForegroundColor Cyan
Write-Host "  Docker Compose Edition" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# --- 1/10: Проверка SSH-соединения ---
Write-Host "[1/10] Проверка SSH-соединения..." -ForegroundColor Yellow
try {
    $sshTest = ssh -o ConnectTimeout=5 -o StrictHostKeyChecking=no ${USER}@${SERVER} "echo SSH_OK"
    if ($sshTest -eq "SSH_OK") {
        Write-Host "  OK: SSH-соединение установлено" -ForegroundColor Green
    } else {
        Write-Host "  FAIL: SSH-соединение не удалось" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "  FAIL: Ошибка SSH: $_" -ForegroundColor Red
    exit 1
}

# --- 2/10: Информация о системе ---
Write-Host "`n[2/10] Информация о системе..." -ForegroundColor Yellow
$sysCmd = 'echo "--- Система ---"; uname -a; echo ""; echo "--- Диск ---"; df -h /; echo ""; echo "--- Память ---"; free -h'
ssh ${USER}@${SERVER} $sysCmd

# --- 3/10: Статус Docker-контейнеров ---
Write-Host "`n[3/10] Статус Docker-контейнеров..." -ForegroundColor Yellow
$psCmd = "cd ${PROJECT_DIR}; docker compose -f ${COMPOSE_FILE} ps"
ssh ${USER}@${SERVER} $psCmd

# --- 4/10: Проверка Frontend, порт 80 ---
Write-Host "`n[4/10] Проверка Frontend, порт 80..." -ForegroundColor Yellow
try {
    $frontResp = Invoke-WebRequest -Uri "http://${SERVER}" -UseBasicParsing -TimeoutSec 10
    Write-Host "  OK: Frontend отвечает, HTTP $($frontResp.StatusCode)" -ForegroundColor Green
} catch {
    Write-Host "  FAIL: Frontend не отвечает: $($_.Exception.Message)" -ForegroundColor Red
}

# --- 5/10: Проверка Backend/Gateway, порт 8000 ---
Write-Host "`n[5/10] Проверка Backend/Gateway, порт 8000..." -ForegroundColor Yellow
try {
    $backResp = Invoke-WebRequest -Uri "http://${SERVER}:8000/docs" -UseBasicParsing -TimeoutSec 10
    Write-Host "  OK: Backend API отвечает, HTTP $($backResp.StatusCode)" -ForegroundColor Green
} catch {
    Write-Host "  FAIL: Backend API не отвечает: $($_.Exception.Message)" -ForegroundColor Red
}

# --- 6/10: Проверка noVNC, порт 6080 внутри сервера ---
Write-Host "`n[6/10] Проверка noVNC, порт 6080 внутри сервера..." -ForegroundColor Yellow
$noVncCmd = 'curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:6080/ 2>/dev/null'
$noVncCheck = ssh ${USER}@${SERVER} $noVncCmd
if ($noVncCheck -eq "200") {
    Write-Host "  OK: noVNC доступен внутри сервера, HTTP 200" -ForegroundColor Green
    Write-Host "  INFO: Для доступа с локальной машины запустите .\start.ps1" -ForegroundColor Gray
} else {
    Write-Host "  WARN: noVNC не отвечает внутри сервера, код: $noVncCheck" -ForegroundColor Yellow
}

# --- 7/10: Проверка PostgreSQL ---
Write-Host "`n[7/10] Проверка PostgreSQL..." -ForegroundColor Yellow
$pgCmd = "cd ${PROJECT_DIR}; docker compose -f ${COMPOSE_FILE} exec -T postgres pg_isready -U postgres 2>&1"
$pgCheck = ssh ${USER}@${SERVER} $pgCmd
if ($pgCheck -match "accepting connections") {
    Write-Host "  OK: PostgreSQL принимает соединения" -ForegroundColor Green
} else {
    Write-Host "  FAIL: PostgreSQL: $pgCheck" -ForegroundColor Red
}

# --- 8/10: Проверка Redis ---
Write-Host "`n[8/10] Проверка Redis..." -ForegroundColor Yellow
$redisCmd = "cd ${PROJECT_DIR}; docker compose -f ${COMPOSE_FILE} exec -T redis redis-cli ping 2>&1"
$redisCheck = ssh ${USER}@${SERVER} $redisCmd
if ($redisCheck -match "PONG") {
    Write-Host "  OK: Redis отвечает PONG" -ForegroundColor Green
} elseif ($redisCheck -match "NOAUTH") {
    Write-Host "  OK: Redis работает, требует аутентификацию" -ForegroundColor Green
} else {
    Write-Host "  FAIL: Redis: $redisCheck" -ForegroundColor Red
}

# --- 9/10: Последние логи Gateway ---
Write-Host "`n[9/10] Последние логи Gateway, 5 строк..." -ForegroundColor Yellow
$gwLogsCmd = "cd ${PROJECT_DIR}; docker compose -f ${COMPOSE_FILE} logs --tail=5 gateway 2>&1"
ssh ${USER}@${SERVER} $gwLogsCmd

# --- 10/10: Последние логи Scraping Worker ---
Write-Host "`n[10/10] Последние логи Scraping Worker, 5 строк..." -ForegroundColor Yellow
$swLogsCmd = "cd ${PROJECT_DIR}; docker compose -f ${COMPOSE_FILE} logs --tail=5 scraping-worker 2>&1"
ssh ${USER}@${SERVER} $swLogsCmd

# --- Итог ---
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  Диагностика завершена!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Адреса сервисов:" -ForegroundColor White
Write-Host "    Frontend:  http://${SERVER}" -ForegroundColor Gray
Write-Host "    Backend:   http://${SERVER}:8000" -ForegroundColor Gray
Write-Host "    API Docs:  http://${SERVER}:8000/docs" -ForegroundColor Gray
Write-Host "    noVNC:     http://localhost:6080 -- через SSH-туннель" -ForegroundColor Gray
Write-Host ""
