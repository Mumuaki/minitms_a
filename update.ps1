# PowerShell скрипт для обновления MiniTMS

$ErrorActionPreference = "Stop"

Write-Host "🔄 MiniTMS Update Script" -ForegroundColor Cyan
Write-Host "========================" -ForegroundColor Cyan

# Определение compose файла
if (Test-Path "docker-compose.vps.yml") {
    $composeFile = "docker-compose.vps.yml"
    Write-Host "📦 Используется VPS конфигурация" -ForegroundColor Cyan
} elseif (Test-Path "docker-compose.yml") {
    $composeFile = "docker-compose.yml"
    Write-Host "📦 Используется Production конфигурация" -ForegroundColor Cyan
} else {
    Write-Host "❌ Не найден docker-compose файл" -ForegroundColor Red
    exit 1
}

# Создание бэкапа БД
$backupChoice = Read-Host "Создать бэкап базы данных перед обновлением? (y/n)"
if ($backupChoice -eq "y") {
    Write-Host "💾 Создание бэкапа базы данных..." -ForegroundColor Yellow
    $backupFile = "backup_$(Get-Date -Format 'yyyyMMdd_HHmmss').sql"
    
    try {
        docker-compose -f $composeFile exec -T postgres pg_dump -U postgres mini-tms > $backupFile
        Write-Host "✅ Бэкап создан: $backupFile" -ForegroundColor Green
    } catch {
        Write-Host "⚠️  Не удалось создать бэкап" -ForegroundColor Yellow
    }
}

# Получение последних изменений
Write-Host "📥 Получение последних изменений из Git..." -ForegroundColor Cyan
if (Test-Path ".git") {
    try {
        git pull origin main
    } catch {
        try {
            git pull origin master
        } catch {
            Write-Host "⚠️  Не удалось обновить из Git" -ForegroundColor Yellow
        }
    }
} else {
    Write-Host "⚠️  Это не Git репозиторий. Пропускаем git pull." -ForegroundColor Yellow
}

# Остановка контейнеров
Write-Host "🛑 Остановка контейнеров..." -ForegroundColor Yellow
docker-compose -f $composeFile down

# Удаление старых образов
$cleanChoice = Read-Host "Удалить старые Docker образы? (y/n)"
if ($cleanChoice -eq "y") {
    Write-Host "🧹 Очистка старых образов..." -ForegroundColor Yellow
    docker system prune -f
}

# Сборка новых образов
Write-Host "🔨 Сборка новых образов..." -ForegroundColor Cyan
docker-compose -f $composeFile build --no-cache

# Запуск контейнеров
Write-Host "🚀 Запуск обновленных контейнеров..." -ForegroundColor Cyan
docker-compose -f $composeFile up -d

# Ожидание готовности
Write-Host "⏳ Ожидание готовности сервисов..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

# Применение миграций
Write-Host "📊 Применение миграций базы данных..." -ForegroundColor Cyan
try {
    docker-compose -f $composeFile exec -T backend alembic upgrade head
} catch {
    Write-Host "⚠️  Миграции не удалось применить" -ForegroundColor Yellow
}

# Проверка статуса
Write-Host ""
Write-Host "📊 Статус контейнеров:" -ForegroundColor Cyan
docker-compose -f $composeFile ps

# Проверка health endpoint
Write-Host ""
Write-Host "🏥 Проверка работоспособности API..." -ForegroundColor Cyan
Start-Sleep -Seconds 5
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -UseBasicParsing
    Write-Host "✅ API отвечает: $($response.StatusCode)" -ForegroundColor Green
} catch {
    Write-Host "⚠️  API недоступен" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "✅ Обновление завершено!" -ForegroundColor Green
Write-Host ""
Write-Host "📝 Полезные команды:" -ForegroundColor Cyan
Write-Host "   Просмотр логов:  docker-compose -f $composeFile logs -f" -ForegroundColor White
Write-Host "   Перезапуск:      docker-compose -f $composeFile restart" -ForegroundColor White
Write-Host "   Остановка:       docker-compose -f $composeFile down" -ForegroundColor White
Write-Host ""
