# Dockerfile для Backend (FastAPI)
FROM python:3.11-slim

# Установка переменных окружения
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    postgresql-client \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Структура внутри контейнера:
#   /workspace/backend/   ← исходники (main.py, src/, requirements.txt)
#   PYTHONPATH=/workspace → import backend.src.* работает корректно
WORKDIR /workspace

# Сначала устанавливаем зависимости (кэш слоя не инвалидируется при смене кода)
COPY requirements.txt ./backend/
RUN pip install --no-cache-dir -r ./backend/requirements.txt

# Копируем весь backend-код в /workspace/backend/
COPY . ./backend/

# Создание пользователя без root прав
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /workspace
USER appuser

# PYTHONPATH=/workspace позволяет находить пакет "backend" как /workspace/backend/
ENV PYTHONPATH=/workspace

WORKDIR /workspace/backend

# Expose порт
EXPOSE 8000

# Команда запуска (можно переопределить в docker-compose.yml)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
