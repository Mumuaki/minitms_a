param(
    [switch]$SkipMigrations
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8
chcp 65001 > $null

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$venvPython = Join-Path $projectRoot ".\venv\Scripts\python.exe"
$envFile = Join-Path $projectRoot ".\backend\.env"
$envExample = Join-Path $projectRoot ".\backend\.env.example"
$frontendDir = Join-Path $projectRoot ".\frontend"

if (-not (Test-Path $venvPython)) {
    throw "Не найдено виртуальное окружение: $venvPython"
}

if (-not (Test-Path $envFile) -and (Test-Path $envExample)) {
    Copy-Item -Path $envExample -Destination $envFile
    Write-Host "Создан backend/.env из шаблона backend/.env.example. Проверьте значения перед прод-запуском." -ForegroundColor Yellow
}

$psPreamble = '[Console]::OutputEncoding=[System.Text.Encoding]::UTF8; $OutputEncoding=[System.Text.Encoding]::UTF8; chcp 65001 > $null;'

if (-not $SkipMigrations) {
    Write-Host "Применяю миграции БД..." -ForegroundColor Cyan
    Set-Location $projectRoot
    & $venvPython -m alembic upgrade head
}

Write-Host "Запускаю backend (uvicorn) в новом окне..." -ForegroundColor Cyan
$backendCmd = @"
$psPreamble
Set-Location '$projectRoot'
& '$venvPython' -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
"@
Start-Process -FilePath "powershell.exe" -ArgumentList @("-NoExit", "-Command", $backendCmd) | Out-Null

Write-Host "Запускаю frontend (Vite) в новом окне..." -ForegroundColor Cyan
$frontendCmd = @"
$psPreamble
Set-Location '$frontendDir'
npm run dev
"@
Start-Process -FilePath "powershell.exe" -ArgumentList @("-NoExit", "-Command", $frontendCmd) | Out-Null

Write-Host ""
Write-Host "MiniTMS запущен." -ForegroundColor Green
Write-Host "Frontend: http://localhost:5173"
Write-Host "Backend:  http://localhost:8000"
Write-Host "Swagger:  http://localhost:8000/docs"
Write-Host ""
Write-Host "Для остановки используйте: .\stop.ps1"
