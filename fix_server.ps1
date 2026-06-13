# MiniTMS Server Fix & Maintenance Script (Docker Compose Edition)
# This script helps fix common issues with the deployed system

$SERVER = "89.167.70.67"
$USER = "root"
$PROJECT_DIR = "/opt/minitms"
$COMPOSE_FILE = "docker-compose.prod.yml"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "MiniTMS Server Fix & Maintenance (Docker)" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

function Show-Menu {
    Write-Host "`nSelect an action:" -ForegroundColor Yellow
    Write-Host "1. Restart Backend Services" -ForegroundColor White
    Write-Host "2. Restart Frontend Service" -ForegroundColor White
    Write-Host "3. Restart PostgreSQL" -ForegroundColor White
    Write-Host "4. Restart Redis" -ForegroundColor White
    Write-Host "5. Restart All Services" -ForegroundColor White
    Write-Host "6. View Backend Logs (live)" -ForegroundColor White
    Write-Host "7. View Frontend Logs (live)" -ForegroundColor White
    Write-Host "8. Check Database Migrations" -ForegroundColor White
    Write-Host "9. Run Database Migrations" -ForegroundColor White
    Write-Host "10. Clear Redis Cache" -ForegroundColor White
    Write-Host "11. Check Disk Space" -ForegroundColor White
    Write-Host "12. Update Code and Rebuild (Git Pull & Build)" -ForegroundColor White
    Write-Host "13. Rebuild Containers (No Cache)" -ForegroundColor White
    Write-Host "14. Check Containers Status (docker compose ps)" -ForegroundColor White
    Write-Host "15. Test Trans.eu Connection" -ForegroundColor White
    Write-Host "16. Test GPS Integration" -ForegroundColor White
    Write-Host "17. Backup Database" -ForegroundColor White
    Write-Host "18. View System Resources" -ForegroundColor White
    Write-Host "19. Check Network Connectivity" -ForegroundColor White
    Write-Host "20. Full System Diagnostic" -ForegroundColor White
    Write-Host "0. Exit" -ForegroundColor Red
    Write-Host ""
}

function Restart-BackendService {
    Write-Host "`nRestarting Backend Services..." -ForegroundColor Yellow
    ssh ${USER}@${SERVER} "cd ${PROJECT_DIR} && docker compose -f ${COMPOSE_FILE} restart core-api cargo-engine integration-hub scraping-worker && docker compose -f ${COMPOSE_FILE} ps"
}

function Restart-FrontendService {
    Write-Host "`nRestarting Frontend Service..." -ForegroundColor Yellow
    ssh ${USER}@${SERVER} "cd ${PROJECT_DIR} && docker compose -f ${COMPOSE_FILE} restart frontend && docker compose -f ${COMPOSE_FILE} ps frontend"
}

function Restart-PostgreSQL {
    Write-Host "`nRestarting PostgreSQL..." -ForegroundColor Yellow
    ssh ${USER}@${SERVER} "cd ${PROJECT_DIR} && docker compose -f ${COMPOSE_FILE} restart postgres && docker compose -f ${COMPOSE_FILE} ps postgres"
}

function Restart-Redis {
    Write-Host "`nRestarting Redis..." -ForegroundColor Yellow
    ssh ${USER}@${SERVER} "cd ${PROJECT_DIR} && docker compose -f ${COMPOSE_FILE} restart redis && docker compose -f ${COMPOSE_FILE} ps redis"
}

function Restart-AllServices {
    Write-Host "`nRestarting All Services..." -ForegroundColor Yellow
    ssh ${USER}@${SERVER} "cd ${PROJECT_DIR} && docker compose -f ${COMPOSE_FILE} restart && docker compose -f ${COMPOSE_FILE} ps"
}

function View-BackendLogs {
    Write-Host "`nViewing Backend Logs (Ctrl+C to exit)..." -ForegroundColor Yellow
    ssh ${USER}@${SERVER} "cd ${PROJECT_DIR} && docker compose -f ${COMPOSE_FILE} logs -f core-api cargo-engine integration-hub scraping-worker"
}

function View-FrontendLogs {
    Write-Host "`nViewing Frontend Logs (Ctrl+C to exit)..." -ForegroundColor Yellow
    ssh ${USER}@${SERVER} "cd ${PROJECT_DIR} && docker compose -f ${COMPOSE_FILE} logs -f frontend"
}

function Check-DatabaseMigrations {
    Write-Host "`nChecking Database Migrations..." -ForegroundColor Yellow
    ssh ${USER}@${SERVER} "cd ${PROJECT_DIR} && docker compose -f ${COMPOSE_FILE} exec -T core-api alembic current"
}

function Run-DatabaseMigrations {
    Write-Host "`nRunning Database Migrations..." -ForegroundColor Yellow
    ssh ${USER}@${SERVER} "cd ${PROJECT_DIR} && docker compose -f ${COMPOSE_FILE} exec -T core-api alembic upgrade head"
}

