# MiniTMS Detailed Module Testing Script
# This script performs detailed checks on each module according to the specification

$SERVER = "89.167.70.67"
$USER = "root"
$BACKEND_URL = "http://${SERVER}:8000"
$FRONTEND_URL = "http://${SERVER}:3000"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "MiniTMS Module Testing" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# Helper function to test API endpoint
function Test-APIEndpoint {
    param(
        [string]$Name,
        [string]$Endpoint,
        [string]$Method = "GET",
        [string]$Body = $null
    )
    
    Write-Host "`nTesting: $Name" -ForegroundColor Yellow
    Write-Host "Endpoint: $Endpoint" -ForegroundColor Gray
    
    if ($Method -eq "GET") {
        $cmd = "curl -s -w '\nHTTP_CODE:%{http_code}' '$Endpoint'"
    } else {
        $cmd = "curl -s -X $Method -H 'Content-Type: application/json' -d '$Body' -w '\nHTTP_CODE:%{http_code}' '$Endpoint'"
    }
    
    $result = ssh ${USER}@${SERVER} $cmd
    Write-Host $result
    
    if ($result -match "HTTP_CODE:200") {
        Write-Host "[OK] $Name - OK" -ForegroundColor Green
        return $true
    } elseif ($result -match "HTTP_CODE:401") {
        Write-Host "[WARN] $Name - Authentication required (401)" -ForegroundColor Yellow
        return $true
    } else {
        Write-Host "[FAIL] $Name - Failed" -ForegroundColor Red
        return $false
    }
}

# MODULE 1: Authentication & Authorization
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "MODULE 1: Authentication & Authorization" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

Test-APIEndpoint "Health Check" "${BACKEND_URL}/health"
Test-APIEndpoint "API Documentation" "${BACKEND_URL}/docs"
Test-APIEndpoint "Login Endpoint" "${BACKEND_URL}/api/v1/auth/login"

# MODULE 2: Fleet Management
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "MODULE 2: Fleet Management" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

Test-APIEndpoint "Get Vehicles" "${BACKEND_URL}/api/v1/vehicles"
Test-APIEndpoint "Vehicle Statistics" "${BACKEND_URL}/api/v1/vehicles/stats"

# MODULE 3: Trans.eu Scraping
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "MODULE 3: Trans.eu Web Scraping" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

Test-APIEndpoint "Get Cargos" "${BACKEND_URL}/api/v1/cargos"
Test-APIEndpoint "Search Cargos" "${BACKEND_URL}/api/v1/cargos/search"
Test-APIEndpoint "Scraping Status" "${BACKEND_URL}/api/v1/scraping/status"

# MODULE 4: Profitability Calculation
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "MODULE 4: Profitability Calculation" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

Test-APIEndpoint "Filter by Vehicle" "${BACKEND_URL}/api/v1/cargos/filter-by-vehicle"
Test-APIEndpoint "Calculate Route" "${BACKEND_URL}/api/v1/routes/calculate"

# MODULE 5: Route Planning
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "MODULE 5: Route Planning" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

Test-APIEndpoint "Route Planning" "${BACKEND_URL}/api/v1/route-planning"

# MODULE 6: GPS Integration
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "MODULE 6: GPS Integration" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

Test-APIEndpoint "GPS Vehicles" "${BACKEND_URL}/api/v1/gps/vehicles"
Test-APIEndpoint "GPS Status" "${BACKEND_URL}/api/v1/gps/status"

# MODULE 7: Email Communication
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "MODULE 7: Email Communication" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

Test-APIEndpoint "Email Templates" "${BACKEND_URL}/api/v1/email/templates"
Test-APIEndpoint "Email History" "${BACKEND_URL}/api/v1/email/history"

# MODULE 8: Financial Planning
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "MODULE 8: Financial Planning" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

Test-APIEndpoint "Financial Plans" "${BACKEND_URL}/api/v1/financial/plans"
Test-APIEndpoint "Dashboard Stats" "${BACKEND_URL}/api/v1/financial/dashboard"

# MODULE 9: Google Sheets Integration
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "MODULE 9: Google Sheets Integration" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

Test-APIEndpoint "Google Sheets Status" "${BACKEND_URL}/api/v1/integrations/google-sheets/status"
Test-APIEndpoint "Sync Status" "${BACKEND_URL}/api/v1/integrations/google-sheets/sync"

# MODULE 10: Settings
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "MODULE 10: Settings & Configuration" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

Test-APIEndpoint "System Settings" "${BACKEND_URL}/api/v1/settings"
Test-APIEndpoint "User Settings" "${BACKEND_URL}/api/v1/settings/user"

# Check Database Connection
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "DATABASE: PostgreSQL Connection" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

Write-Host "`nChecking database tables..." -ForegroundColor Yellow
ssh ${USER}@${SERVER} "sudo -u postgres psql -d minitms -c '\dt' 2>/dev/null || echo 'Cannot connect to database'"

Write-Host "`nChecking database size..." -ForegroundColor Yellow
ssh ${USER}@${SERVER} "sudo -u postgres psql -d minitms -c 'SELECT pg_size_pretty(pg_database_size(current_database()));' 2>/dev/null"

# Check Redis Connection
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "CACHE: Redis Connection" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

Write-Host "`nChecking Redis info..." -ForegroundColor Yellow
ssh ${USER}@${SERVER} "redis-cli info | grep -E '(redis_version|connected_clients|used_memory_human)'"

Write-Host "`nChecking Redis keys..." -ForegroundColor Yellow
ssh ${USER}@${SERVER} "redis-cli DBSIZE"

# Check Frontend
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "FRONTEND: React Application" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

Write-Host "`nChecking frontend availability..." -ForegroundColor Yellow
ssh ${USER}@${SERVER} "curl -s -o /dev/null -w 'HTTP Status: %{http_code}\n' http://localhost:3000 || curl -s -o /dev/null -w 'HTTP Status: %{http_code}\n' http://localhost:80"

# Check Environment Variables
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "CONFIGURATION: Environment Check" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

Write-Host "`nChecking .env file..." -ForegroundColor Yellow
ssh ${USER}@${SERVER} "cat /root/MiniTMS/backend/.env 2>/dev/null | grep -v PASSWORD | grep -v SECRET | grep -v KEY || echo '.env file not found in /root/MiniTMS/backend/'"

# Check Logs for Errors
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "LOGS: Recent Errors" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

Write-Host "`nChecking for recent errors in logs..." -ForegroundColor Yellow
ssh ${USER}@${SERVER} "journalctl -u minitms-backend --since '1 hour ago' --no-pager | grep -i error | tail -10 || echo 'No recent errors found'"

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Module Testing Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
