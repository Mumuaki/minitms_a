# MiniTMS Business Requirements Testing
# Tests according to MiniTMS_Full_Doc_Structure.md specifications

$SERVER = "89.167.70.67"
$USER = "root"
$BACKEND_URL = "http://localhost:8000"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "MiniTMS Business Requirements Testing" -ForegroundColor Cyan
Write-Host "Based on MiniTMS_Full_Doc_Structure.md" -ForegroundColor Gray
Write-Host "========================================" -ForegroundColor Cyan

# BR-001: Система должна автоматически получать грузы с trans.eu
Write-Host "`n[BR-001] Trans.eu Integration - КРИТИЧЕСКИЙ" -ForegroundColor Red
Write-Host "Requirement: Система должна автоматически получать грузы с trans.eu" -ForegroundColor Gray
ssh ${USER}@${SERVER} @"
echo 'Testing Trans.eu credentials...'
grep -E '(TRANS_EU_USERNAME|TRANS_EU_PASSWORD)' /opt/minitms/backend/.env | grep -v '#'
echo ''
echo 'Testing scraping endpoint...'
curl -s ${BACKEND_URL}/api/v1/scraping/status -w '\nHTTP: %{http_code}\n'
"@

# BR-002: Система должна рассчитывать прибыльность каждого груза
Write-Host "`n[BR-002] Profitability Calculation - КРИТИЧЕСКИЙ" -ForegroundColor Red
Write-Host "Requirement: Расчёт €/км = Цена груза / (Дистанция A→B + Дистанция B→C)" -ForegroundColor Gray
ssh ${USER}@${SERVER} @"
echo 'Testing profitability calculation...'
curl -s '${BACKEND_URL}/api/v1/cargos/search?fuel_consumption=30&fuel_price=1.5&limit=1' | head -50
"@

# BR-003: Система должна учитывать текущее местоположение транспорта
Write-Host "`n[BR-003] GPS Location Tracking - ВЫСОКИЙ" -ForegroundColor Yellow
Write-Host "Requirement: Учёт текущего местоположения ТС" -ForegroundColor Gray
ssh ${USER}@${SERVER} @"
echo 'Testing GPS integration...'
curl -s ${BACKEND_URL}/api/v1/gps/vehicles -w '\nHTTP: %{http_code}\n'
echo ''
echo 'Checking GPS Dozor credentials...'
grep -E '(GPS_DOZOR_URL|GPS_DOZOR_USERNAME)' /opt/minitms/backend/.env | grep -v '#'
"@

# BR-004: Многопользовательский режим
Write-Host "`n[BR-004] Multi-user Support - ВЫСОКИЙ" -ForegroundColor Yellow
Write-Host "Requirement: Поддержка 4 ролей (Administrator, Director, Dispatcher, Guest)" -ForegroundColor Gray
ssh ${USER}@${SERVER} @"
echo 'Testing user management...'
curl -s ${BACKEND_URL}/api/v1/users -w '\nHTTP: %{http_code}\n'
echo ''
echo 'Testing roles...'
curl -s ${BACKEND_URL}/api/v1/auth/roles -w '\nHTTP: %{http_code}\n'
"@

# BR-005: GPS-трекеры
Write-Host "`n[BR-005] GPS Tracker Integration - СРЕДНИЙ" -ForegroundColor Cyan
Write-Host "Requirement: Интеграция с GPS-трекерами" -ForegroundColor Gray
ssh ${USER}@${SERVER} @"
echo 'Testing GPS tracker endpoints...'
curl -s ${BACKEND_URL}/api/v1/gps/trackers -w '\nHTTP: %{http_code}\n'
"@

# BR-006: Email коммуникация
Write-Host "`n[BR-006] Email Communication - СРЕДНИЙ" -ForegroundColor Cyan
Write-Host "Requirement: Email-коммуникация с заказчиками" -ForegroundColor Gray
Write-Host "Limits: Max 50 emails/hour, Min 30 sec interval" -ForegroundColor Gray
ssh ${USER}@${SERVER} @"
echo 'Testing email functionality...'
curl -s ${BACKEND_URL}/api/v1/email/templates -w '\nHTTP: %{http_code}\n'
echo ''
echo 'Testing email limits...'
curl -s ${BACKEND_URL}/api/v1/email/limits -w '\nHTTP: %{http_code}\n'
"@

# BR-007: Google Sheets учёт
Write-Host "`n[BR-007] Google Sheets Integration - ВЫСОКИЙ" -ForegroundColor Yellow
Write-Host "Requirement: Ведение учёта в Google Sheets (24 столбца)" -ForegroundColor Gray
ssh ${USER}@${SERVER} @"
echo 'Testing Google Sheets integration...'
curl -s ${BACKEND_URL}/api/v1/integrations/google-sheets/status -w '\nHTTP: %{http_code}\n'
"@

