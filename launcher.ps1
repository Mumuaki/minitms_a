# MiniTMS Server Management Launcher
# Interactive menu for all management scripts

$VERSION = "1.0"
$SERVER = "89.167.70.67"

function Show-Banner {
    Clear-Host
    Write-Host "========================================================" -ForegroundColor Cyan
    Write-Host "           MiniTMS Server Management v$VERSION          " -ForegroundColor Cyan
    Write-Host "========================================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "  Server: $SERVER" -ForegroundColor Yellow
    Write-Host "  User: root" -ForegroundColor Yellow
    Write-Host ""
}

function Show-Menu {
    Write-Host "========================================================" -ForegroundColor White
    Write-Host "                    MAIN MENU                           " -ForegroundColor White
    Write-Host "========================================================" -ForegroundColor White
    Write-Host ""
    
    Write-Host "  [DIAGNOSTICS]" -ForegroundColor Green
    Write-Host "  1. Quick Server Check (30 sec)" -ForegroundColor White
    Write-Host "  2. Detailed Module Check (1-2 min)" -ForegroundColor White
    Write-Host "  3. Business Requirements Test (2-3 min)" -ForegroundColor White
    Write-Host "  4. Feature Testing (1-2 min)" -ForegroundColor White
    Write-Host "  5. Full Diagnostic Report (5-7 min)" -ForegroundColor White
    Write-Host ""
    
    Write-Host "  [MANAGEMENT]" -ForegroundColor Yellow
    Write-Host "  6. Interactive Fix Menu" -ForegroundColor White
    Write-Host "  7. Connect to Server (SSH)" -ForegroundColor White
    Write-Host ""
    
    Write-Host "  [DOCUMENTATION]" -ForegroundColor Cyan
    Write-Host "  8. Quick Start Guide" -ForegroundColor White
    Write-Host "  9. Full Documentation" -ForegroundColor White
    Write-Host "  10. Index & Navigation" -ForegroundColor White
    Write-Host ""
    
    Write-Host "  [EXIT]" -ForegroundColor Red
    Write-Host "  0. Exit" -ForegroundColor White
    Write-Host ""
    Write-Host "========================================================" -ForegroundColor White
    Write-Host ""
}

function Run-QuickCheck {
    Write-Host "`n[*] Running Quick Server Check..." -ForegroundColor Green
    Write-Host "This will take about 30 seconds...`n" -ForegroundColor Gray
    & "d:\MiniTMS\check_server.ps1"
}

function Run-ModuleCheck {
    Write-Host "`n[*] Running Detailed Module Check..." -ForegroundColor Green
    Write-Host "This will take about 1-2 minutes...`n" -ForegroundColor Gray
    & "d:\MiniTMS\check_modules.ps1"
}

function Run-BusinessRequirements {
    Write-Host "`n[*] Running Business Requirements Test..." -ForegroundColor Green
    Write-Host "This will take about 2-3 minutes...`n" -ForegroundColor Gray
    & "d:\MiniTMS\test_business_requirements.ps1"
}

function Run-FeatureTest {
    Write-Host "`n[*] Running Feature Testing..." -ForegroundColor Green
    Write-Host "This will take about 1-2 minutes...`n" -ForegroundColor Gray
    & "d:\MiniTMS\test_features.ps1"
}

function Run-FullDiagnostic {
    Write-Host "`n[*] Running Full Diagnostic Report..." -ForegroundColor Green
    Write-Host "This will take about 5-7 minutes...`n" -ForegroundColor Gray
    & "d:\MiniTMS\run_full_diagnostic.ps1"
}

function Run-FixMenu {
    Write-Host "`n[*] Opening Interactive Fix Menu..." -ForegroundColor Yellow
    & "d:\MiniTMS\fix_server.ps1"
}

function Connect-ToServer {
    Write-Host "`n[*] Connecting to Server..." -ForegroundColor Cyan
    & "d:\MiniTMS\connect_server.ps1"
}

function Open-QuickStart {
    Write-Host "`n[*] Opening Quick Start Guide..." -ForegroundColor Cyan
    notepad "d:\MiniTMS\QUICK_START.md"
}

function Open-Documentation {
    Write-Host "`n[*] Opening Full Documentation..." -ForegroundColor Cyan
    notepad "d:\MiniTMS\README_SERVER_SCRIPTS.md"
}

function Open-Index {
    Write-Host "`n[*] Opening Index..." -ForegroundColor Cyan
    notepad "d:\MiniTMS\INDEX.md"
}

# Main Loop
while ($true) {
    Show-Banner
    Show-Menu
    
    $choice = Read-Host "Enter your choice"
    
    switch ($choice) {
        "1" { 
            Run-QuickCheck
            Write-Host "`n[OK] Quick check complete!" -ForegroundColor Green
        }
        "2" { 
            Run-ModuleCheck
            Write-Host "`n[OK] Module check complete!" -ForegroundColor Green
        }
        "3" { 
            Run-BusinessRequirements
            Write-Host "`n[OK] Business requirements test complete!" -ForegroundColor Green
        }
        "4" { 
            Run-FeatureTest
            Write-Host "`n[OK] Feature testing complete!" -ForegroundColor Green
        }
        "5" { 
            Run-FullDiagnostic
            Write-Host "`n[OK] Full diagnostic complete!" -ForegroundColor Green
        }
        "6" { 
            Run-FixMenu
            Write-Host "`n[OK] Returned from fix menu" -ForegroundColor Green
        }
        "7" { 
            Connect-ToServer
            Write-Host "`n[OK] Disconnected from server" -ForegroundColor Green
        }
        "8" { 
            Open-QuickStart
        }
        "9" { 
            Open-Documentation
        }
        "10" { 
            Open-Index
        }
        "0" { 
            Write-Host "`nGoodbye!" -ForegroundColor Green
            Start-Sleep -Seconds 1
            exit 
        }
        default { 
            Write-Host "`n[ERROR] Invalid choice. Please try again." -ForegroundColor Red 
        }
    }
    
    if ($choice -ne "0") {
        Write-Host "`nPress any key to return to main menu..." -ForegroundColor Gray
        $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
    }
}
