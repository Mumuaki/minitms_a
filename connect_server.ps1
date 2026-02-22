# Quick SSH Connection Script for MiniTMS Server

$SERVER = "89.167.70.67"
$USER = "root"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Connecting to MiniTMS Server" -ForegroundColor Cyan
Write-Host "Server: $SERVER" -ForegroundColor Yellow
Write-Host "User: $USER" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Connect via SSH
ssh ${USER}@${SERVER}
