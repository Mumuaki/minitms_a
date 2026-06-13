# MiniTMS Stop Script
# Закрывает SSH-туннель для noVNC

$PID_FILE = Join-Path (Split-Path -Parent $MyInvocation.MyCommand.Path) ".tunnel.pid"

[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  MiniTMS — Остановка туннеля" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

if (-not (Test-Path $PID_FILE)) {
    Write-Host "  INFO: SSH-туннель не запущен (файл .tunnel.pid не найден)" -ForegroundColor Yellow
    Write-Host "" 
    exit 0
}

$tunnelPid = Get-Content $PID_FILE -ErrorAction SilentlyContinue

if (-not $tunnelPid) {
    Write-Host "  INFO: Файл .tunnel.pid пуст" -ForegroundColor Yellow
    Remove-Item $PID_FILE -Force -ErrorAction SilentlyContinue
    exit 0
}

$proc = Get-Process -Id $tunnelPid -ErrorAction SilentlyContinue

if ($proc) {
    try {
        Stop-Process -Id $tunnelPid -Force -ErrorAction Stop
        Write-Host "  OK: SSH-туннель остановлен (PID $tunnelPid)" -ForegroundColor Green
    } catch {
        Write-Host "  FAIL: Не удалось остановить процесс PID ${tunnelPid}: $($_.Exception.Message)" -ForegroundColor Red
    }
} else {
    Write-Host "  INFO: Процесс PID $tunnelPid уже не запущен" -ForegroundColor Yellow
}

Remove-Item $PID_FILE -Force -ErrorAction SilentlyContinue
Write-Host ""
Write-Host "  Туннель закрыт. Сервер продолжает работать." -ForegroundColor Gray
Write-Host "  Для повторного подключения: .\start.ps1" -ForegroundColor Gray
Write-Host ""
