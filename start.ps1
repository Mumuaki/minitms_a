# MiniTMS Start Script
# Проверяет удалённый сервер и открывает SSH-туннель для noVNC

$SERVER = "89.167.70.67"
$USER = "root"
$COMPOSE_FILE = "docker-compose.prod.yml"
$PROJECT_DIR = "/opt/minitms"
$LOCAL_NOVNC_PORT = 6080
$PID_FILE = Join-Path (Split-Path -Parent $MyInvocation.MyCommand.Path) ".tunnel.pid"

[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  MiniTMS — Подключение к серверу" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# --- Шаг 1: Проверка SSH ---
Write-Host "[1/4] Проверка SSH-соединения..." -ForegroundColor Yellow
try {
    $sshTest = ssh -o ConnectTimeout=5 -o StrictHostKeyChecking=no ${USER}@${SERVER} "echo SSH_OK"
    if ($sshTest -ne "SSH_OK") {
        Write-Host "  FAIL: SSH-соединение не удалось" -ForegroundColor Red
        exit 1
    }
    Write-Host "  OK: SSH-соединение установлено" -ForegroundColor Green
} catch {
    Write-Host "  FAIL: Ошибка SSH: $_" -ForegroundColor Red
    exit 1
}

# --- Шаг 2: Проверка и запуск контейнеров ---
Write-Host "`n[2/4] Проверка Docker-контейнеров на сервере..." -ForegroundColor Yellow
$containers = ssh ${USER}@${SERVER} "cd ${PROJECT_DIR} && docker compose -f ${COMPOSE_FILE} ps --format '{{.Name}} {{.Status}}' 2>&1"

$hasContainers = $false
$allHealthy = $true

foreach ($line in $containers) {
    if ($line -match "^\s*$") { continue }
    $hasContainers = $true
    if ($line -match "(Up|healthy)") {
        Write-Host "  OK: $line" -ForegroundColor Green
    } else {
        Write-Host "  WARN: $line" -ForegroundColor Yellow
        $allHealthy = $false
    }
}

if (-not $hasContainers -or -not $allHealthy) {
    if (-not $hasContainers) {
        Write-Host "  WARN: Контейнеры не запущены на сервере (список пуст)." -ForegroundColor Yellow
    } else {
        Write-Host "  WARN: Не все контейнеры находятся в рабочем состоянии." -ForegroundColor Yellow
    }
    Write-Host "  INFO: Автоматический запуск проекта на сервере..." -ForegroundColor Cyan
    try {
        $startResult = ssh ${USER}@${SERVER} "cd ${PROJECT_DIR} && docker compose -f ${COMPOSE_FILE} up -d"
        Write-Host "  OK: Команда запуска выполнена" -ForegroundColor Green
        
        Write-Host "  ⏳ Ожидание запуска сервисов (10 секунд)..." -ForegroundColor Yellow
        Start-Sleep -Seconds 10
        
        Write-Host "  Проверка статуса после запуска..." -ForegroundColor Yellow
        $containersAfter = ssh ${USER}@${SERVER} "cd ${PROJECT_DIR} && docker compose -f ${COMPOSE_FILE} ps --format '{{.Name}} {{.Status}}' 2>&1"
        $finalHealthy = $true
        $finalHasContainers = $false
        foreach ($line in $containersAfter) {
            if ($line -match "^\s*$") { continue }
            $finalHasContainers = $true
            if ($line -match "(Up|healthy)") {
                Write-Host "    OK: $line" -ForegroundColor Green
            } else {
                Write-Host "    WARN: $line" -ForegroundColor Yellow
                $finalHealthy = $false
            }
        }
        if (-not $finalHasContainers -or -not $finalHealthy) {
            Write-Host "  FAIL: Некоторые контейнеры не удалось запустить автоматически." -ForegroundColor Red
            Write-Host "  INFO: Рекомендуется проверить логи на сервере: ssh ${USER}@${SERVER} 'cd ${PROJECT_DIR} && docker compose -f ${COMPOSE_FILE} logs'" -ForegroundColor Gray
        } else {
            Write-Host "  OK: Все контейнеры успешно запущены!" -ForegroundColor Green
        }
    } catch {
        Write-Host "  FAIL: Не удалось выполнить автоматический запуск: $_" -ForegroundColor Red
    }
} else {
    Write-Host "  OK: Все контейнеры уже запущены и работают" -ForegroundColor Green
}

# --- Шаг 3: Закрыть старый туннель (если есть) ---
Write-Host "`n[3/4] Настройка SSH-туннеля для noVNC..." -ForegroundColor Yellow
if (Test-Path $PID_FILE) {
    $oldPid = Get-Content $PID_FILE -ErrorAction SilentlyContinue
    if ($oldPid) {
        $oldProc = Get-Process -Id $oldPid -ErrorAction SilentlyContinue
        if ($oldProc) {
            Stop-Process -Id $oldPid -Force -ErrorAction SilentlyContinue
            Write-Host "  INFO: Закрыт предыдущий туннель (PID $oldPid)" -ForegroundColor Gray
        }
    }
    Remove-Item $PID_FILE -Force -ErrorAction SilentlyContinue
}

# Проверяем, не занят ли порт
$portCheck = Get-NetTCPConnection -LocalPort $LOCAL_NOVNC_PORT -ErrorAction SilentlyContinue
if ($portCheck) {
    Write-Host "  WARN: Порт $LOCAL_NOVNC_PORT уже занят. Туннель не создан." -ForegroundColor Yellow
    Write-Host "  INFO: Возможно, туннель уже открыт. Проверьте http://localhost:${LOCAL_NOVNC_PORT}" -ForegroundColor Gray
} else {
    # Запускаем SSH-туннель в фоновом процессе PowerShell
    $tunnelProcess = Start-Process -FilePath "ssh" `
        -ArgumentList "-N", "-L", "${LOCAL_NOVNC_PORT}:127.0.0.1:${LOCAL_NOVNC_PORT}", "${USER}@${SERVER}" `
        -WindowStyle Hidden `
        -PassThru

    # Ждём секунду, проверяем что процесс жив
    Start-Sleep -Seconds 2
    if ($tunnelProcess.HasExited) {
        Write-Host "  FAIL: SSH-туннель не удалось запустить" -ForegroundColor Red
    } else {
        # Сохраняем PID
        $tunnelProcess.Id | Out-File -FilePath $PID_FILE -Encoding ascii
        Write-Host "  OK: SSH-туннель открыт (PID $($tunnelProcess.Id))" -ForegroundColor Green
        Write-Host "  INFO: noVNC доступен на http://localhost:${LOCAL_NOVNC_PORT}" -ForegroundColor Gray
    }
}

# --- Шаг 4: Итог ---
Write-Host "`n[4/4] Готово!" -ForegroundColor Yellow
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  MiniTMS запущен и доступен" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Адреса сервисов:" -ForegroundColor White
Write-Host "    Frontend:       http://${SERVER}" -ForegroundColor Gray
Write-Host "    Backend API:    http://${SERVER}:8000" -ForegroundColor Gray
Write-Host "    API Docs:       http://${SERVER}:8000/docs" -ForegroundColor Gray
Write-Host "    noVNC (скрапер): http://localhost:${LOCAL_NOVNC_PORT}" -ForegroundColor Gray
Write-Host ""
Write-Host "  Для остановки туннеля: .\stop.ps1" -ForegroundColor White
Write-Host ""
