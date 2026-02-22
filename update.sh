#!/bin/bash
# Скрипт для обновления MiniTMS на VPS

set -e

echo "🔄 MiniTMS Update Script"
echo "========================"

# Определение compose файла
if [ -f "docker-compose.vps.yml" ]; then
    COMPOSE_FILE="docker-compose.vps.yml"
    echo "📦 Используется VPS конфигурация"
elif [ -f "docker-compose.yml" ]; then
    COMPOSE_FILE="docker-compose.yml"
    echo "📦 Используется Production конфигурация"
else
    echo "❌ Не найден docker-compose файл"
    exit 1
fi

# Создание бэкапа БД (опционально)
read -p "Создать бэкап базы данных перед обновлением? (y/n): " backup_choice
if [ "$backup_choice" = "y" ]; then
    echo "💾 Создание бэкапа базы данных..."
    BACKUP_FILE="backup_$(date +%Y%m%d_%H%M%S).sql"
    
    # Попробуем создать бэкап из контейнера или локально
    if docker-compose -f $COMPOSE_FILE ps | grep -q postgres; then
        docker-compose -f $COMPOSE_FILE exec -T postgres pg_dump -U postgres mini-tms > $BACKUP_FILE
    else
        pg_dump -h localhost -U postgres mini-tms > $BACKUP_FILE 2>/dev/null || echo "⚠️  Не удалось создать бэкап (PostgreSQL недоступен)"
    fi
    
    if [ -f "$BACKUP_FILE" ]; then
        echo "✅ Бэкап создан: $BACKUP_FILE"
    fi
fi

# Получение последних изменений
echo "📥 Получение последних изменений из Git..."
if [ -d ".git" ]; then
    git pull origin main || git pull origin master || echo "⚠️  Не удалось обновить из Git"
else
    echo "⚠️  Это не Git репозиторий. Пропускаем git pull."
fi

# Остановка контейнеров
echo "🛑 Остановка контейнеров..."
docker-compose -f $COMPOSE_FILE down

# Удаление старых образов (опционально)
read -p "Удалить старые Docker образы? (y/n): " clean_choice
if [ "$clean_choice" = "y" ]; then
    echo "🧹 Очистка старых образов..."
    docker system prune -f
fi

# Сборка новых образов
echo "🔨 Сборка новых образов..."
docker-compose -f $COMPOSE_FILE build --no-cache

# Запуск контейнеров
echo "🚀 Запуск обновленных контейнеров..."
docker-compose -f $COMPOSE_FILE up -d

# Ожидание готовности
echo "⏳ Ожидание готовности сервисов..."
sleep 10

# Применение миграций
echo "📊 Применение миграций базы данных..."
docker-compose -f $COMPOSE_FILE exec -T backend alembic upgrade head || echo "⚠️  Миграции не удалось применить"

# Проверка статуса
echo ""
echo "📊 Статус контейнеров:"
docker-compose -f $COMPOSE_FILE ps

# Проверка health endpoint
echo ""
echo "🏥 Проверка работоспособности API..."
sleep 5
curl -s http://localhost:8000/health || echo "⚠️  API недоступен"

echo ""
echo "✅ Обновление завершено!"
echo ""
echo "📝 Полезные команды:"
echo "   Просмотр логов:  docker-compose -f $COMPOSE_FILE logs -f"
echo "   Перезапуск:      docker-compose -f $COMPOSE_FILE restart"
echo "   Остановка:       docker-compose -f $COMPOSE_FILE down"
echo ""
