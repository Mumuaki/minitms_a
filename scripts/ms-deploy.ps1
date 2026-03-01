# ms-deploy.ps1 - Deploy and integration test for docker-compose.prod.yml
# Usage: powershell -ExecutionPolicy Bypass -File scripts/ms-deploy.ps1
# Requires SSH access to root@89.167.70.67

$SERVER = "89.167.70.67"
$U = "root"
$REMOTE = "/opt/minitms"
$COMPOSE = "docker-compose.prod.yml"
$SSH_HOST = "${U}@${SERVER}"

Write-Host "=== MiniTMS Microservices Deploy ===" -ForegroundColor Cyan
Write-Host "Server : $SSH_HOST"  -ForegroundColor Gray
Write-Host "Path   : $REMOTE"    -ForegroundColor Gray

# Step 1: git pull
Write-Host "`n[1/4] git pull..." -ForegroundColor Yellow
ssh $SSH_HOST "cd $REMOTE && git pull origin main --no-edit"
if ($LASTEXITCODE -ne 0) { Write-Host "FATAL: git pull failed" -ForegroundColor Red; exit 1 }

# Step 2: stop old containers
Write-Host "`n[2/4] Stop old containers..." -ForegroundColor Yellow
ssh $SSH_HOST "cd $REMOTE && docker compose -f $COMPOSE down --remove-orphans 2>/dev/null; echo done"

# Step 3: build and start
Write-Host "`n[3/4] Build and start 10 containers..." -ForegroundColor Yellow
ssh $SSH_HOST "cd $REMOTE && docker compose -f $COMPOSE up -d --build"
if ($LASTEXITCODE -ne 0) { Write-Host "FATAL: docker compose up failed" -ForegroundColor Red; exit 1 }

# Step 4: wait and check
Write-Host "`n[4/4] Waiting 30 sec for services to start..." -ForegroundColor Yellow
Start-Sleep -Seconds 30

Write-Host "`n=== Container status ===" -ForegroundColor Cyan
ssh $SSH_HOST "cd $REMOTE && docker compose -f $COMPOSE ps"

Write-Host "`n=== Health check ===" -ForegroundColor Cyan

$ports = @(
    "gateway:8000",
    "core-api:8001",
    "cargo-engine:8002",
    "scraping-worker:8003",
    "integration-hub:8004"
)

$allOk = $true
foreach ($item in $ports) {
    $parts = $item -split ":"
    $svcName = $parts[0]
    $svcPort = $parts[1]
    $result = ssh $SSH_HOST "curl -sf http://localhost:$svcPort/health 2>/dev/null && echo OK || echo FAIL"
    if ($result -match "FAIL" -or -not $result) {
        Write-Host "  [FAIL] $svcName port=$svcPort" -ForegroundColor Red
        $allOk = $false
    }
    else {
        Write-Host "  [ OK ] $svcName -> $result" -ForegroundColor Green
    }
}

Write-Host ""
if ($allOk) {
    Write-Host "=== ALL SERVICES OK ===" -ForegroundColor Green
    Write-Host "  API docs : http://${SERVER}:8000/docs" -ForegroundColor White
    Write-Host "  Frontend : http://${SERVER}:80"         -ForegroundColor White
    Write-Host "  noVNC    : http://${SERVER}:6080"       -ForegroundColor White
}
else {
    Write-Host "=== SOME SERVICES FAILED ===" -ForegroundColor Red
    Write-Host "  Check logs: ssh $SSH_HOST 'cd $REMOTE && docker compose -f $COMPOSE logs --tail=80'" -ForegroundColor Yellow
}
