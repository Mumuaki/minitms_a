# PowerShell скрипт для развертывания MiniTMS на Windows

$ErrorActionPreference = "Stop"

Write-Host "🚀 MiniTMS Deployment Script" -ForegroundColor Cyan
Write-Host "==============================" -ForegroundColor Cyan

# Проверка наличия Docker
try {
    docker --version | Out-Null
    Write-Host "✅ Docker установлен" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker не установлен. Установите Docker Desktop и попробуйте снова." -ForegroundColor Red
    exit 1
}

try {
    docker-compose --version | Out-Null
    Write-Host "✅ Docker Compose установлен" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker Compose не установлен." -ForegroundColor Red
    exit 1
}

# Выбор режима развертывания
Write-Host ""
Write-Host "Выберите режим развертывания:" -ForegroundColor Yellow
Write-Host "1) Development (с hot-reload)"
Write-Host "2) Production (полный стек в Docker)"
Write-Host "3) VPS (PostgreSQL и Redis уже установлены)"
$mode = Read-Host "Введите номер (1-3)"

switch ($mode) {
    "1" {
        Write-Host "📦 Запуск в режиме Development..." -ForegroundColor Cyan
        $composeFile = "docker-compose.dev.yml"
    }
    "2" {
        Write-Host "📦 Запуск в режиме Production..." -ForegroundColor Cyan
        $composeFile = "docker-compose.yml"
    }
    "3" {
        Write-Host "📦 Запуск для VPS..." -ForegroundColor Cyan
        $composeFile = "docker-compose.vps.yml"
    }
    default {
        Write-Host "❌ Неверный выбор" -ForegroundColor Red
        exit 1
    }
}

# Проверка наличия .env файлов
if (-not (Test-Path "backend\.env")) {
    Write-Host "⚠️  Файл backend\.env не найден" -ForegroundColor Yellow
    $createEnv = Read-Host "Создать из .env.example? (y/n)"
    if ($createEnv -eq "y") {
        Copy-Item "backend\.env.example" "backend\.env"
        Write-Host "✅ Создан backend\.env из .env.example" -ForegroundColor Green
        Write-Host "⚠️  Пожалуйста, отредактируйте backend\.env перед продолжением" -ForegroundColor Yellow
        Read-Host "Нажмите Enter после редактирования .env файла"
    } else {
        Write-Host "❌ Невозможно продолжить без .env файла" -ForegroundColor Red
        exit 1
    }
}

# Остановка существующих контейнеров
Write-Host "🛑 Остановка существующих контейнеров..." -ForegroundColor Yellow
docker-compose -f $composeFile down 2>$null

# Сборка образов
Write-Host "🔨 Сборка Docker образов..." -ForegroundColor Cyan
docker-compose -f $composeFile build

# Запуск контейнеров
Write-Host "🚀 Запуск контейнеров..." -ForegroundColor Cyan
docker-compose -f $composeFile up -d

# Ожидание готовности сервисов
Write-Host "⏳ Ожидание готовности сервисов..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

# Применение миграций
if ($mode -ne "3") {
    Write-Host "📊 Применение миграций базы данных..." -ForegroundColor Cyan
    try {
        docker-compose -f $composeFile exec -T backend alembic upgrade head
    } catch {
        Write-Host "⚠️  Миграции не удалось применить (возможно, БД недоступна)" -ForegroundColor Yellow
    }
}

# Проверка статуса
Write-Host ""
Write-Host "📊 Статус контейнеров:" -ForegroundColor Cyan
docker-compose -f $composeFile ps

Write-Host ""
Write-Host "✅ Развертывание завершено!" -ForegroundColor Green
Write-Host ""
Write-Host "🌐 Приложение доступно:" -ForegroundColor Cyan
switch ($mode) {
    "1" {
        Write-Host "   Frontend: http://localhost:5173" -ForegroundColor White
        Write-Host "   Backend:  http://localhost:8000" -ForegroundColor White
        Write-Host "   API Docs: http://localhost:8000/docs" -ForegroundColor White
    }
    "2" {
        Write-Host "   Frontend: http://localhost:80" -ForegroundColor White
        Write-Host "   Backend:  http://localhost:8000" -ForegroundColor White
        Write-Host "   API Docs: http://localhost:8000/docs" -ForegroundColor White
    }
    "3" {
        Write-Host "   Frontend: http://localhost:80" -ForegroundColor White
        Write-Host "   Backend:  http://localhost:8000" -ForegroundColor White
        Write-Host "   API Docs: http://localhost:8000/docs" -ForegroundColor White
    }
}

Write-Host ""
Write-Host "📝 Полезные команды:" -ForegroundColor Cyan
Write-Host "   Просмотр логов:     docker-compose -f $composeFile logs -f" -ForegroundColor White
Write-Host "   Остановка:          docker-compose -f $composeFile down" -ForegroundColor White
Write-Host "   Перезапуск:         docker-compose -f $composeFile restart" -ForegroundColor White
Write-Host "   Статус:             docker-compose -f $composeFile ps" -ForegroundColor White
Write-Host ""
