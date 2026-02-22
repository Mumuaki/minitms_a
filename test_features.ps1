# MiniTMS Feature Testing Script
# Tests specific features according to the specification

$SERVER = "89.167.70.67"
$USER = "root"
$BACKEND_URL = "http://localhost:8000"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "MiniTMS Feature Testing" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# Test 1: Authentication System
Write-Host "`n[TEST 1] Authentication & Authorization" -ForegroundColor Yellow
Write-Host "Testing login endpoint..." -ForegroundColor Gray
ssh ${USER}@${SERVER} "curl -s -X POST -H 'Content-Type: application/json' -d '{\"username\":\"admin\",\"password\":\"test\"}' ${BACKEND_URL}/api/v1/auth/login -w '\nHTTP: %{http_code}'"

# Test 2: Fleet Management - Add Vehicle
Write-Host "`n[TEST 2] Fleet Management - Vehicle CRUD" -ForegroundColor Yellow
Write-Host "Testing vehicle endpoints..." -ForegroundColor Gray
ssh ${USER}@${SERVER} "curl -s ${BACKEND_URL}/api/v1/vehicles -w '\nHTTP: %{http_code}'"

# Test 3: Trans.eu Scraping
Write-Host "`n[TEST 3] Trans.eu Web Scraping" -ForegroundColor Yellow
Write-Host "Testing scraping status..." -ForegroundColor Gray
ssh ${USER}@${SERVER} "curl -s ${BACKEND_URL}/api/v1/scraping/status -w '\nHTTP: %{http_code}'"

# Test 4: Profitability Calculation
Write-Host "`n[TEST 4] Profitability Calculation" -ForegroundColor Yellow
Write-Host "Testing cargo search with profitability..." -ForegroundColor Gray
ssh ${USER}@${SERVER} "curl -s '${BACKEND_URL}/api/v1/cargos/search?fuel_consumption=30&fuel_price=1.5&page=1&limit=5' -w '\nHTTP: %{http_code}'"

# Test 5: Route Visualization
Write-Host "`n[TEST 5] Route Visualization (OSM Integration)" -ForegroundColor Yellow
Write-Host "Testing route calculation..." -ForegroundColor Gray
ssh ${USER}@${SERVER} "curl -s ${BACKEND_URL}/api/v1/routes/calculate -w '\nHTTP: %{http_code}'"

# Test 6: GPS Integration
Write-Host "`n[TEST 6] GPS Integration (GPS Dozor)" -ForegroundColor Yellow
Write-Host "Testing GPS connection..." -ForegroundColor Gray
ssh ${USER}@${SERVER} "curl -s ${BACKEND_URL}/api/v1/gps/vehicles -w '\nHTTP: %{http_code}'"
Write-Host "Testing direct GPS Dozor API..." -ForegroundColor Gray
ssh ${USER}@${SERVER} "curl -s -u 'rymma.hrusko@gmail.com:@@Jhznpf1!@@' https://a1.gpsguard.eu/api/v1/vehicle/ -w '\nHTTP: %{http_code}'"

# Test 7: Email Communication
Write-Host "`n[TEST 7] Email Communication" -ForegroundColor Yellow
Write-Host "Testing email templates..." -ForegroundColor Gray
ssh ${USER}@${SERVER} "curl -s ${BACKEND_URL}/api/v1/email/templates -w '\nHTTP: %{http_code}'"
Write-Host "Testing email rate limits..." -ForegroundColor Gray
ssh ${USER}@${SERVER} "curl -s ${BACKEND_URL}/api/v1/email/limits -w '\nHTTP: %{http_code}'"

# Test 8: Financial Planning
Write-Host "`n[TEST 8] Financial Planning" -ForegroundColor Yellow
Write-Host "Testing financial dashboard..." -ForegroundColor Gray
ssh ${USER}@${SERVER} "curl -s ${BACKEND_URL}/api/v1/financial/dashboard -w '\nHTTP: %{http_code}'"
Write-Host "Testing plans..." -ForegroundColor Gray
ssh ${USER}@${SERVER} "curl -s ${BACKEND_URL}/api/v1/financial/plans -w '\nHTTP: %{http_code}'"

# Test 9: Google Sheets Integration
Write-Host "`n[TEST 9] Google Sheets Integration" -ForegroundColor Yellow
Write-Host "Testing Google Sheets status..." -ForegroundColor Gray
ssh ${USER}@${SERVER} "curl -s ${BACKEND_URL}/api/v1/integrations/google-sheets/status -w '\nHTTP: %{http_code}'"

# Test 10: Notifications
Write-Host "`n[TEST 10] Notification System" -ForegroundColor Yellow
Write-Host "Testing notification settings..." -ForegroundColor Gray
ssh ${USER}@${SERVER} "curl -s ${BACKEND_URL}/api/v1/notifications/settings -w '\nHTTP: %{http_code}'"

