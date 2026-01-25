import asyncio
import logging
import sys
import os

# Utils
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from backend.src.infrastructure.config.settings import settings
settings.HEADLESS_MODE = False  # Visible mode

from backend.src.infrastructure.external_services.trans_eu.client import TransEuClient

# Logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("VisualSearchTest")

async def main():
    logger.info("Запуск визуального теста ПОИСКА (v4 - Persistent Check)...")
    logger.info("ВНИМАНИЕ: Браузер НЕ закроется автоматически. Закройте терминал или окно вручную для выхода.")

    if not settings.TRANS_EU_USERNAME:
        logger.error("Нет учетных данных!")
        return

    client = TransEuClient()
    try:
        await client.start()
        
        # 1. Login
        logger.info("1. Проверка сессии...")
        if not await client.login():
            logger.error("Не удалось войти")
            return

        # 2. Search
        logger.info("2. Тест поиска...")
        # Test: Vienna -> Munich with INVALID dates (Unloading before Loading)
        loading = "AT, Vienna"
        unloading = "DE, Munich"
        
        logger.info(f"2. Тест ВАЛИДАЦИИ: Загрузка (27.01) > Разгрузка (26.01)")
        try:
            await client.search_offers(
                loading_location=loading,
                unloading_location=unloading,
                loading_radius=75,
                unloading_radius=200,
                date_from="27.01.2026",
                date_to="27.01.2026",
                unloading_date_from="26.01.2026", # ERROR: Before Loading
                unloading_date_to="26.01.2026"
            )
        except ValueError as e:
            logger.info(f"!!! ПЕРЕХВАЧЕНА ОШИБКА ВАЛИДАЦИИ: {e} !!!")
        
        logger.info(">>> ТЕСТ ЗАВЕРШЕН <<<")
        logger.info("Браузер остается открытым. Скрипт переходит в режим ожидания...")
        
        # Бесконечный цикл, чтобы скрипт не завершился и контекст не закрылся
        while True:
            await asyncio.sleep(1)

    except Exception as e:
        logger.error(f"Error: {e}")
        # Даже при ошибке не закрываем сразу, чтобы можно было увидеть консоль
        await asyncio.sleep(60)
        await client.stop()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nЗавершение работы...")
