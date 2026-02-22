Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8
chcp 65001 > $null

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$escapedRoot = [Regex]::Escape($projectRoot)

$targets = Get-CimInstance Win32_Process | Where-Object {
    ($_.Name -match 'python(\.exe)?|powershell(\.exe)?|node(\.exe)?') -and
    $_.CommandLine -and
    (
        ($_.CommandLine -match 'uvicorn\s+backend\.main:app') -or
        ($_.CommandLine -match '\bvite\b')
    ) -and
    ($_.CommandLine -match $escapedRoot)
}

if (-not $targets) {
    Write-Host "Процессы MiniTMS не найдены." -ForegroundColor Yellow
    exit 0
}

foreach ($proc in $targets) {
    try {
        Stop-Process -Id $proc.ProcessId -Force -ErrorAction Stop
        Write-Host ("Остановлен PID {0}: {1}" -f $proc.ProcessId, $proc.Name) -ForegroundColor Green
    }
    catch {
        Write-Host ("Не удалось остановить PID {0}: {1}" -f $proc.ProcessId, $_.Exception.Message) -ForegroundColor Red
    }
}
