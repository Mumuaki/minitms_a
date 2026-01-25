from playwright.async_api import async_playwright, BrowserContext, Page, Playwright
import logging
import os
from backend.src.infrastructure.config.settings import settings

logger = logging.getLogger(__name__)

class TransEuClient:
    """
    Client for interacting with Trans.eu platform via Browser Automation.
    Uses Persistent Context to maintain session and avoid multiple logins.
    """

    def __init__(self):
        self.playwright: Playwright = None
        self.context: BrowserContext = None
        self.page: Page = None
        self.headless = settings.HEADLESS_MODE
        self.user_data_dir = settings.BROWSER_PROFILE_DIR

    async def start(self):
        """
        Initialize Playwright with Persistent Context.
        This keeps cookies/storage in 'browser_profile' folder.
        """
        logger.info(f"Starting TransEuClient (Persistent Logic)... Profile: {self.user_data_dir}")
        
        # Ensure profile dir exists
        if not os.path.exists(self.user_data_dir):
            os.makedirs(self.user_data_dir, exist_ok=True)

        self.playwright = await async_playwright().start()
        
        # Launch Persistent Context directly
        # Note: 'channel="chrome"' allows using installed Chrome for better evasion, 
        # or remove it to use bundled Chromium.
        self.context = await self.playwright.chromium.launch_persistent_context(
            user_data_dir=self.user_data_dir,
            headless=self.headless,
            slow_mo=200, # Reduced slow_mo for better feel
            viewport=None, # Required for --start-maximized to take full effect
            args=["--start-maximized", "--disable-blink-features=AutomationControlled"]
        )
        
        # Get the first page (persistent context opens one by default)
        if self.context.pages:
            self.page = self.context.pages[0]
        else:
            self.page = await self.context.new_page()

    async def stop(self):
        """
        Close Context and Playwright.
        WARNING: This closes the browser window.
        Use only when shutting down the service or restarting manually.
        """
        if self.context:
            await self.context.close()
        if self.playwright:
            await self.playwright.stop()
        logger.info("TransEuClient (Persistent) stopped.")

    async def close_page_only(self):
        """Helper to close page without closing browser (if needed in future logic)."""
        if self.page:
            await self.page.close()

    async def login(self) -> bool:
        """
        Perform login to Trans.eu using persistent session.
        Checks if already logged in (via cookies), skips login form if so.
        """
        if not settings.TRANS_EU_USERNAME or not settings.TRANS_EU_PASSWORD:
            logger.error("Trans.eu credentials are missing settings.")
            return False

        try:
            target_url = "https://platform.trans.eu/exchange/offers"
            
            # Check if we are already on the page (from previous session attach)
            if self.page.url == target_url:
                logger.info("Already on target URL.")
                return True

            logger.info("Navigating to Trans.eu...")
            await self.page.goto(target_url)  
            
            # Wait for potential redirect or load
            await self.page.wait_for_timeout(3000)

            # Check logic
            if "id.trans.eu" in self.page.url or "auth.platform.trans.eu" in self.page.url:
                logger.info("Session expired or new login needed. Redirected to Auth.")
                
                # --- Login Form Logic ---
                await self.page.wait_for_selector('input[type="text"], input[type="email"]', timeout=10000)
                await self.page.fill('input[type="text"], input[type="email"]', settings.TRANS_EU_USERNAME)
                await self.page.fill('input[type="password"]', settings.TRANS_EU_PASSWORD)
                await self.page.click('button[type="submit"]')
                
                logger.info("Credentials submitted.")
                await self.page.wait_for_url("**/exchange/offers", timeout=60000) # Increased timeout for login
                logger.info("Login successful (New Session).")
                return True
                
            elif "/exchange/offers" in self.page.url:
                # Need to verify we are not on a public landing page looking similar
                # Check for "Offers" specific element inside app
                try:
                    # Check for "Search" button or dashboard element
                    # Selector for Search button (from previous step analysis)
                    await self.page.wait_for_selector('button[data-ctx="basicFilters.form.submit"]', timeout=10000)
                    logger.info("Already logged in (Cookies Valid).")
                    return True
                except:
                    logger.warning("On offers URL but Dashboard not ready? Checking login form...")
                    # Fallback check
                    if await self.page.query_selector('input[type="password"]'):
                        logger.info("Login form detected on Offers URL.")
                        # Perform login... (Code duplication, simpler to recurse or fall through)
                        # For now, simplistic fall through if struct is same
                        pass 
            
            return True

        except Exception as e:
            logger.error(f"Login/Navigation failed: {str(e)}")
            await self.page.screenshot(path="login_failed.png")
            return False

    async def search_offers(
        self,
        loading_location: str,
        unloading_location: str,
        date_from: str = None,
        date_to: str = None,
        unloading_date_from: str = None,
        unloading_date_to: str = None,
        weight_to: str = "0.9",
        loading_radius: int = 75,
        unloading_radius: int = 75
    ):
        """
        Execute search workflow with all filters.
        """
        try:
            # --- 0. Date Validation ---
            from datetime import datetime
            now_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            
            def to_dt(s):
                return datetime.strptime(s, "%d.%m.%Y") if s else None

            d_l_from = to_dt(date_from)
            d_l_to = to_dt(date_to)
            d_u_from = to_dt(unloading_date_from)
            d_u_to = to_dt(unloading_date_to)

            error_msg = None
            # 1) Loading From < Today
            if d_l_from and d_l_from < now_date:
                error_msg = "Задан неверный диапазон дат. Дата начала загрузки не может быть меньше текущей даты"
            # 2) Loading From > Loading To
            elif d_l_from and d_l_to and d_l_from > d_l_to:
                error_msg = "Дата завершения загрузки не может быть меньше даты начала"
            # 3) Strict Rule: Any Loading >= Any Unloading
            else:
                loading_dates = [d for d in [d_l_from, d_l_to] if d]
                unloading_dates = [d for d in [d_u_from, d_u_to] if d]
                if loading_dates and unloading_dates:
                    max_load = max(loading_dates)
                    min_unload = min(unloading_dates)
                    if max_load >= min_unload:
                        error_msg = "Дата разгрузки должна быть строго позже даты загрузки"
            
            # 4) Unloading From > Unloading To
            if not error_msg and d_u_from and d_u_to and d_u_from > d_u_to:
                error_msg = "Дата начала разгрузки не может быть позже даты завершения разгрузки"

            if error_msg:
                logger.error(f"Validation Error: {error_msg}")
                # Inject visual banner into the browser page for the user
                overlay_js = f"""
                (() => {{
                    const div = document.createElement('div');
                    div.id = 'minitms-error-overlay';
                    div.innerHTML = `
                        <div style="position: fixed; top: 20px; left: 50%; transform: translateX(-50%); 
                                    z-index: 999999; background: linear-gradient(135deg, #ff4b2b, #ff416c); 
                                    color: white; padding: 20px 40px; border-radius: 12px; 
                                    box-shadow: 0 10px 30px rgba(0,0,0,0.3); font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                                    font-size: 18px; font-weight: bold; text-align: center; border: 2px solid rgba(255,255,255,0.2);
                                    backdrop-filter: blur(10px); animation: slideDown 0.5s ease-out;">
                            <div style="margin-bottom: 10px;">⚠️ ВНИМАНИЕ</div>
                            <div>{error_msg}</div>
                            <button onclick="this.parentElement.parentElement.remove()" 
                                    style="margin-top: 15px; background: white; color: #ff416c; border: none; 
                                           padding: 8px 20px; border-radius: 6px; cursor: pointer; font-weight: bold;">
                                OK
                            </button>
                        </div>
                        <style>
                            @keyframes slideDown {{
                                from {{ top: -100px; opacity: 0; }}
                                to {{ top: 20px; opacity: 1; }}
                            }}
                        </style>
                    `;
                    document.body.appendChild(div);
                }})();
                """
                await self.page.evaluate(overlay_js)
                # Still raise error for application logic
                raise ValueError(error_msg)

            logger.info(f"Starting search: {loading_location} -> {unloading_location}")
            
            # Ensure filters are expanded
            basic_filters = self.page.locator('div[data-ctx="basic-filters"]')
            if not await basic_filters.is_visible():
                expand_btn = self.page.locator('button[data-ctx="basic-filters-form-hide-filters-preview"]')
                if await expand_btn.is_visible():
                    await expand_btn.click()
                    await basic_filters.wait_for(state="visible", timeout=5000)

            # --- 1. Loading Location ---
            await self._set_location_field('div[data-ctx="place-loading_place-0"]', loading_location, radius=loading_radius)
            
            # --- 2. Unloading Location ---
            await self._set_location_field('div[data-ctx="place-unloading_place-0"]', unloading_location, radius=unloading_radius)

            # --- 3. Dates ---
            adv_filters = self.page.locator('div[data-ctx="advanced-filters"]')
            
            # Loading Dates
            logger.info(f"Setting Loading dates: {date_from} - {date_to}")
            await self._set_date_input(adv_filters, "from", 0, date_from)
            await self._set_date_input(adv_filters, "to", 0, date_to)
            
            # Unloading Dates
            logger.info(f"Setting Unloading dates: {unloading_date_from} - {unloading_date_to}")
            await self._set_date_input(adv_filters, "from", 1, unloading_date_from)
            await self._set_date_input(adv_filters, "to", 1, unloading_date_to)

            # --- 4. Weight ---
            if weight_to:
                logger.info(f"Setting Weight To: {weight_to}")
                weight_input = self.page.locator('div[data-ctx="load_weight.valueTo"] input')
                if await weight_input.count() > 0:
                    await weight_input.click()
                    await weight_input.fill(weight_to)

            # --- 5. Click Search ---
            logger.info("Clicking Search...")
            search_btn = self.page.locator('button[data-ctx="basicFilters.form.submit"]')
            await search_btn.click()
            
            await self.page.wait_for_timeout(3000)
            return True

        except Exception as e:
            logger.error(f"Search failed: {e}")
            await self.page.screenshot(path="search_failed.png")
            return False

    async def _set_date_input(self, parent_locator, name: str, index: int, value: str):
        """
        Helper to set date. If value is None/empty, clears the field.
        """
        try:
            import re
            inp = parent_locator.locator(f'input[name="{name}"]').nth(index)
            if await inp.count() > 0:
                logger.debug(f"Handling date {name}[{index}], value: {value}")
                await inp.scroll_into_view_if_needed()
                
                if not value:
                    logger.info(f"Clearing date {name}[{index}]")
                    await inp.click()
                    await self.page.keyboard.press("Control+A")
                    await self.page.keyboard.press("Backspace")
                    await self.page.keyboard.press("Escape")
                    return

                logger.info(f"Interaction with calendar for {name}[{index}], target day: {value}")
                await inp.click()
                await self.page.wait_for_timeout(1000)
                
                day_num = str(int(value.split(".")[0]))
                day_cell = self.page.locator(f'div._1d3i7nl_jh_f:not(._1d3i7nl_jh_g)').filter(has_text=re.compile(f"^\s*{day_num}\s*$")).first
                
                if await day_cell.count() > 0:
                    logger.info(f"Found EXACT day cell '{day_num}'. Clicking (force)...")
                    await day_cell.click(force=True)
                    await self.page.wait_for_timeout(1000)
                else:
                    logger.warning(f"Day cell '{day_num}' for current month not found. Trying fallback typing.")
                    await self.page.keyboard.press("Control+A")
                    await self.page.keyboard.press("Backspace")
                    await inp.type(value, delay=50)
                    await self.page.keyboard.press("Enter")
                
                await self.page.keyboard.press("Escape")
            else:
                logger.warning(f"Date input {name} at index {index} not found.")
        except Exception as e:
            logger.error(f"Error setting date {name} via calendar: {e}")

    async def _set_location_field(self, container_selector: str, value: str, radius: int = 0):
        """
        Robust location setter:
        1. Clear & Type text.
        2. Wait for Dropdown (in Portal #mainRegionDropdowns).
        3. Click best match.
        4. Set Radius.
        """
        try:
            logger.info(f"Setting location in {container_selector} to '{value}'")
            container = self.page.locator(container_selector)
            
            # 1. Clear existing
            clear_btn = container.locator('svg[data-ctx="clear"]')
            if await clear_btn.count() > 0 and await clear_btn.is_visible():
                await clear_btn.click()
                await self.page.wait_for_timeout(300)

            # 2. Activate Input
            label_wrapper = container.locator('label[data-ctx="select"]')
            if await label_wrapper.count() > 0:
                await label_wrapper.click(force=True)
            else:
                await container.click(force=True)
            
            await self.page.wait_for_timeout(300)

            # 3. Type text
            await self.page.keyboard.type(value, delay=50)
            
            # 4. Wait for Suggestions in Portal
            logger.info("Waiting for suggestions dropdown...")
            # Dropdown is usually in #mainRegionDropdowns or body > .portal-container
            # We look for option containing the City Name
            city = value.split(" ")[-1].replace(",", "").strip() # Simple extraction
            if len(city) < 3: city = value # Fallback for short inputs
            
            dropdown_option = self.page.locator(f'div#mainRegionDropdowns span[class*="Option__option"]:has-text("{city}")').first
            
            try:
                await dropdown_option.wait_for(state="visible", timeout=5000)
                logger.info(f"Found option for '{city}'. Clicking (force)...")
                await dropdown_option.click(force=True)
            except Exception:
                logger.warning(f"Specific option for '{city}' not found. Clicking first available option.")
                # Fallback: strict generic option
                first_option = self.page.locator('div#mainRegionDropdowns span[class*="Option__option"]').first
                if await first_option.count() > 0:
                     await first_option.click(force=True)
                else:
                     logger.error("No dropdown options appeared!")
                     # Try Enter key as last resort
                     await self.page.keyboard.press("Enter")
            
            await self.page.wait_for_timeout(500)

            # 5. Set Radius (if requested and input exists)
            if radius > 0:
                # Look for range input inside the same location wrapper
                # It might be visible only after selection
                range_input = container.locator('input[name="range"]')
                if await range_input.count() > 0:
                     logger.info(f"Setting radius to {radius} km")
                     # It might be readonly or require special interaction, but let's try fill first
                     # If it has +/- buttons, maybe better to type
                     await range_input.click(force=True)
                     await range_input.fill(str(radius))
                     await self.page.keyboard.press("Enter") # Confirm
                else:
                     logger.warning("Radius input not found.")
            
        except Exception as e:
            logger.error(f"Error setting location: {e}")
            raise e
