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
logger = logging.getLogger("Inspector")

async def main():
    logger.info("Запуск инспектора элементов...")
    client = TransEuClient()
    try:
        await client.start()
        # Ensure window is large enough
        await client.page.set_viewport_size({"width": 1280, "height": 800})

        if not await client.login():
            return

        logger.info("Навигация к фильтрам...")
        # Expand filters
        basic_filters = client.page.locator('div[data-ctx="basic-filters"]')
        if not await basic_filters.is_visible():
            expand_btn = client.page.locator('button[data-ctx="basic-filters-form-hide-filters-preview"]')
            if await expand_btn.is_visible():
                await expand_btn.click()
                await basic_filters.wait_for(state="visible", timeout=5000)

        # Trigger Dropdown
        logger.info("Активация выпадающего списка...")
        container = client.page.locator('div[data-ctx="place-loading_place-0"]')
        
        # Clear if needed
        clear_btn = container.locator('svg[data-ctx="clear"]')
        if await clear_btn.count() > 0 and await clear_btn.is_visible():
            await clear_btn.click(force=True)
            await client.page.wait_for_timeout(500)

        # Click label
        await container.locator('label[data-ctx="select"]').click(force=True)
        await client.page.wait_for_timeout(500)
        
        # Type unique text
        test_text = "Komorniki"
        logger.info(f"Печатаем '{test_text}'...")
        await client.page.keyboard.type(test_text, delay=100)
        
        logger.info("Ждем 3 секунды...")
        await client.page.wait_for_timeout(3000)
        
        # --- JS INSPECTION ---
        logger.info("Выполняем JS-инспекцию DOM...")
        
        js_script = """
        () => {
            const results = {};
            
            // 1. Find elements containing text "Komorniki"
            const allElements = document.querySelectorAll('*');
            const matches = [];
            
            for (const el of allElements) {
                // Check direct text content (shallow)
                if (el.childNodes.length) {
                    for (const node of el.childNodes) {
                        if (node.nodeType === Node.TEXT_NODE && node.textContent.includes('Komorniki')) {
                            // Don't include the input field itself if possible
                            if (el.tagName !== 'INPUT') {
                                matches.push(el);
                            }
                        }
                    }
                }
            }
            
            results.matches = matches.map(el => {
                let rect = el.getBoundingClientRect();
                return {
                    tagName: el.tagName,
                    className: el.className,
                    id: el.id,
                    innerText: el.innerText ? el.innerText.substring(0, 50) : '',
                    visible: (rect.width > 0 && rect.height > 0),
                    zIndex: window.getComputedStyle(el).zIndex,
                    role: el.getAttribute('role'),
                    parents: getParentChain(el)
                };
            });

            // 2. Find high z-index containers (Potential Modals/Dropdowns)
            results.layers = [];
            const bodyChildren = document.body.children;
            for (const el of bodyChildren) {
                const style = window.getComputedStyle(el);
                const rect = el.getBoundingClientRect();
                if (style.position === 'absolute' || style.position === 'fixed') {
                     if (rect.width > 0 && rect.height > 0) {
                         results.layers.push({
                             tagName: el.tagName,
                             className: el.className,
                             zIndex: style.zIndex,
                             rect: {x: rect.x, y: rect.y, w: rect.width, h: rect.height},
                             htmlSnippet: el.outerHTML.substring(0, 200)
                         });
                     }
                }
            }
            
            function getParentChain(el) {
                const chain = [];
                let curr = el.parentElement;
                while(curr && curr.tagName !== 'BODY') {
                    chain.push(`${curr.tagName}.${curr.className.replace(/ /g, '.')}[id="${curr.id}"]`);
                    curr = curr.parentElement;
                }
                return chain;
            }

            return results;
        }
        """
        
        inspection_data = await client.page.evaluate(js_script)
        
        logger.info("Сохраняем отчет...")
        with open("inspection_report.json", "w", encoding="utf-8") as f:
            json.dump(inspection_data, f, indent=2, ensure_ascii=False)
            
        logger.info("Отчет сохранен в 'inspection_report.json'")
        
        # Also snapshot again just in case
        await client.page.screenshot(path="inspection_view.png")

    except Exception as e:
        logger.error(f"Error: {e}")
    finally:
        # Don't close immediately to allow user view if needed, but for inspector auto-close is ok
        await client.stop()

if __name__ == "__main__":
    asyncio.run(main())
