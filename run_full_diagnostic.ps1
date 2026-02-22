# MiniTMS Full Diagnostic Report Generator
# Runs all checks and generates a comprehensive report

$SERVER = "89.167.70.67"
$USER = "root"
$TIMESTAMP = Get-Date -Format "yyyyMMdd_HHmmss"
$REPORT_FILE = "d:\MiniTMS\diagnostic_report_${TIMESTAMP}.txt"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "MiniTMS Full Diagnostic Report" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Server: $SERVER" -ForegroundColor Yellow
Write-Host "Timestamp: $TIMESTAMP" -ForegroundColor Yellow
Write-Host "Report: $REPORT_FILE" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Cyan

# Start report
@"
========================================
MiniTMS Full Diagnostic Report
========================================
Server: $SERVER
User: $USER
Date: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")
========================================

"@ | Out-File -FilePath $REPORT_FILE -Encoding UTF8

# Function to add to report and display
function Add-ToReport {
    param([string]$Content)
    $Content | Out-File -FilePath $REPORT_FILE -Append -Encoding UTF8
    Write-Host $Content
}

# 1. Basic Server Check
Add-ToReport "`n[1/5] BASIC SERVER CHECK"
Add-ToReport "========================================`n"
Write-Host "Running basic server check..." -ForegroundColor Yellow
& "d:\MiniTMS\check_server.ps1" | Out-File -FilePath $REPORT_FILE -Append -Encoding UTF8

# 2. Module Check
Add-ToReport "`n`n[2/5] MODULE CHECK"
Add-ToReport "========================================`n"
Write-Host "`nRunning module check..." -ForegroundColor Yellow
& "d:\MiniTMS\check_modules.ps1" | Out-File -FilePath $REPORT_FILE -Append -Encoding UTF8

# 3. Business Requirements Check
Add-ToReport "`n`n[3/5] BUSINESS REQUIREMENTS CHECK"
Add-ToReport "========================================`n"
Write-Host "`nRunning business requirements check..." -ForegroundColor Yellow
& "d:\MiniTMS\test_business_requirements.ps1" | Out-File -FilePath $REPORT_FILE -Append -Encoding UTF8

# 4. Feature Tests
Add-ToReport "`n`n[4/5] FEATURE TESTS"
Add-ToReport "========================================`n"
Write-Host "`nRunning feature tests..." -ForegroundColor Yellow
& "d:\MiniTMS\test_features.ps1" | Out-File -FilePath $REPORT_FILE -Append -Encoding UTF8

# 5. System Resources
Add-ToReport "`n`n[5/5] SYSTEM RESOURCES"
Add-ToReport "========================================`n"
Write-Host "`nChecking system resources..." -ForegroundColor Yellow

$resources = ssh ${USER}@${SERVER} @"
echo '=== CPU Usage ==='
top -bn1 | grep 'Cpu(s)' | sed 's/.*, *\([0-9.]*\)%* id.*/\1/' | awk '{print 100 - \$1"%"}'
echo ''
echo '=== Memory Usage ==='
free -h | grep Mem | awk '{print "Used: " \$3 " / Total: " \$2 " (" \$3/\$2*100 "%)"}'
echo ''
echo '=== Disk Usage ==='
df -h | grep -E '(Filesystem|/$)'
echo ''
echo '=== Network Connections ==='
netstat -an | grep ESTABLISHED | wc -l
echo 'established connections'
echo ''
echo '=== Process Count ==='
ps aux | wc -l
echo 'total processes'
echo ''
echo '=== Uptime ==='
uptime
"@

Add-ToReport $resources

# Summary
Add-ToReport "`n`n========================================"
Add-ToReport "DIAGNOSTIC SUMMARY"
Add-ToReport "========================================`n"

# Count HTTP 200 responses
$content = Get-Content $REPORT_FILE -Raw
$http200Count = ([regex]::Matches($content, "HTTP.*200")).Count
$http401Count = ([regex]::Matches($content, "HTTP.*401")).Count
$http500Count = ([regex]::Matches($content, "HTTP.*500")).Count
$httpErrorCount = ([regex]::Matches($content, "HTTP.*(404|502|503)")).Count

Add-ToReport "HTTP Response Summary:"
Add-ToReport "- Successful (200): $http200Count"
Add-ToReport "- Auth Required (401): $http401Count"
Add-ToReport "- Server Errors (500): $http500Count"
Add-ToReport "- Other Errors (404/502/503): $httpErrorCount"
Add-ToReport ""

# Service status summary
$activeServices = ([regex]::Matches($content, "active \(running\)")).Count
$inactiveServices = ([regex]::Matches($content, "inactive|failed")).Count

Add-ToReport "Service Status Summary:"
Add-ToReport "- Active Services: $activeServices"
Add-ToReport "- Inactive/Failed Services: $inactiveServices"
Add-ToReport ""

# Overall health
if ($http500Count -eq 0 -and $httpErrorCount -eq 0 -and $inactiveServices -eq 0) {
    Add-ToReport "Overall Health: ✅ EXCELLENT"
    Write-Host "`nOverall Health: ✅ EXCELLENT" -ForegroundColor Green
} elseif ($http500Count -lt 3 -and $httpErrorCount -lt 3) {
    Add-ToReport "Overall Health: ⚠️ GOOD (Minor issues detected)"
    Write-Host "`nOverall Health: ⚠️ GOOD (Minor issues detected)" -ForegroundColor Yellow
} else {
    Add-ToReport "Overall Health: ❌ NEEDS ATTENTION"
    Write-Host "`nOverall Health: ❌ NEEDS ATTENTION" -ForegroundColor Red
}

Add-ToReport "`n========================================"
Add-ToReport "End of Report"
Add-ToReport "========================================"

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Diagnostic Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Report saved to: $REPORT_FILE" -ForegroundColor Yellow
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Yellow
Write-Host "1. Review the report file" -ForegroundColor White
Write-Host "2. If issues found, use: .\fix_server.ps1" -ForegroundColor White
Write-Host "3. For specific problems, see: SERVER_MANAGEMENT.md" -ForegroundColor White
Write-Host ""

# Ask if user wants to open the report
$openReport = Read-Host "Open report now? (Y/N)"
if ($openReport -eq "Y" -or $openReport -eq "y") {
    notepad $REPORT_FILE
}
