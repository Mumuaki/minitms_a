# Sync project with https://github.com/Mumuaki/minitms_a.git
# Run from project root (e.g. d:\MiniTMS): powershell -ExecutionPolicy Bypass -File scripts/sync-github.ps1

$ErrorActionPreference = "Stop"
$projectRoot = if ($PSScriptRoot) { Resolve-Path (Join-Path $PSScriptRoot "..") } else { Get-Location }
Set-Location $projectRoot

$gitPaths = @("D:\Git\bin", "C:\Program Files\Git\bin")
foreach ($p in $gitPaths) {
  if (Test-Path (Join-Path $p "git.exe")) {
    $env:Path = "$p;$env:Path"
    break
  }
}

$gitExe = Get-Command git -ErrorAction SilentlyContinue
if (-not $gitExe) {
  Write-Host "Git not found. Install Git or add it to PATH (see scripts/add-git-to-path.ps1)." -ForegroundColor Red
  exit 1
}

Write-Host "Remote: origin -> https://github.com/Mumuaki/minitms_a.git" -ForegroundColor Cyan
Write-Host "Project dir: $projectRoot" -ForegroundColor Cyan

Write-Host "`n1. git fetch origin..." -ForegroundColor Yellow
& git fetch origin
if ($LASTEXITCODE -ne 0) {
  Write-Host "Fetch failed. Check network and remote URL." -ForegroundColor Red
  exit 1
}

$branch = (& git rev-parse --abbrev-ref HEAD 2>$null)
if (-not $branch) { $branch = "main" }
$remoteHasBranch = (& git ls-remote --heads origin $branch 2>$null)
if ($remoteHasBranch) {
  Write-Host "2. git pull origin $branch..." -ForegroundColor Yellow
  $prevErr = $ErrorActionPreference
  $ErrorActionPreference = "Continue"
  $null = & git pull origin $branch --no-edit 2>&1
  $ErrorActionPreference = $prevErr
  if ($LASTEXITCODE -ne 0) { Write-Host "   (pull had issues, continuing)" -ForegroundColor Gray }
} else {
  Write-Host "2. No branch '$branch' on remote yet (empty repo or first push). Skipping pull." -ForegroundColor Gray
}

Write-Host "`n3. git status:" -ForegroundColor Yellow
& git status

$statusOut = & git status --porcelain
if ($statusOut) {
  Write-Host "`n4. Add and commit changes..." -ForegroundColor Yellow
  & git add -A
  & git commit -m "Sync: MiniTMS project with remote"
  if ($LASTEXITCODE -ne 0) {
    Write-Host "   Commit skipped (nothing to commit after add)." -ForegroundColor Gray
  }
} else {
  Write-Host "`n4. No uncommitted changes." -ForegroundColor Green
}

Write-Host "`n5. git push origin $branch..." -ForegroundColor Yellow
& git push -u origin $branch
if ($LASTEXITCODE -ne 0) {
  Write-Host "Push failed. Check auth (login/token) and repo permissions." -ForegroundColor Red
  exit 1
}

Write-Host "`nSync with https://github.com/Mumuaki/minitms_a.git done." -ForegroundColor Green
