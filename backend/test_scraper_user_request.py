"""
Тестовый скрипт для проверки скрапера Trans.eu по запросу пользователя.
Дата: 28.01.2026

Параметры поиска:
- Загрузка: Шаморин, Словакия (SK, Šamorín)
- Разгрузка: Дортмунд, Германия (DE, Dortmund) + 150 км
- Дата загрузки: 28-29.02.2026
- Дата выгрузки: до 01.03.2026
- Длина и вес: по умолчанию
"""
import asyncio
import logging
import sys
import os

# Utils
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from backend.src.infrastructure.config.settings import settings
settings.HEADLESS_MODE = False  # Visible mode for testing

from backend.src.infrastructure.external_services.trans_eu.client import TransEuClient

# Logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("UserScraperTest")

async def main():
    logger.info("=" * 70)
    logger.info("ТЕСТ СКРАПЕРА TRANS.EU - ЗАПРОС ПОЛЬЗОВАТЕЛЯ")
    logger.info("=" * 70)
    logger.info("Параметры:")
    logger.info("  Загрузка: SK, Samorin")
    logger.info("  Разгрузка: DE, Dortmund + 150 км")
    logger.info("  Дата загрузки: 28.01.2026 - 29.01.2026")
    logger.info("  Дата выгрузки: до 01.02.2026")
    logger.info("  Макс. вес: 0.9 т")
    logger.info("  Макс. длина (LDM): 4.8 м")
    logger.info("=" * 70)

    if not settings.TRANS_EU_USERNAME:
        logger.error("❌ Нет учетных данных Trans.eu! Проверьте .env файл.")
        return

    client = TransEuClient()
    try:
        logger.info("\n[1/3] Запуск браузера...")
        await client.start()
        
        logger.info("\n[2/3] Авторизация на Trans.eu...")
        if not await client.login():
            logger.error("❌ Не удалось авторизоваться!")
            return
        
        logger.info("\n[3/3] Выполнение поиска грузов...")
        
        result = await client.search_offers(
            loading_location="SK, Samorin",
            unloading_location="DE, Dortmund",
            loading_radius=75,     # По умолчанию
            unloading_radius=150,   # По запросу пользователя
            date_from="28.01.2026",
            date_to="29.01.2026",
            unloading_date_from=None,
            unloading_date_to="01.02.2026",
            weight_to="0.9",        # По умолчанию
            length_to="4.8"         # По умолчанию
        )
        
        if result:
            logger.info("\n✅ Поиск выполнен успешно!")
        else:
            logger.warning("\n⚠️ Поиск завершён с ошибкой")
        
        logger.info("\n" + "=" * 70)
        logger.info("ТЕСТ ЗАВЕРШЁН. Нажмите Ctrl+C для выхода.")
        logger.info("=" * 70)
        
        while True:
            await asyncio.sleep(1)

    except Exception as e:
        logger.error(f"\n❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        await asyncio.sleep(60)
    finally:
        pass

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Завершение работы...")
