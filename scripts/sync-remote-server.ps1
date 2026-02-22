# Sync remote server with GitHub (minitms_a): git pull on server + restart backend/frontend
# Run from project root: powershell -ExecutionPolicy Bypass -File scripts/sync-remote-server.ps1
# Requires: SSH access to the server (e.g. ssh root@89.167.70.67)

$SERVER = "89.167.70.67"
$USER = "root"
# Project path on the server
$REMOTE_PROJECT = "/opt/minitms"
$GITHUB_REPO = "https://github.com/Mumuaki/minitms_a.git"

$ErrorActionPreference = "Stop"

Write-Host "Remote server sync: $USER@$SERVER" -ForegroundColor Cyan
Write-Host "Project on server: $REMOTE_PROJECT" -ForegroundColor Cyan
Write-Host "GitHub repo: $GITHUB_REPO" -ForegroundColor Cyan

# 1. Set origin URL, fetch, then pull or reset to match repo
Write-Host "`n1. Setting origin and syncing with GitHub on server..." -ForegroundColor Yellow
$fetchCmd = "cd $REMOTE_PROJECT && git remote set-url origin $GITHUB_REPO 2>/dev/null; git fetch origin"
ssh "${USER}@${SERVER}" $fetchCmd
if ($LASTEXITCODE -ne 0) {
  Write-Host "Git fetch on server failed. Check SSH and that project path exists." -ForegroundColor Red
  exit 1
}
$pullCmd = "cd $REMOTE_PROJECT && git pull origin main --no-edit 2>&1"
$pullOut = ssh "${USER}@${SERVER}" $pullCmd
if ($LASTEXITCODE -ne 0 -or $pullOut -match "would be overwritten by merge|Could not merge") {
  Write-Host "   Pull had conflicts or untracked overwrite - resetting to origin/main." -ForegroundColor Gray
  $resetCmd = "cd $REMOTE_PROJECT && git reset --hard origin/main"
  ssh "${USER}@${SERVER}" $resetCmd
  if ($LASTEXITCODE -ne 0) { exit 1 }
} else {
  Write-Host $pullOut
}

# 2. Rebuild and restart backend (code is baked into Docker image, must rebuild)
Write-Host "`n2. Rebuilding and restarting backend..." -ForegroundColor Yellow
$rebuildCmd = "cd $REMOTE_PROJECT && docker compose -f docker-compose.vps.yml build backend && docker compose -f docker-compose.vps.yml up -d backend; echo Done"
ssh "${USER}@${SERVER}" $rebuildCmd

Write-Host "`nSync with remote server done." -ForegroundColor Green
Write-Host "Frontend: http://${SERVER}  (port 80)" -ForegroundColor Gray
Write-Host "API Docs: http://${SERVER}:8000/docs" -ForegroundColor Gray