# FR-FLEET-001: Управление автопарком
Write-Host "`n[FR-FLEET-001] Fleet Management - КРИТИЧЕСКИЙ" -ForegroundColor Red
Write-Host "Requirement: Добавление ТС с размерами кузова (L×W×H)" -ForegroundColor Gray
ssh ${USER}@${SERVER} @"
echo 'Testing vehicle management...'
curl -s ${BACKEND_URL}/api/v1/vehicles -w '\nHTTP: %{http_code}\n'
echo ''
echo 'Testing vehicle statistics...'
curl -s ${BACKEND_URL}/api/v1/vehicles/stats -w '\nHTTP: %{http_code}\n'
"@

# FR-CALC-001: Фильтрация по параметрам ТС
Write-Host "`n[FR-CALC-001] Vehicle Parameter Filtering - КРИТИЧЕСКИЙ" -ForegroundColor Red
Write-Host "Requirement: Фильтрация по весу, длине, ширине, высоте кузова" -ForegroundColor Gray
ssh ${USER}@${SERVER} @"
echo 'Testing vehicle-based filtering...'
curl -s '${BACKEND_URL}/api/v1/cargos/filter-by-vehicle?vehicle_max_weight=20&vehicle_length=13.6' -w '\nHTTP: %{http_code}\n'
"@

# FR-UI-002: Цветовая кодировка рентабельности
Write-Host "`n[FR-UI-002] Profitability Color Coding - КРИТИЧЕСКИЙ" -ForegroundColor Red
Write-Host "Requirement: 🔴<0.54 ⚪0.54-0.59 🟡0.60-0.79 🟢≥0.80 €/км" -ForegroundColor Gray
ssh ${USER}@${SERVER} @"
echo 'Testing color-coded profitability...'
curl -s '${BACKEND_URL}/api/v1/cargos/search?status_colors=GREEN,YELLOW&limit=5' | grep -E '(status_color|rate_per_km)' | head -20
"@

# FR-EMAIL-006: Email лимиты
Write-Host "`n[FR-EMAIL-006] Email Rate Limiting - КРИТИЧЕСКИЙ" -ForegroundColor Red
Write-Host "Requirement: Максимум 50 писем/час, минимум 30 сек между письмами" -ForegroundColor Gray
ssh ${USER}@${SERVER} @"
echo 'Testing email rate limits...'
curl -s ${BACKEND_URL}/api/v1/email/limits -w '\nHTTP: %{http_code}\n'
"@

# FR-PLAN-001: Финансовое планирование
Write-Host "`n[FR-PLAN-001] Financial Planning - КРИТИЧЕСКИЙ" -ForegroundColor Red
Write-Host "Requirement: Плановые показатели (Выручка, Маржа, Пробег)" -ForegroundColor Gray
ssh ${USER}@${SERVER} @"
echo 'Testing financial planning...'
curl -s ${BACKEND_URL}/api/v1/financial/plans -w '\nHTTP: %{http_code}\n'
echo ''
echo 'Testing dashboard...'
curl -s ${BACKEND_URL}/api/v1/financial/dashboard -w '\nHTTP: %{http_code}\n'
"@

# FR-GSHEET-002: Автосоздание структуры таблицы
Write-Host "`n[FR-GSHEET-002] Auto-create Google Sheets Structure - КРИТИЧЕСКИЙ" -ForegroundColor Red
Write-Host "Requirement: Автоматическое создание таблицы с 24 столбцами" -ForegroundColor Gray
ssh ${USER}@${SERVER} @"
echo 'Testing Google Sheets auto-creation...'
curl -s ${BACKEND_URL}/api/v1/integrations/google-sheets/structure -w '\nHTTP: %{http_code}\n'
"@

# FR-LOC-001: Локализация
Write-Host "`n[FR-LOC-001] Localization - ВЫСОКИЙ" -ForegroundColor Yellow
Write-Host "Requirement: Поддержка 4 языков (RU, EN, SK, PL)" -ForegroundColor Gray
ssh ${USER}@${SERVER} @"
echo 'Testing localization support...'
curl -s ${BACKEND_URL}/api/v1/localization/languages -w '\nHTTP: %{http_code}\n'
"@

