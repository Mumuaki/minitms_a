# Пошаговая проверка MiniTMS на удалённом сервере 89.167.70.67
# Запуск: powershell -ExecutionPolicy Bypass -File scripts/test-remote.ps1

$Base = "http://89.167.70.67"
$Backend = "${Base}:8000"
$Frontend = $Base   # frontend runs on port 80
$timeout = 10

function Test-Url {
    param([string]$Url, [string]$Name, [string]$Expect = "any")
    try {
        $r = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec $timeout
        $ok = ($r.StatusCode -ge 200 -and $r.StatusCode -lt 400)
        if ($Expect -eq "json" -and $r.Content) {
            $j = $r.Content | ConvertFrom-Json -ErrorAction SilentlyContinue
            if ($j.status -eq "ok") { $ok = $true }
        }
        if ($ok) { Write-Host "  OK   $Name" -ForegroundColor Green } else { Write-Host "  FAIL $Name (HTTP $($r.StatusCode))" -ForegroundColor Red }
        return $ok
    } catch {
        Write-Host "  FAIL $Name - $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
}

Write-Host "`n=== MiniTMS: проверка удалённого сервера 89.167.70.67 ===`n" -ForegroundColor Cyan

# Шаг 1: Backend health
Write-Host "1. Backend health" -ForegroundColor Yellow
$b1 = Test-Url -Url "$Backend/health" -Name "GET /health" -Expect "json"

# Шаг 2: Backend docs
Write-Host "`n2. Backend API Docs" -ForegroundColor Yellow
$b2 = Test-Url -Url "$Backend/docs" -Name "GET /docs"

# Шаг 3: Frontend
Write-Host "`n3. Frontend" -ForegroundColor Yellow
$f1 = Test-Url -Url $Frontend -Name "GET / (frontend)"

# Шаг 4: OpenAPI (опционально)
Write-Host "`n4. OpenAPI schema" -ForegroundColor Yellow
$b3 = Test-Url -Url "$Backend/openapi.json" -Name "GET /openapi.json"

Write-Host ""
if ($b1 -and $b2 -and $f1) {
    Write-Host "Итог: приложение доступно. Можно тестировать в браузере:" -ForegroundColor Green
    Write-Host "  $Frontend" -ForegroundColor White
    Write-Host "  $Backend/docs" -ForegroundColor White
} else {
    Write-Host "Итог: часть проверок не прошла. На сервере выполните:" -ForegroundColor Red
    Write-Host "  ssh root@89.167.70.67" -ForegroundColor White
    Write-Host "  cd /opt/minitms && docker compose -f docker-compose.vps.yml up -d" -ForegroundColor White
}
Write-Host ""
