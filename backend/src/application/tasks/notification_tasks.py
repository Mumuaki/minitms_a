import logging
from backend.src.infrastructure.messaging.celery_app import celery_app

logger = logging.getLogger(__name__)

@celery_app.task(name="backend.src.application.tasks.notification_tasks.send_telegram_alert")
def send_telegram_alert(message: str):
    """
    Отправляет уведомление оператору в Telegram.
    (Заглушка. Будет реализована в модуле уведомлений).
    """
    logger.info(f"TELEGRAM ALERT: {message}")
    # TODO: интеграция с python-telegram-bot или requests к API Telegram
    return True
