import asyncio
import logging
import sys
import os
import json

# Utils
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from backend.src.infrastructure.config.settings import settings
settings.HEADLESS_MODE = False 

from backend.src.infrastructure.external_services.trans_eu.client import TransEuClient

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("CalendarInspector")

async def main():
    logger.info("Запуск инспектора календаря...")
    client = TransEuClient()
    try:
        await client.start()
        await client.page.set_viewport_size({"width": 1280, "height": 800})

        if not await client.login():
            return

        logger.info("Навигация к фильтрам...")
        basic_filters = client.page.locator('div[data-ctx="basic-filters"]')
        if not await basic_filters.is_visible():
            expand_btn = client.page.locator('button[data-ctx="basic-filters-form-hide-filters-preview"]')
            if await expand_btn.is_visible():
                await expand_btn.click()
                await basic_filters.wait_for(state="visible", timeout=5000)

        # Focus date input "From" of Loading
        logger.info("Кликаем по полю 'Дата загрузки' (От)...")
        adv_filters = client.page.locator('div[data-ctx="advanced-filters"]')
        first_from_input = adv_filters.locator('input[name="from"]').nth(0)
        await first_from_input.click()
        
        logger.info("Ждем появления календаря 2 секунды...")
        await client.page.wait_for_timeout(2000)
        
        # JS Inspection for Calendar
        js_script = """
        () => {
            const results = {};
            // Look for visible layers with date-related stuff
            const all = document.querySelectorAll('*');
            const calendarParts = [];
            
            // Heuristic search for calendar items (numeric cells)
            for (const el of all) {
                const rect = el.getBoundingClientRect();
                if (rect.width > 0 && rect.height > 0) {
                    const text = el.innerText ? el.innerText.trim() : '';
                    // If text is a number 1-31 and part of a popup
                    if (/^[0-9]{1,2}$/.test(text)) {
                         // Check parentage for 'portal' or 'dropdown' or 'calendar'
                         let p = el;
                         let isCalendar = false;
                         while(p && p !== document.body) {
                             if(p.className.toLowerCase().includes('calendar') || 
                                p.className.toLowerCase().includes('date') || 
                                p.id.includes('Dropdown')) {
                                    isCalendar = true;
                                    break;
                             }
                             p = p.parentElement;
                         }
                         if(isCalendar) {
                            calendarParts.push({
                                tagName: el.tagName,
                                className: el.className,
                                text: text,
                                ariaLabel: el.getAttribute('aria-label'),
                                title: el.getAttribute('title'),
                                zIndex: window.getComputedStyle(el).zIndex,
                                rect: {x: rect.x, y: rect.y}
                            });
                         }
                    }
                }
            }
            results.days = calendarParts;
            
            // Also find the main container of the calendar
            results.containers = [];
            const portals = document.querySelectorAll('[id*="Dropdown"], [class*="portal"], [class*="Popup"]');
            portals.forEach(p => {
                const rect = p.getBoundingClientRect();
                if(rect.width > 50) {
                    results.containers.push({
                        id: p.id,
                        className: p.className,
                        html: p.outerHTML.substring(0, 500)
                    });
                }
            });
            
            return results;
        }
        """
        
        data = await client.page.evaluate(js_script)
        
        with open("calendar_report.json", "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            
        logger.info("Отчет сохранен в 'calendar_report.json'")
        await client.page.screenshot(path="calendar_view.png")

    except Exception as e:
        logger.error(f"Error: {e}")
    finally:
        await client.stop()

if __name__ == "__main__":
    asyncio.run(main())
