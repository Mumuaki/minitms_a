import asyncio
import logging
import sys
import os

# Добавляем корневую директорию проекта в sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))

from backend.src.infrastructure.external_services.trans_eu.client import TransEuClient

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_extraction():
    """
    Интеграционный тест для проверки цепочки:
    Запуск -> Логин -> Поиск -> Извлечение данных -> Маппинг.
    """
    client = TransEuClient()
    try:
        logger.info("Starting Trans.eu Integration Test...")
        await client.start()
        
        # 1. Логин (использует сессию из профиля, если она жива)
        success = await client.login()
        if not success:
            logger.error("Login process failed.")
            return

        # 2. Поиск грузов
        # Загрузка: Šamorín, SK
        # Разгрузка: AT, 8022
        # Дата загрузки: 26.01.2026 (Сегодня)
        # Дата разгрузки: 27.01.2026 (Завтра)
        # Вес: 0.9 т (по спецификации), Длина: 4.8 м (по спецификации)
        logger.info("Executing search: Šamorín, SK -> AT, 8022")
        search_ok = await client.search_offers(
            loading_location="Šamorín, SK",
            unloading_location="AT, 8022",
            date_from="26.01.2026",
            date_to="26.01.2026",
            unloading_date_from="27.01.2026",
            unloading_date_to="27.01.2026",
            weight_to="0.9",
            loading_radius=75,
            unloading_radius=75
        )
        
        if not search_ok:
            logger.error("Search workflow failed.")
            return

        # 3. Извлечение и маппинг результатов
        logger.info("Extracting and mapping results from DOM...")
        offers = await client.get_search_results()
        
        logger.info(f"Test completed. Results: {len(offers)} offers found.")
        
        if offers:
            print("\n" + "="*50)
            print(f"{'#':<3} | {'External ID':<15} | {'Route':<30} | {'Price':<10}")
            print("-" * 65)
            for i, cargo in enumerate(offers[:10]): # Показываем первые 10 для проверки
                route = f"{cargo.loading_place['city']} -> {cargo.unloading_place['city']}"
                print(f"{i+1:<3} | {cargo.external_id:<15} | {route[:30]:<30} | {cargo.price} EUR")
            print("="*50 + "\n")
        else:
            logger.warning("No offers were extracted. Check selectors in parser.py or page content.")

    except Exception as e:
        logger.exception(f"Unexpected error during test: {e}")
    finally:
        # Для отладки можно закомментировать стоп, чтобы увидеть браузер
        # Но по правилам хорошего тона в тестах мы закрываем ресурсы
        # await client.stop()
        logger.info("Test finished. Browser remains open for review (if headless=False).")

if __name__ == "__main__":
    asyncio.run(test_extraction())
