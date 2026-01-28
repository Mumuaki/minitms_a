import asyncio
import logging
import sys
import os
from datetime import datetime

# Добавляем корневую директорию проекта в sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))

from backend.src.infrastructure.external_services.trans_eu.client import TransEuClient

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_cargo_search_specific():
    """
    Новый тест по запросу пользователя:
    Загрузка: Šamorín, Slovakia (SK)
    Разгрузка: Австрия (AT), 8022
    Вес: 0.9 (по умолчанию)
    Длина: 4.8 (по умолчанию)
    Дата загрузки: Сегодня (25.01.2026)
    Дата выгрузки: до 30.01.2026
    """
    client = TransEuClient()
    try:
        logger.info("Starting Specific Cargo Search Test...")
        await client.start()
        
        # 1. Логин (через сессию или форму)
        success = await client.login()
        if not success:
            logger.error("Login process failed. Check credentials in .env")
            return

        # 2. Параметры поиска
        today_str = datetime.now().strftime("%d.%m.%Y")
        loading_loc = "Šamorín, SK"
        unloading_loc = "AT, 8022"
        date_unload_to = "30.01.2026"
        
        logger.info(f"Executing search: {loading_loc} -> {unloading_loc}")
        logger.info(f"Dates: Loading from {today_str}, Unloading until {date_unload_to}")

        search_ok = await client.search_offers(
            loading_location=loading_loc,
            unloading_location=unloading_loc,
            date_from=today_str,
            date_to=None, # Любая дата загрузки начиная с сегодня
            unloading_date_from=None, 
            unloading_date_to=date_unload_to,
            weight_to="0.9",
            loading_radius=75,
            unloading_radius=75
        )
        
        if not search_ok:
            logger.error("Search workflow failed visually or by timeout.")
            return

        # 3. Извлечение результатов
        logger.info("Extracting search results from page...")
        offers = await client.get_search_results()
        
        print("\n" + "="*80)
        print(f"RESULTS FOR: {loading_loc} -> {unloading_loc} (until {date_unload_to})")
        print("="*80)
        
        if offers:
            print(f"{'#':<3} | {'ID':<12} | {'Loading City':<20} | {'Unloading City':<20} | {'Price':<10}")
            print("-" * 80)
            for i, cargo in enumerate(offers):
                l_city = cargo.loading_place.get('city', 'N/A')
                u_city = cargo.unloading_place.get('city', 'N/A')
                print(f"{i+1:<3} | {cargo.external_id:<12} | {l_city[:20]:<20} | {u_city[:20]:<20} | {cargo.price} EUR")
        else:
            print("No offers found for current criteria.")
        
        print("="*80 + "\n")

    except ValueError as ve:
        logger.error(f"Validation Error: {ve}")
    except Exception as e:
        logger.exception(f"Unexpected error during test: {e}")
    finally:
        # Оставляем браузер открытым для визуальной проверки, как в предыдущих тестах
        # await client.stop() 
        logger.info("Test finished. Browser remains open for manual inspection.")

if __name__ == "__main__":
    asyncio.run(test_cargo_search_specific())
