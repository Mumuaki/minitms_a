# MiniTMS Server Fix & Maintenance Script
# This script helps fix common issues with the deployed system

$SERVER = "89.167.70.67"
$USER = "root"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "MiniTMS Server Fix & Maintenance" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

function Show-Menu {
    Write-Host "`nSelect an action:" -ForegroundColor Yellow
    Write-Host "1. Restart Backend Service" -ForegroundColor White
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
    Write-Host "12. Update Backend Code (git pull)" -ForegroundColor White
    Write-Host "13. Install/Update Dependencies" -ForegroundColor White
    Write-Host "14. Check Service Status" -ForegroundColor White
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
    Write-Host "`nRestarting Backend Service..." -ForegroundColor Yellow
    ssh ${USER}@${SERVER} "systemctl restart minitms-backend && systemctl status minitms-backend --no-pager | head -20"
}

function Restart-FrontendService {
    Write-Host "`nRestarting Frontend Service..." -ForegroundColor Yellow
    ssh ${USER}@${SERVER} "systemctl restart minitms-frontend && systemctl status minitms-frontend --no-pager | head -20"
}

function Restart-PostgreSQL {
    Write-Host "`nRestarting PostgreSQL..." -ForegroundColor Yellow
    ssh ${USER}@${SERVER} "systemctl restart postgresql && systemctl status postgresql --no-pager | head -20"
}

function Restart-Redis {
    Write-Host "`nRestarting Redis..." -ForegroundColor Yellow
    ssh ${USER}@${SERVER} "systemctl restart redis && systemctl status redis --no-pager | head -20"
}

function Restart-AllServices {
    Write-Host "`nRestarting All Services..." -ForegroundColor Yellow
    ssh ${USER}@${SERVER} "systemctl restart postgresql redis minitms-backend minitms-frontend && echo 'All services restarted'"
    Start-Sleep -Seconds 3
    ssh ${USER}@${SERVER} "systemctl status minitms-backend minitms-frontend --no-pager | head -40"
}

function View-BackendLogs {
    Write-Host "`nViewing Backend Logs (Ctrl+C to exit)..." -ForegroundColor Yellow
    ssh ${USER}@${SERVER} "journalctl -u minitms-backend -f"
}

function View-FrontendLogs {
    Write-Host "`nViewing Frontend Logs (Ctrl+C to exit)..." -ForegroundColor Yellow
    ssh ${USER}@${SERVER} "journalctl -u minitms-frontend -f"
}

function Check-DatabaseMigrations {
    Write-Host "`nChecking Database Migrations..." -ForegroundColor Yellow
    ssh ${USER}@${SERVER} "cd /root/MiniTMS/backend && python -m alembic current"
}

function Run-DatabaseMigrations {
    Write-Host "`nRunning Database Migrations..." -ForegroundColor Yellow
    ssh ${USER}@${SERVER} "cd /root/MiniTMS/backend && python -m alembic upgrade head"
}

function Clear-RedisCache {
    Write-Host "`nClearing Redis Cache..." -ForegroundColor Yellow
    ssh ${USER}@${SERVER} "redis-cli FLUSHDB && echo 'Redis cache cleared'"
}

function Check-DiskSpace {
    Write-Host "`nChecking Disk Space..." -ForegroundColor Yellow
    ssh ${USER}@${SERVER} "df -h"
}

function Update-BackendCode {
    Write-Host "`nUpdating Backend Code..." -ForegroundColor Yellow
    ssh ${USER}@${SERVER} "cd /root/MiniTMS && git pull && echo 'Code updated'"
}

function Install-Dependencies {
    Write-Host "`nInstalling/Updating Dependencies..." -ForegroundColor Yellow
    ssh ${USER}@${SERVER} "cd /root/MiniTMS/backend && pip install -r requirements.txt"
}

function Check-ServiceStatus {
    Write-Host "`nChecking Service Status..." -ForegroundColor Yellow
    ssh ${USER}@${SERVER} "systemctl status minitms-backend minitms-frontend postgresql redis --no-pager | head -80"
}

function Test-TransEuConnection {
    Write-Host "`nTesting Trans.eu Connection..." -ForegroundColor Yellow
    ssh ${USER}@${SERVER} "curl -s -o /dev/null -w 'HTTP Status: %{http_code}\n' https://www.trans.eu"
}

function Test-GPSIntegration {
    Write-Host "`nTesting GPS Integration..." -ForegroundColor Yellow
    ssh ${USER}@${SERVER} "curl -s -o /dev/null -w 'HTTP Status: %{http_code}\n' https://a1.gpsguard.eu/api/v1/vehicle/"
}

function Backup-Database {
    Write-Host "`nCreating Database Backup..." -ForegroundColor Yellow
    $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
    ssh ${USER}@${SERVER} "sudo -u postgres pg_dump minitms > /root/backups/minitms_backup_${timestamp}.sql && echo 'Backup created: /root/backups/minitms_backup_${timestamp}.sql'"
}

function View-SystemResources {
    Write-Host "`nViewing System Resources..." -ForegroundColor Yellow
    ssh ${USER}@${SERVER} "echo '=== CPU ===' && top -bn1 | head -20 && echo '' && echo '=== Memory ===' && free -h && echo '' && echo '=== Disk ===' && df -h"
}

function Check-NetworkConnectivity {
    Write-Host "`nChecking Network Connectivity..." -ForegroundColor Yellow
    ssh ${USER}@${SERVER} "echo '=== DNS ===' && nslookup google.com && echo '' && echo '=== External IP ===' && curl -s ifconfig.me && echo '' && echo '=== Open Ports ===' && netstat -tlnp | grep LISTEN"
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
