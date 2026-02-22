# Deploy backend files to VPS (89.167.70.67). Run from project root: powershell -ExecutionPolicy Bypass -File scripts/deploy-backend-to-vps.ps1

$VPS = "root@89.167.70.67"
$REMOTE_DIR = "/opt/minitms"

$files = @(
    "backend/src/infrastructure/external_services/gps/dozor_gps_adapter.py",
    "backend/src/application/use_cases/fleet/add_vehicle.py",
    "backend/src/application/use_cases/fleet/update_vehicle.py",
    "backend/src/application/use_cases/fleet/refresh_vehicle_location.py",
    "backend/src/infrastructure/api/v1/endpoints/fleet.py"
)

$root = "d:\MiniTMS"
if ($PSScriptRoot) {
    $parent = Split-Path -Parent $PSScriptRoot
    if (Test-Path (Join-Path $parent "backend")) { $root = $parent }
}
if (-not (Test-Path (Join-Path $root "backend"))) {
    Write-Host "Error: Run from project root (d:\MiniTMS)" -ForegroundColor Red
    exit 1
}

Write-Host "Deploying backend to $VPS ..." -ForegroundColor Cyan
foreach ($rel in $files) {
    $local = Join-Path $root $rel
    if (-not (Test-Path $local)) {
        Write-Host "  Skip (missing): $rel" -ForegroundColor Yellow
        continue
    }
    Write-Host "  $rel"
    scp $local "${VPS}:${REMOTE_DIR}/$rel"
    if ($LASTEXITCODE -ne 0) {
        Write-Host "  scp failed for $rel" -ForegroundColor Red
    }
}
Write-Host ""
Write-Host "Done. On VPS run: docker compose restart backend" -ForegroundColor Green
