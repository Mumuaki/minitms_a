"""
celery_app.py — конфигурация и инстанс Celery для MiniTMS.

Брокер и бэкенд результатов: Redis (через REDIS_URL из .env).
Autodiscovery задач: добавлять новые модули с задачами в CELERY_IMPORTS.
"""

import os
from celery import Celery

from backend.src.infrastructure.config.settings import settings

app = Celery(
    "minitms",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=[
        "backend.src.application.tasks.scraping_tasks",
        "backend.src.application.tasks.gps_tasks"
    ]
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

    # Маршрутизация задач
    task_routes={
        "backend.src.application.tasks.scraping_tasks.*": {"queue": "scraping"},
        "backend.src.application.tasks.gps_tasks.*": {"queue": "celery"},
        "backend.src.application.tasks.notification_tasks.*": {"queue": "notifications"},
    },

    # Лимиты времени (300 сек для ручного решения капчи)
    task_time_limit=330,
    task_soft_time_limit=300,
)

from celery.schedules import crontab

app.conf.beat_schedule = {
    "sync-daily-mileage-at-midnight": {
        "task": "sync_daily_mileage",
        "schedule": crontab(hour=0, minute=5),
    },
}

# Имя переменной совпадает с GEMINI.md — celery_app (для ссылки в compose)
celery_app = app