# Test 11: Localization (4 languages)
Write-Host "`n[TEST 11] Localization (RU, EN, SK, PL)" -ForegroundColor Yellow
Write-Host "Testing language support..." -ForegroundColor Gray
ssh ${USER}@${SERVER} "curl -s ${BACKEND_URL}/api/v1/localization/languages -w '\nHTTP: %{http_code}'"

# Test 12: Settings
Write-Host "`n[TEST 12] System Settings" -ForegroundColor Yellow
Write-Host "Testing settings endpoints..." -ForegroundColor Gray
ssh ${USER}@${SERVER} "curl -s ${BACKEND_URL}/api/v1/settings -w '\nHTTP: %{http_code}'"

# Test 13: Database Performance
Write-Host "`n[TEST 13] Database Performance" -ForegroundColor Yellow
Write-Host "Checking database size and performance..." -ForegroundColor Gray
ssh ${USER}@${SERVER} "sudo -u postgres psql -d minitms -c 'SELECT schemaname, tablename, pg_size_pretty(pg_total_relation_size(schemaname||'\''.'\''||tablename)) AS size FROM pg_tables WHERE schemaname = '\''public'\'' ORDER BY pg_total_relation_size(schemaname||'\''.'\''||tablename) DESC LIMIT 10;' 2>/dev/null"

# Test 14: Redis Cache Performance
Write-Host "`n[TEST 14] Redis Cache Performance" -ForegroundColor Yellow
Write-Host "Checking Redis performance..." -ForegroundColor Gray
ssh ${USER}@${SERVER} "redis-cli --latency-history -i 1 -c 5"

# Test 15: API Response Time
Write-Host "`n[TEST 15] API Response Time" -ForegroundColor Yellow
Write-Host "Measuring API response times..." -ForegroundColor Gray
ssh ${USER}@${SERVER} "curl -s -o /dev/null -w 'Health: %{time_total}s\n' ${BACKEND_URL}/health"
ssh ${USER}@${SERVER} "curl -s -o /dev/null -w 'Vehicles: %{time_total}s\n' ${BACKEND_URL}/api/v1/vehicles"
ssh ${USER}@${SERVER} "curl -s -o /dev/null -w 'Cargos: %{time_total}s\n' ${BACKEND_URL}/api/v1/cargos"

# Test 16: Security Headers
Write-Host "`n[TEST 16] Security Headers" -ForegroundColor Yellow
Write-Host "Checking security headers..." -ForegroundColor Gray
ssh ${USER}@${SERVER} "curl -s -I ${BACKEND_URL}/health | grep -E '(X-Frame-Options|X-Content-Type-Options|Strict-Transport-Security)'"

# Test 17: CORS Configuration
Write-Host "`n[TEST 17] CORS Configuration" -ForegroundColor Yellow
Write-Host "Testing CORS headers..." -ForegroundColor Gray
ssh ${USER}@${SERVER} "curl -s -I -H 'Origin: http://localhost:3000' ${BACKEND_URL}/health | grep -i 'access-control'"

# Test 18: WebSocket Support (if applicable)
Write-Host "`n[TEST 18] WebSocket Support" -ForegroundColor Yellow
Write-Host "Checking WebSocket endpoints..." -ForegroundColor Gray
ssh ${USER}@${SERVER} "curl -s ${BACKEND_URL}/api/v1/ws/status -w '\nHTTP: %{http_code}' || echo 'WebSocket not configured'"

# Test 19: File Upload (for documents)
Write-Host "`n[TEST 19] File Upload Capability" -ForegroundColor Yellow
Write-Host "Testing file upload endpoints..." -ForegroundColor Gray
ssh ${USER}@${SERVER} "curl -s ${BACKEND_URL}/api/v1/upload/test -w '\nHTTP: %{http_code}' || echo 'Upload endpoint not found'"

# Test 20: Export Functionality
Write-Host "`n[TEST 20] Export Functionality (CSV/Excel)" -ForegroundColor Yellow
Write-Host "Testing export endpoints..." -ForegroundColor Gray
ssh ${USER}@${SERVER} "curl -s ${BACKEND_URL}/api/v1/export/vehicles -w '\nHTTP: %{http_code}'"

# Summary
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Feature Testing Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan

Write-Host "`nNext Steps:" -ForegroundColor Yellow
Write-Host "1. Review any failed tests (HTTP codes != 200/401)" -ForegroundColor White
Write-Host "2. Check logs for detailed error messages" -ForegroundColor White
Write-Host "3. Use fix_server.ps1 to restart services if needed" -ForegroundColor White
Write-Host "4. Verify .env configuration for integrations" -ForegroundColor White
