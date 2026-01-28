
import asyncio
import logging
import os
import sys

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from backend.src.infrastructure.external_services.trans_eu.client import TransEuClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("DOM_DEBUGGER")

async def dump_structure():
    client = TransEuClient()
    try:
        logger.info("Starting DOM Structure Debugger...")
        await client.start()
        
        success = await client.login()
        if not success:
            logger.error("Login failed. Cannot debug structure.")
            return

        # Ensure we are on the search page and filters are expanded
        await client.page.wait_for_selector('button[data-ctx="basicFilters.form.submit"]')
        
        # Close popups
        await client._close_popups()
        
        # Expand filters if needed
        basic_filters = client.page.locator('div[data-ctx="basic-filters"]')
        if not await basic_filters.is_visible():
            expand_btn = client.page.locator('button[data-ctx="basic-filters-form-hide-filters-preview"]')
            if await expand_btn.is_visible():
                await expand_btn.click()
                await client.page.wait_for_timeout(1000)

        logger.info("Extracting DOM information about search fields...")

        # Extract all relevant containers and inputs
        structure = await client.page.evaluate('''() => {
            const results = [];
            
            // Find all divs that have data-ctx
            const containers = document.querySelectorAll('div[data-ctx]');
            containers.forEach(div => {
                const ctx = div.getAttribute('data-ctx');
                const label = div.innerText.split('\\n')[0]; // First line is usually the label
                const inputs = Array.from(div.querySelectorAll('input')).map(inp => ({
                    name: inp.getAttribute('name'),
                    data_ctx: inp.getAttribute('data-ctx'),
                    value: inp.value,
                    type: inp.type
                }));
                
                if (inputs.length > 0 || ctx.includes('place') || ctx.includes('load')) {
                    results.push({
                        container_ctx: ctx,
                        label: label,
                        inputs: inputs
                    });
                }
            });

            // Also find all inputs globally just in case
            const allInputs = Array.from(document.querySelectorAll('input')).map(inp => ({
                name: inp.getAttribute('name'),
                data_ctx: inp.getAttribute('data-ctx'),
                parent_ctx: inp.parentElement.getAttribute('data-ctx') || inp.parentElement.parentElement.getAttribute('data-ctx'),
                val: inp.value
            }));

            return { fields: results, all_inputs: allInputs };
        }''')

        # Save to file
        output_path = "docs/trans_eu_dom_dump.txt"
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("=== TRANS.EU FIELD STRUCTURE DUMP ===\n\n")
            for field in structure['fields']:
                f.write(f"Container data-ctx: {field['container_ctx']}\n")
                f.write(f"Label/Text: {field['label']}\n")
                for inp in field['inputs']:
                    f.write(f"  -> Input: name={inp['name']}, data-ctx={inp['data_ctx']}, value='{inp['value']}'\n")
                f.write("-" * 40 + "\n")
            
            f.write("\n=== ALL INPUTS RAW DUMP ===\n")
            for inp in structure['all_inputs']:
                f.write(f"Input: name={inp['name']}, data-ctx={inp['data_ctx']}, parent-ctx={inp['parent_ctx']}, val='{inp['val']}'\n")

        logger.info(f"Structure dump saved to {output_path}")
        await client.page.screenshot(path="dom_debug_final.png")

    except Exception as e:
        logger.exception(f"Error: {e}")
    finally:
        await client.stop()

if __name__ == "__main__":
    asyncio.run(dump_structure())
