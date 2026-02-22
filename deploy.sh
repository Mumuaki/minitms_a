#!/bin/bash
# Скрипт для развертывания MiniTMS на VPS

set -e

echo "🚀 MiniTMS Deployment Script"
echo "=============================="

# Проверка наличия Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker не установлен. Установите Docker и попробуйте снова."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose не установлен. Установите Docker Compose и попробуйте снова."
    exit 1
fi

echo "✅ Docker и Docker Compose установлены"

# Выбор режима развертывания
echo ""
echo "Выберите режим развертывания:"
echo "1) Development (с hot-reload)"
echo "2) Production (полный стек в Docker)"
echo "3) VPS (PostgreSQL и Redis уже установлены)"
read -p "Введите номер (1-3): " mode

case $mode in
    1)
        echo "📦 Запуск в режиме Development..."
        COMPOSE_FILE="docker-compose.dev.yml"
        ;;
    2)
        echo "📦 Запуск в режиме Production..."
        COMPOSE_FILE="docker-compose.yml"
        ;;
    3)
        echo "📦 Запуск для VPS..."
        COMPOSE_FILE="docker-compose.vps.yml"
        ;;
    *)
        echo "❌ Неверный выбор"
        exit 1
        ;;
esac

# Проверка наличия .env файлов
if [ ! -f "backend/.env" ]; then
    echo "⚠️  Файл backend/.env не найден"
    read -p "Создать из .env.example? (y/n): " create_env
    if [ "$create_env" = "y" ]; then
        cp backend/.env.example backend/.env
        echo "✅ Создан backend/.env из .env.example"
        echo "⚠️  Пожалуйста, отредактируйте backend/.env перед продолжением"
        read -p "Нажмите Enter после редактирования .env файла..."
    else
        echo "❌ Невозможно продолжить без .env файла"
        exit 1
    fi
fi

# Остановка существующих контейнеров
echo "🛑 Остановка существующих контейнеров..."
docker-compose -f $COMPOSE_FILE down 2>/dev/null || true

# Сборка образов
echo "🔨 Сборка Docker образов..."
docker-compose -f $COMPOSE_FILE build

# Запуск контейнеров
echo "🚀 Запуск контейнеров..."
docker-compose -f $COMPOSE_FILE up -d

# Ожидание готовности сервисов
echo "⏳ Ожидание готовности сервисов..."
sleep 10

# Применение миграций (только для режимов с БД в Docker)
if [ "$mode" != "3" ] || [ "$COMPOSE_FILE" != "docker-compose.vps.yml" ]; then
    echo "📊 Применение миграций базы данных..."
    docker-compose -f $COMPOSE_FILE exec -T backend alembic upgrade head || echo "⚠️  Миграции не удалось применить (возможно, БД недоступна)"
fi

# Проверка статуса
echo ""
echo "📊 Статус контейнеров:"
docker-compose -f $COMPOSE_FILE ps

echo ""
echo "✅ Развертывание завершено!"
echo ""
echo "🌐 Приложение доступно:"
if [ "$mode" = "1" ]; then
    echo "   Frontend: http://localhost:5173"
    echo "   Backend:  http://localhost:8000"
    echo "   API Docs: http://localhost:8000/docs"
elif [ "$mode" = "2" ]; then
    echo "   Frontend: http://localhost:80"
    echo "   Backend:  http://localhost:8000"
    echo "   API Docs: http://localhost:8000/docs"
else
    echo "   Frontend: http://localhost:3000"
    echo "   Backend:  http://localhost:8000"
    echo "   API Docs: http://localhost:8000/docs"
fi

echo ""
echo "📝 Полезные команды:"
echo "   Просмотр логов:     docker-compose -f $COMPOSE_FILE logs -f"
echo "   Остановка:          docker-compose -f $COMPOSE_FILE down"
echo "   Перезапуск:         docker-compose -f $COMPOSE_FILE restart"
echo "   Статус:             docker-compose -f $COMPOSE_FILE ps"
echo ""
