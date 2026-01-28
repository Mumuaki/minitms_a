"""
Скрипт для инспекции DOM элементов фильтров на Trans.eu.
"""
import asyncio
import logging
import sys
import os

# Utils
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from backend.src.infrastructure.config.settings import settings
settings.HEADLESS_MODE = True # Headless для скорости

from backend.src.infrastructure.external_services.trans_eu.client import TransEuClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Inspector")

async def main():
    client = TransEuClient()
    try:
        await client.start()
        if not await client.login():
            logger.error("Login failed")
            return

        logger.info("Waiting for dashboard to load (10s)...")
        await client.page.wait_for_timeout(10000)

        logger.info("Expanding filters...")
        # Раскрываем фильтры (используя логику из client.py)
        expand_selectors = [
            'button:has-text("EXPAND FILTERS")', 'button:has-text("MORE FILTERS")',
            'button[data-ctx="basic-filters-form-hide-filters-preview"]', 'button[data-ctx*="filter"]'
        ]
        for sel in expand_selectors:
            try:
                btn = client.page.locator(sel).first
                if await btn.is_visible(timeout=2000):
                    await btn.click()
                    logger.info(f"Clicked expand button: {sel}")
                    await client.page.wait_for_timeout(2000)
                    break
            except: pass
        
        logger.info("Extracting data-ctx attributes...")
        
        # JS to get all data-ctx values
        data_ctx_list = await client.page.evaluate("""
            () => {
                return Array.from(document.querySelectorAll('*[data-ctx]'))
                    .map(el => el.getAttribute('data-ctx'));
            }
        """)
        
        logger.info(f"Found {len(data_ctx_list)} data-ctx elements.")
        with open("data_ctx_list.txt", "w", encoding="utf-8") as f:
            for ctx in sorted(set(data_ctx_list)):
                f.write(ctx + "\n")
        
        logger.info("List saved to data_ctx_list.txt")

        # Save HTML too just in case
        html = await client.page.content()
        with open("trans_eu_filters.html", "w", encoding="utf-8") as f:
            f.write(html)

    finally:
        await client.stop()

if __name__ == "__main__":
    asyncio.run(main())
