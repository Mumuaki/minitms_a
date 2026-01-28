
import asyncio
import logging
import sys
import os

# Utils
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from backend.src.infrastructure.config.settings import settings
settings.HEADLESS_MODE = False # Визуальный режим, чтобы календарь отрендерился

from backend.src.infrastructure.external_services.trans_eu.client import TransEuClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("CalendarInspector")

async def main():
    client = TransEuClient()
    try:
        await client.start()
        if not await client.login():
            return

        logger.info("Opening filters...")
        # Expand filters logic
        expand_selectors = ['button:has-text("EXPAND FILTERS")', 'button[data-ctx="basic-filters-form-hide-filters-preview"]']
        for sel in expand_selectors:
            try:
                btn = client.page.locator(sel).first
                if await btn.is_visible(timeout=2000):
                    await btn.click()
                    break
            except: pass
        
        logger.info("Clicking Date Input...")
        # Находим поле даты (From date)
        # Обычно это первое поле input[name="from"] внутри advanced filters
        adv_filters = client.page.locator('div[data-ctx="advanced-filters"]')
        date_input = adv_filters.locator('input[name="from"]').first
        
        if await date_input.count() > 0:
            await date_input.click()
            logger.info("Calendar should be open. Waiting 2s...")
            await client.page.wait_for_timeout(2000)
            
            # Сохраняем DOM
            html = await client.page.content()
            with open("calendar_dump.html", "w", encoding="utf-8") as f:
                f.write(html)
            logger.info("DOM saved to calendar_dump.html")
        else:
            logger.error("Date input not found")

    finally:
        await client.stop()

if __name__ == "__main__":
    asyncio.run(main())