# FR-SETTINGS-003: Минимальная ставка
Write-Host "`n[FR-SETTINGS-003] Minimum Rate Setting - ВЫСОКИЙ" -ForegroundColor Yellow
Write-Host "Requirement: Настройка минимальной ставки (0.15 - 3.5 EUR/км)" -ForegroundColor Gray
ssh ${USER}@${SERVER} @"
echo 'Testing rate settings...'
curl -s ${BACKEND_URL}/api/v1/settings/rates -w '\nHTTP: %{http_code}\n'
"@

# Performance Requirements
Write-Host "`n[PERFORMANCE] System Performance Tests" -ForegroundColor Magenta
Write-Host "Requirement: Загрузка списка грузов < 3 сек, Расчёт 100 грузов < 5 сек" -ForegroundColor Gray
ssh ${USER}@${SERVER} @"
echo 'Testing cargo list load time...'
time curl -s ${BACKEND_URL}/api/v1/cargos?limit=100 > /dev/null
echo ''
echo 'Testing profitability calculation time...'
time curl -s '${BACKEND_URL}/api/v1/cargos/search?fuel_consumption=30&fuel_price=1.5&limit=100' > /dev/null
"@

# Security Requirements
Write-Host "`n[SECURITY] Security Tests" -ForegroundColor Magenta
Write-Host "Requirement: TLS 1.3, bcrypt, GDPR compliance" -ForegroundColor Gray
ssh ${USER}@${SERVER} @"
echo 'Testing authentication...'
curl -s ${BACKEND_URL}/api/v1/auth/login -w '\nHTTP: %{http_code}\n'
echo ''
echo 'Checking security headers...'
curl -s -I ${BACKEND_URL}/health | grep -E '(X-Frame-Options|X-Content-Type-Options)'
"@

# Database Check
Write-Host "`n[DATABASE] Database Integrity" -ForegroundColor Magenta
Write-Host "Checking database tables and relationships..." -ForegroundColor Gray
ssh ${USER}@${SERVER} @"
echo 'Listing all tables...'
sudo -u postgres psql -d minitms -c '\dt' 2>/dev/null | grep public
echo ''
echo 'Checking key tables...'
sudo -u postgres psql -d minitms -c 'SELECT COUNT(*) as vehicles FROM vehicles; SELECT COUNT(*) as cargos FROM cargos; SELECT COUNT(*) as users FROM users;' 2>/dev/null
"@

# Redis Cache Check
Write-Host "`n[CACHE] Redis Cache Status" -ForegroundColor Magenta
ssh ${USER}@${SERVER} @"
echo 'Redis info...'
redis-cli info | grep -E '(redis_version|connected_clients|used_memory_human|total_commands_processed)'
echo ''
echo 'Redis keys count...'
redis-cli DBSIZE
"@

# Summary Report
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Business Requirements Test Summary" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

Write-Host "`nCritical Requirements (КРИТИЧЕСКИЙ):" -ForegroundColor Red
Write-Host "- BR-001: Trans.eu Integration" -ForegroundColor White
Write-Host "- BR-002: Profitability Calculation" -ForegroundColor White
Write-Host "- FR-FLEET-001: Fleet Management" -ForegroundColor White
Write-Host "- FR-CALC-001: Vehicle Filtering" -ForegroundColor White
Write-Host "- FR-UI-002: Color Coding" -ForegroundColor White
Write-Host "- FR-EMAIL-006: Email Limits" -ForegroundColor White
Write-Host "- FR-PLAN-001: Financial Planning" -ForegroundColor White
Write-Host "- FR-GSHEET-002: Google Sheets Structure" -ForegroundColor White

Write-Host "`nHigh Priority Requirements (ВЫСОКИЙ):" -ForegroundColor Yellow
Write-Host "- BR-003: GPS Location" -ForegroundColor White
Write-Host "- BR-004: Multi-user Support" -ForegroundColor White
Write-Host "- BR-007: Google Sheets Integration" -ForegroundColor White
Write-Host "- FR-LOC-001: Localization" -ForegroundColor White
Write-Host "- FR-SETTINGS-003: Rate Settings" -ForegroundColor White

Write-Host "`nMedium Priority Requirements (СРЕДНИЙ):" -ForegroundColor Cyan
Write-Host "- BR-005: GPS Trackers" -ForegroundColor White
Write-Host "- BR-006: Email Communication" -ForegroundColor White

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Testing Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan

Write-Host "`nNext Steps:" -ForegroundColor Yellow
Write-Host "1. Review all HTTP status codes (200/401 = OK)" -ForegroundColor White
Write-Host "2. Check logs for any errors: .\fix_server.ps1 -> Option 6" -ForegroundColor White
Write-Host "3. Verify .env configuration for failed integrations" -ForegroundColor White
Write-Host "4. Test frontend UI for visual confirmation" -ForegroundColor White
