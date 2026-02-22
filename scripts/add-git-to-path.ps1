# Добавить D:\Git в пользовательскую переменную PATH (постоянно для всех приложений).
# Запуск: powershell -ExecutionPolicy Bypass -File scripts/add-git-to-path.ps1

$gitPath = "D:\Git\bin"
$currentPath = [Environment]::GetEnvironmentVariable("Path", "User")
if ($currentPath -split ";" -contains $gitPath) {
  Write-Host "D:\Git уже есть в PATH." -ForegroundColor Green
  exit 0
}
[Environment]::SetEnvironmentVariable("Path", "$gitPath;$currentPath", "User")
Write-Host "Добавлено: D:\Git\bin в пользовательский PATH." -ForegroundColor Green
Write-Host "Перезапустите терминал или Cursor, чтобы применить." -ForegroundColor Yellow
