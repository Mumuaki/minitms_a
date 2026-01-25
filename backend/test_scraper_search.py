"""
Тестовый скрипт для проверки скрапера Trans.eu с конкретными параметрами поиска.
Дата: 25.01.2026

Параметры поиска:
- Загрузка: Братислава (SK) + радиус по умолчанию
- Разгрузка: 8020 Грац (AT) + 200 км
- Длина груза: до 2.5 м
- Вес груза: до 0.4 т
- Дата загрузки: 26-28.01.2026
- Дата выгрузки: до 30.01.2026
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
logger = logging.getLogger("ScraperTest")

async def main():
    logger.info("=" * 70)
    logger.info("ТЕСТ СКРАПЕРА TRANS.EU - Поиск грузов")
    logger.info("=" * 70)
    logger.info("Параметры поиска:")
    logger.info("  Загрузка: Братислава (SK)")
    logger.info("  Разгрузка: 8020 Грац (AT) + 200 км")
    logger.info("  Длина груза: до 2.5 м")
    logger.info("  Вес груза: до 0.4 т")
    logger.info("  Дата загрузки: 26-28.01.2026")
    logger.info("  Дата выгрузки: до 30.01.2026")
    logger.info("=" * 70)
    logger.info("ВНИМАНИЕ: Браузер НЕ закроется автоматически.")
    logger.info("Нажмите Ctrl+C для завершения.")
    logger.info("=" * 70)

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

        # 3. Поиск грузов с заданными параметрами
        logger.info("\n[3/3] Выполнение поиска грузов...")
        
        # Параметры поиска
        loading = "SK, Bratislava"  # Братислава, Словакия
        unloading = "AT, 8020, Graz"  # Грац, Австрия с индексом
        
        # Даты
        loading_date_from = "15.04.2026"
        loading_date_to = "18.04.2026"
        unloading_date_to = "20.04.2026"
        
        # Вес до 0.4 т
        weight_to = "0.4"
        
        logger.info(f"\n📍 Маршрут:")
        logger.info(f"   Загрузка: {loading} + 75 км")
        logger.info(f"   Разгрузка: {unloading} + 200 км")
        logger.info(f"\n📅 Даты:")
        logger.info(f"   Загрузка: {loading_date_from} - {loading_date_to}")
        logger.info(f"   Разгрузка: до {unloading_date_to}")
        logger.info(f"\n📦 Параметры груза:")
        logger.info(f"   Вес: до {weight_to} т")
        logger.info(f"   Длина: до 2.5 м")
        
        result = await client.search_offers(
            loading_location=loading,
            unloading_location=unloading,
            loading_radius=75,  # По умолчанию +75 км (согласно спецификации)
            unloading_radius=200,  # 200 км
            date_from=loading_date_from,
            date_to=loading_date_to,
            unloading_date_from=None,  # Не указываем начало разгрузки
            unloading_date_to=unloading_date_to,
            weight_to=weight_to,
            length_to="2.5"
        )
        
        if result:
            logger.info("\n✅ Поиск выполнен успешно!")
            logger.info("\n💡 Проверьте результаты в открытом браузере.")
        else:
            logger.warning("\n⚠️ Поиск завершён с ошибкой")
        
        logger.info("\n" + "=" * 70)
        logger.info("ТЕСТ ЗАВЕРШЁН")
        logger.info("Браузер остаётся открытым для проверки результатов.")
        logger.info("Нажмите Ctrl+C для завершения.")
        logger.info("=" * 70)
        
        # Бесконечный цикл, чтобы скрипт не завершился
        while True:
            await asyncio.sleep(1)

    except ValueError as e:
        logger.error(f"\n❌ Ошибка валидации: {e}")
        await asyncio.sleep(30)
    except Exception as e:
        logger.error(f"\n❌ Ошибка: {e}")
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