function Clear-RedisCache {
    Write-Host "`nClearing Redis Cache..." -ForegroundColor Yellow
    $cmd = 'cd {0} && REDIS_PASSWORD=$(grep -E "^REDIS_PASSWORD=" .env | cut -d= -f2 | tr -d ''\r\n'') && docker compose -f {1} exec -T redis redis-cli -a $REDIS_PASSWORD FLUSHDB' -f $PROJECT_DIR, $COMPOSE_FILE
    ssh ${USER}@${SERVER} $cmd
}

function Check-DiskSpace {
    Write-Host "`nChecking Disk Space..." -ForegroundColor Yellow
    ssh ${USER}@${SERVER} "df -h /"
}

function Update-BackendCode {
    Write-Host "`nUpdating Code (Git Pull & Rebuild)..." -ForegroundColor Yellow
    ssh ${USER}@${SERVER} "cd ${PROJECT_DIR} && git pull && docker compose -f ${COMPOSE_FILE} up -d --build"
}

function Install-Dependencies {
    Write-Host "`nRebuilding Containers without cache..." -ForegroundColor Yellow
    ssh ${USER}@${SERVER} "cd ${PROJECT_DIR} && docker compose -f ${COMPOSE_FILE} build --no-cache && docker compose -f ${COMPOSE_FILE} up -d"
}

function Check-ServiceStatus {
    Write-Host "`nChecking Containers Status..." -ForegroundColor Yellow
    ssh ${USER}@${SERVER} "cd ${PROJECT_DIR} && docker compose -f ${COMPOSE_FILE} ps"
}

function Test-TransEuConnection {
    Write-Host "`nTesting Trans.eu Connection from scraper..." -ForegroundColor Yellow
    ssh ${USER}@${SERVER} "cd ${PROJECT_DIR} && docker compose -f ${COMPOSE_FILE} exec -T scraping-worker curl -s -o /dev/null -w 'HTTP Status: %{http_code}\n' https://www.trans.eu"
}

function Test-GPSIntegration {
    Write-Host "`nTesting GPS Integration from integration-hub..." -ForegroundColor Yellow
    ssh ${USER}@${SERVER} "cd ${PROJECT_DIR} && docker compose -f ${COMPOSE_FILE} exec -T integration-hub curl -s -o /dev/null -w 'HTTP Status: %{http_code}\n' https://a1.gpsguard.eu/api/v1/vehicle/"
}

function Backup-Database {
    Write-Host "`nCreating Database Backup..." -ForegroundColor Yellow
    $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
    ssh ${USER}@${SERVER} "cd ${PROJECT_DIR} && docker compose -f ${COMPOSE_FILE} exec -T postgres pg_dump -U postgres minitms > /root/backups/minitms_backup_${timestamp}.sql && echo 'Backup created: /root/backups/minitms_backup_${timestamp}.sql'"
}

function View-SystemResources {
    Write-Host "`nViewing System Resources..." -ForegroundColor Yellow
    ssh ${USER}@${SERVER} "echo '=== CPU & Memory ===' && free -h && echo '' && echo '=== Docker Stats ===' && docker stats --no-stream"
}

function Check-NetworkConnectivity {
    Write-Host "`nChecking Network Connectivity..." -ForegroundColor Yellow
    ssh ${USER}@${SERVER} "echo '=== External IP ===' && curl -s ifconfig.me && echo '' && echo '=== Listen Ports ===' && netstat -tlnp"
}

function Full-SystemDiagnostic {
    Write-Host "`nRunning Full System Diagnostic..." -ForegroundColor Yellow
    & "d:\MiniTMS\check_server.ps1"
}

# Main Loop
while ($true) {
    Show-Menu
    $choice = Read-Host "Enter your choice"
    
    switch ($choice) {
        "1" { Restart-BackendService }
        "2" { Restart-FrontendService }
        "3" { Restart-PostgreSQL }
        "4" { Restart-Redis }
        "5" { Restart-AllServices }
        "6" { View-BackendLogs }
        "7" { View-FrontendLogs }
        "8" { Check-DatabaseMigrations }
        "9" { Run-DatabaseMigrations }
        "10" { Clear-RedisCache }
        "11" { Check-DiskSpace }
        "12" { Update-BackendCode }
        "13" { Install-Dependencies }
        "14" { Check-ServiceStatus }
        "15" { Test-TransEuConnection }
        "16" { Test-GPSIntegration }
        "17" { Backup-Database }
        "18" { View-SystemResources }
        "19" { Check-NetworkConnectivity }
        "20" { Full-SystemDiagnostic }
        "0" { 
            Write-Host "`nExiting..." -ForegroundColor Green
            exit 
        }
        default { 
            Write-Host "`nInvalid choice. Please try again." -ForegroundColor Red 
        }
    }
    
    Write-Host "`nPress any key to continue..." -ForegroundColor Gray
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
}
