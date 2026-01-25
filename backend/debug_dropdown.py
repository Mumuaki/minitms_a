import asyncio
import logging
import sys
import os

# Utils
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
# Force visible to debug
from backend.src.infrastructure.config.settings import settings
settings.HEADLESS_MODE = False 

from backend.src.infrastructure.external_services.trans_eu.client import TransEuClient

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("DropdownDebugger")

async def main():
    logger.info("Запуск отладчика выпадающего списка...")
    client = TransEuClient()
    try:
        await client.start()
        # Set window pos to 0,0 to be visible
        # await client.page.set_viewport_size({"width": 1280, "height": 800}) # Optional, profile has its own

        if not await client.login():
            return

        logger.info("Навигация к фильтрам...")
        # Ensure filters are expanded
        expand_btn = await client.page.query_selector('button[data-ctx="basic-filters-form-hide-filters-preview"]')
        if expand_btn and await expand_btn.is_visible():
            await expand_btn.click()
            await client.page.wait_for_timeout(1000)

        # Focus loading input
        logger.info("Кликаем по полю загрузки...")
        container = client.page.locator('div[data-ctx="place-loading_place-0"]')
        
        # Click label to activate
        await container.locator('label[data-ctx="select"]').click(force=True)
        await client.page.wait_for_timeout(500)
        
        # Type "Berlin"
        logger.info("Печатаем 'Berlin'...")
        await client.page.keyboard.type("Berlin", delay=100)
        
        logger.info("Ждем появления списка 5 секунд...")
        await client.page.wait_for_timeout(5000)
        
        # Dump HTML
        logger.info("Сохраняем HTML с открытым списком...")
        content = await client.page.content()
        with open("trans_eu_dropdown.html", "w", encoding="utf-8") as f:
            f.write(content)
            
        logger.info("Готово. HTML сохранен в 'trans_eu_dropdown.html'")

    except Exception as e:
        logger.error(f"Error: {e}")
    finally:
        await client.stop()

if __name__ == "__main__":
    asyncio.run(main())
