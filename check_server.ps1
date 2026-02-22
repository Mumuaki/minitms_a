# MiniTMS Server Diagnostic Script
# This script checks all components of the deployed MiniTMS system

$SERVER = "89.167.70.67"
$USER = "root"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "MiniTMS Server Diagnostic Tool" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Test SSH Connection
Write-Host "[1/10] Testing SSH Connection..." -ForegroundColor Yellow
try {
    $sshTest = ssh -o ConnectTimeout=5 -o StrictHostKeyChecking=no ${USER}@${SERVER} "echo 'SSH OK'"
    if ($sshTest -eq "SSH OK") {
        Write-Host "✓ SSH connection successful" -ForegroundColor Green
    } else {
        Write-Host "✗ SSH connection failed" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "✗ SSH connection error: $_" -ForegroundColor Red
    exit 1
}

# Check System Info
Write-Host "`n[2/10] Checking System Information..." -ForegroundColor Yellow
ssh ${USER}@${SERVER} "echo '--- System Info ---'; uname -a; echo ''; echo '--- Disk Usage ---'; df -h | grep -E '(Filesystem|/`$|/home)'; echo ''; echo '--- Memory Usage ---'; free -h"

# Check PostgreSQL
Write-Host "`n[3/10] Checking PostgreSQL..." -ForegroundColor Yellow
ssh ${USER}@${SERVER} "systemctl status postgresql --no-pager | head -20"
ssh ${USER}@${SERVER} "sudo -u postgres psql -c '\l' | grep minitms"

# Check Redis
Write-Host "`n[4/10] Checking Redis..." -ForegroundColor Yellow
ssh ${USER}@${SERVER} "systemctl status redis --no-pager | head -20"
ssh ${USER}@${SERVER} "redis-cli ping"

# Check Backend Service
Write-Host "`n[5/10] Checking Backend Service..." -ForegroundColor Yellow
ssh ${USER}@${SERVER} "systemctl status minitms-backend --no-pager 2>/dev/null | head -20 || echo 'Service not found, checking manual process...'"
ssh ${USER}@${SERVER} "ps aux | grep -E '(uvicorn|python.*main)' | grep -v grep"

# Check Backend Port
Write-Host "`n[6/10] Checking Backend Port (8000)..." -ForegroundColor Yellow
ssh ${USER}@${SERVER} "netstat -tlnp | grep ':8000'; if [ `$? -ne 0 ]; then ss -tlnp | grep ':8000'; fi"

# Check Frontend Service
Write-Host "`n[7/10] Checking Frontend Service..." -ForegroundColor Yellow
ssh ${USER}@${SERVER} "systemctl status minitms-frontend --no-pager 2>/dev/null | head -20 || echo 'Service not found, checking manual process...'"
ssh ${USER}@${SERVER} "ps aux | grep -E '(node|npm)' | grep -v grep"

# Check Frontend Port
Write-Host "`n[8/10] Checking Frontend Port (3000 or 80)..." -ForegroundColor Yellow
ssh ${USER}@${SERVER} "netstat -tlnp | grep -E ':(3000|80|443)'; if [ `$? -ne 0 ]; then ss -tlnp | grep -E ':(3000|80|443)'; fi"

# Check Nginx/Web Server
Write-Host "`n[9/10] Checking Web Server (Nginx/Apache)..." -ForegroundColor Yellow
ssh ${USER}@${SERVER} "systemctl status nginx --no-pager 2>/dev/null | head -20 || systemctl status apache2 --no-pager 2>/dev/null | head -20 || echo 'No web server found'"

# Check Application Logs
Write-Host "`n[10/10] Checking Recent Application Logs..." -ForegroundColor Yellow
ssh ${USER}@${SERVER} "echo '--- Backend Logs (last 20 lines) ---'; tail -20 /var/log/minitms/backend.log 2>/dev/null || tail -20 /root/MiniTMS/backend/logs/*.log 2>/dev/null || journalctl -u minitms-backend -n 20 --no-pager || echo 'No backend logs found'"

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Diagnostic Complete!" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# Test API Endpoints
Write-Host "`n[BONUS] Testing API Endpoints..." -ForegroundColor Yellow
Write-Host "Testing Backend Health Check..." -ForegroundColor Gray
ssh ${USER}@${SERVER} "curl -s http://localhost:8000/health 2>/dev/null || curl -s http://localhost:8000/api/v1/health 2>/dev/null || echo 'Health endpoint not responding'"

Write-Host "`nTesting Backend API Documentation..." -ForegroundColor Gray
ssh ${USER}@${SERVER} "curl -s -o /dev/null -w 'HTTP Status: %{http_code}\n' http://localhost:8000/docs"

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "All checks completed!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
