"""
celery_app.py — конфигурация и инстанс Celery для MiniTMS.

Брокер и бэкенд результатов: Redis (через REDIS_URL из .env).
Autodiscovery задач: добавлять новые модули с задачами в CELERY_IMPORTS.
"""

import os
from celery import Celery

# REDIS_URL берётся из переменной окружения (задаётся в backend/.env)
# Формат: redis://:PASSWORD@redis:6379/0
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")

app = Celery(
    "minitms",
    broker=REDIS_URL,
    backend=REDIS_URL,
)

app.conf.update(
    # Сериализация
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],

    # Временная зона
    timezone="UTC",
    enable_utc=True,

    # Автоматическое подтверждение задачи только после успешного выполнения
    task_acks_late=True,

    # Одна задача на воркер одновременно (безопасно при Playwright)
    worker_prefetch_multiplier=1,

    # Лимит хранения результатов: 1 день
    result_expires=86400,
)

# Имя переменной совпадает с GEMINI.md — celery_app (для ссылки в compose)
celery_app = app
