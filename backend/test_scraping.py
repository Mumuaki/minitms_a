"""
Тестовый скрипт для проверки скрапинга Trans.eu.
Дата: 25.01.2026
"""
import asyncio
import logging
import sys
import os
from datetime import datetime, timedelta

# Utils
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from backend.src.infrastructure.config.settings import settings
settings.HEADLESS_MODE = False  # Visible mode for testing

from backend.src.infrastructure.external_services.trans_eu.client import TransEuClient

# Logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("ScrapingTest")

async def main():
    logger.info("=" * 60)
    logger.info("ТЕСТ СКРАПИНГА TRANS.EU")
    logger.info("=" * 60)
    logger.info("ВНИМАНИЕ: Браузер НЕ закроется автоматически.")
    logger.info("Нажмите Ctrl+C для завершения.")
    logger.info("=" * 60)

    if not settings.TRANS_EU_USERNAME:
        logger.error("❌ Нет учетных данных Trans.eu! Проверьте .env файл.")
        return

    logger.info(f"✅ Учётные данные найдены: {settings.TRANS_EU_USERNAME}")

    client = TransEuClient()
    try:
        # 1. Запуск браузера
        logger.info("\n[1/3] Запуск браузера...")
        await client.start()
        logger.info("✅ Браузер запущен")
        
        # 2. Авторизация
        logger.info("\n[2/3] Авторизация на Trans.eu...")
        if not await client.login():
            logger.error("❌ Не удалось авторизоваться!")
            return
        logger.info("✅ Авторизация успешна")

        # 3. Поиск грузов
        logger.info("\n[3/3] Поиск грузов...")
        
        # Параметры поиска (актуальные даты)
        today = datetime.now()
        tomorrow = today + timedelta(days=1)
        day_after = today + timedelta(days=2)
        
        loading = "SK, Bratislava"  # Словакия, Братислава
        unloading = "DE, Berlin"     # Германия, Берлин
        
        date_from = today.strftime("%d.%m.%Y")
        date_to = tomorrow.strftime("%d.%m.%Y")
        unloading_date_from = tomorrow.strftime("%d.%m.%Y")
        unloading_date_to = day_after.strftime("%d.%m.%Y")
        
        logger.info(f"   Маршрут: {loading} → {unloading}")
        logger.info(f"   Дата загрузки: {date_from} - {date_to}")
        logger.info(f"   Дата разгрузки: {unloading_date_from} - {unloading_date_to}")
        logger.info(f"   Радиус загрузки: +75 км")
        logger.info(f"   Радиус разгрузки: +200 км")
        logger.info(f"   Макс. вес: 0.9 т")
        
        result = await client.search_offers(
            loading_location=loading,
            unloading_location=unloading,
            loading_radius=75,
            unloading_radius=200,
            date_from=date_from,
            date_to=date_to,
            unloading_date_from=unloading_date_from,
            unloading_date_to=unloading_date_to,
            weight_to="0.9"
        )
        
        if result:
            logger.info("✅ Поиск выполнен успешно!")
        else:
            logger.warning("⚠️ Поиск завершён с ошибкой")
        
        logger.info("\n" + "=" * 60)
        logger.info("ТЕСТ ЗАВЕРШЁН")
        logger.info("Браузер остаётся открытым для ручной проверки.")
        logger.info("Нажмите Ctrl+C для завершения.")
        logger.info("=" * 60)
        
        # Бесконечный цикл, чтобы скрипт не завершился
        while True:
            await asyncio.sleep(1)

    except ValueError as e:
        logger.error(f"❌ Ошибка валидации: {e}")
        await asyncio.sleep(30)
    except Exception as e:
        logger.error(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        await asyncio.sleep(60)
    finally:
        # При выходе закрываем браузер
        pass

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Завершение работы...")
