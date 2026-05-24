# ms-deploy.ps1 — Deploy MiniTMS microservices to VPS
# Usage: powershell -ExecutionPolicy Bypass -File scripts/ms-deploy.ps1
# Requires SSH access to root@89.167.70.67

$SERVER = "89.167.70.67"
$U      = "root"
$REMOTE = "/opt/minitms"
$COMPOSE = "docker-compose.prod.yml"
$SSH_HOST = "${U}@${SERVER}"

Write-Host "=== MiniTMS Microservices Deploy ===" -ForegroundColor Cyan
Write-Host "Server : $SSH_HOST"  -ForegroundColor Gray
Write-Host "Path   : $REMOTE"    -ForegroundColor Gray

# Step 1: Swap (создаём один раз — idempotent, повторный вызов безопасен)
Write-Host "`n[1/5] Ensure swap (2 GB)..." -ForegroundColor Yellow
ssh $SSH_HOST @"
if ! swapon --show | grep -q '/swapfile'; then
    fallocate -l 2G /swapfile
    chmod 600 /swapfile
    mkswap /swapfile
    swapon /swapfile
    grep -q '/swapfile' /etc/fstab || echo '/swapfile none swap sw 0 0' >> /etc/fstab
    echo 'Swap created and activated'
else
    echo 'Swap already active, skipping'
fi
free -h | grep Swap
"@

# Step 2: git pull
Write-Host "`n[2/5] git pull..." -ForegroundColor Yellow
ssh $SSH_HOST "cd $REMOTE && git pull origin main --no-edit"
if ($LASTEXITCODE -ne 0) { Write-Host "FATAL: git pull failed" -ForegroundColor Red; exit 1 }

# Step 3: stop old containers
Write-Host "`n[3/5] Stop old containers..." -ForegroundColor Yellow
ssh $SSH_HOST "cd $REMOTE && docker compose -f $COMPOSE down --remove-orphans 2>/dev/null; echo done"

# Step 4: build and start
Write-Host "`n[4/5] Build and start containers..." -ForegroundColor Yellow
ssh $SSH_HOST "cd $REMOTE && docker compose -f $COMPOSE up -d --build"
if ($LASTEXITCODE -ne 0) { Write-Host "FATAL: docker compose up failed" -ForegroundColor Red; exit 1 }

# Step 5: wait and check (90s — core-api needs time for alembic migrations)
Write-Host "`n[5/5] Waiting 90 sec for services to initialize..." -ForegroundColor Yellow
Start-Sleep -Seconds 90

Write-Host "`n=== Container status ===" -ForegroundColor Cyan
ssh $SSH_HOST "cd $REMOTE && docker compose -f $COMPOSE ps"

Write-Host "`n=== Health check ===" -ForegroundColor Cyan

$services = @(
    @{ name = "gateway";          port = 8000 },
    @{ name = "core-api";         port = 8001 },
    @{ name = "cargo-engine";     port = 8002 },
    @{ name = "scraping-worker";  port = 8003 },
    @{ name = "integration-hub";  port = 8004 }
)

$allOk = $true
foreach ($svc in $services) {
    $svcName = $svc.name
    $svcPort = $svc.port
    $result = ssh $SSH_HOST "docker exec minitms-$svcName wget -qO- http://localhost:$svcPort/health 2>/dev/null && echo OK || echo FAIL"
    if ($result -match "FAIL" -or -not $result) {
        Write-Host "  [FAIL] $svcName port=$svcPort" -ForegroundColor Red
        # Show last 20 log lines on failure
        ssh $SSH_HOST "cd $REMOTE && docker compose -f $COMPOSE logs --tail=20 $svcName"
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
    Write-Host "  Frontend : http://${SERVER}:80"        -ForegroundColor White
    Write-Host "  noVNC    : http://${SERVER}:6080"      -ForegroundColor White
}
else {
    Write-Host "=== SOME SERVICES FAILED ===" -ForegroundColor Red
    Write-Host "  Check logs: ssh $SSH_HOST 'cd $REMOTE && docker compose -f $COMPOSE logs --tail=80'" -ForegroundColor Yellow
}
