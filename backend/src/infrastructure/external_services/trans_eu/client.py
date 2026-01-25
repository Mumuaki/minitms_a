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
        length_to: str = None,
        loading_radius: int = 75,
        unloading_radius: int = 75
    ):
        """
        Execute search workflow with all filters.
        """
        try:
            # --- 0. Date Validation (Strict) ---
            from datetime import datetime
            
            def parse_dt(d_str):
                if not d_str: return None
                try:
                    return datetime.strptime(d_str, "%d.%m.%Y")
                except ValueError:
                    logger.error(f"Invalid date format: {d_str}")
                    return None

            ld_from = parse_dt(date_from)
            ld_to = parse_dt(date_to)
            ud_from = parse_dt(unloading_date_from)
            ud_to = parse_dt(unloading_date_to)

            # 1. Check Range (From <= To)
            if ld_from and ld_to and ld_from > ld_to:
                raise ValueError(f"Loading Date error: 'From' ({date_from}) cannot be later than 'To' ({date_to})")
            if ud_from and ud_to and ud_from > ud_to:
                raise ValueError(f"Unloading Date error: 'From' ({unloading_date_from}) cannot be later than 'To' ({unloading_date_to})")

            # 2. Check Logic (Unload >= Load)
            # Unloading To (arrival) cannot be before Loading From (departure)
            if ld_from and ud_to and ud_to < ld_from:
                raise ValueError(f"Logical error: Unloading To ({unloading_date_to}) is earlier than Loading From ({date_from})")
            
            # Warn if Unload From < Load From
            if ld_from and ud_from and ud_from < ld_from:
                 logger.warning(f"Note: Unloading From ({unloading_date_from}) is earlier than Loading From ({date_from}). This might be invalid.")

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
            if d_l_from and d_l_from < now_date:
                error_msg = "Задан неверный диапазон дат. Дата начала загрузки не может быть меньше текущей даты"
            elif d_l_from and d_l_to and d_l_from > d_l_to:
                error_msg = "Дата завершения загрузки не может быть меньше даты начала"
            # Strict Rule removed to be more flexible, Trans.eu validates it anyway
            
            if error_msg:
                logger.error(f"Validation Error: {error_msg}")
                raise ValueError(error_msg)

            logger.info("Initializing search workflow...")

            # --- Clear Filters (Очистка кеша/предыдущих значений) ---
            try:
                # Try multiple selectors for Clear button
                clear_selectors = [
                    'button[data-ctx="basicFilters.form.clear"]',
                    'button:has-text("Clear filters")',
                    'button:has-text("Clear all")',
                    'button:has-text("Очистить фильтры")',
                    'button[data-ctx="clear-all"]'
                ]
                for sel in clear_selectors:
                    btn = self.page.locator(sel).first
                    if await btn.is_visible(timeout=500):
                        logger.info(f"Clearing filters using: {sel}")
                        await btn.click()
                        await self.page.wait_for_timeout(1000)
                        break
            except Exception as e:
                logger.warning(f"Could not clear filters (ignorable): {e}")

            logger.info(f"Starting search: {loading_location} -> {unloading_location}")
            
            # --- Раскрытие фильтров (EXPAND FILTERS) ---
            expand_button_selectors = [
                'button:has-text("EXPAND FILTERS")',
                'button:has-text("MORE FILTERS")',
                'button:has-text("Expand filters")',
                'button:has-text("More filters")',
                'button[data-ctx="basic-filters-form-hide-filters-preview"]',
                'button[data-ctx*="filter"]'
            ]
            
            expanded = False
            for selector in expand_button_selectors:
                try:
                    expand_btn = self.page.locator(selector).first
                    if await expand_btn.is_visible(timeout=1000):
                        logger.info(f"Expanding filters using: {selector}")
                        await expand_btn.click()
                        await self.page.wait_for_timeout(1000)
                        expanded = True
                        break
                except Exception:
                    continue
            
            if not expanded:
                # Fallback: check if already expanded (basic-filters visible)
                if await self.page.locator('div[data-ctx="basic-filters"]').is_visible():
                    logger.info("Filters appear to be already expanded.")
                else:
                    logger.warning("Could not find Expand Filters button, trying to proceed anyway.")

            # --- 1. Loading Location ---
            # Передаем радиус +75 км (или из аргумента)
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
                # Try standard selector
                weight_input = self.page.locator('div[data-ctx="load_weight.valueTo"] input')
                if await weight_input.count() > 0:
                    await weight_input.click()
                    await weight_input.fill(weight_to)
                else:
                    logger.warning("Weight input not found by data-ctx, check DOM.")

            # --- 5. Length (LDM) ---
            if length_to:
                logger.info(f"Setting Length (LDM) To: {length_to}")
                length_set = False
                
                # Labels to search for (Specific only, to avoid Route Length collision)
                labels = ["Длина (погрузочные метры)", "Погрузочные метры", "LDM", "Loading meters", "Długość ładunkowa", "Load meters"]
                
                # Contexts to search in: first advanced filters, then page root
                contexts = [adv_filters, self.page]
                
                for context in contexts:
                    if length_set: break
                    
                    for label in labels:
                        try:
                            # Search for label
                            # Strategy: Find label, get parent, find 2nd input (To)
                            # Or if label is 'for', find input by id
                            
                            # 1. Label contains text -> Parent -> Inputs
                            label_el = context.locator(f"label:has-text('{label}')").first
                            if await label_el.count() > 0 and await label_el.is_visible():
                                # Try to find inputs in same container
                                container = label_el.locator("..") # Parent
                                inputs = container.locator("input")
                                
                                # Sometimes parent is deeper, go up one more level
                                if await inputs.count() < 2:
                                    container = container.locator("..")
                                    inputs = container.locator("input")
                                
                                if await inputs.count() >= 2:
                                    target_input = inputs.nth(1)
                                    if await target_input.is_visible():
                                        logger.info(f"Found input for '{label}' in {context}")
                                        await target_input.click()
                                        # Clear default value (13.6)
                                        await self.page.keyboard.press("Control+A")
                                        await self.page.keyboard.press("Backspace")
                                        await self.page.wait_for_timeout(100)
                                        
                                        # Type value
                                        val_str = str(length_to)
                                        await target_input.fill(val_str)
                                        await target_input.press("Tab") # Trigger blur/change
                                        await self.page.wait_for_timeout(500) # Wait for JS validation
                                        
                                        # Verify
                                        current_val = await target_input.input_value()
                                        # Normalize both to compare (handle 2.50 vs 2.5)
                                        if current_val == val_str:
                                            logger.info(f"Set length via label '{label}' SUCCESS: {current_val}")
                                            length_set = True
                                            break
                                        else:
                                            logger.warning(f"Value mismatch after input. Set: {val_str}, Got: {current_val}")
                                            # Try with comma if dot failed
                                            if "." in val_str:
                                                val_comma = val_str.replace(".", ",")
                                                logger.info(f"Retrying with comma: {val_comma}")
                                                await target_input.click()
                                                await self.page.keyboard.press("Control+A")
                                                await self.page.keyboard.press("Backspace")
                                                await target_input.fill(val_comma)
                                                await target_input.press("Tab")
                                                await self.page.wait_for_timeout(500)
                                                current_val = await target_input.input_value()
                                                if current_val == val_comma:
                                                    logger.info(f"Set length via label '{label}' SUCCESS (comma): {current_val}")
                                                    length_set = True
                                                    break
                                            
                                            logger.warning(f"Failed to set length even with comma. Final value: {current_val}")
                        except Exception as e:
                            # logger.debug(f"Error checking label {label}: {e}")
                            pass

                if not length_set:
                    # Fallback to data-ctx if labels failed
                    ldm_ctxs = ["load_ldm.valueTo", "load_meter.valueTo", "load_length.valueTo"]
                    for ctx in ldm_ctxs:
                        inp = self.page.locator(f'div[data-ctx="{ctx}"] input').first
                        if await inp.is_visible():
                            await inp.click()
                            await self.page.keyboard.press("Control+A")
                            await self.page.keyboard.press("Backspace")
                            await inp.fill(str(length_to))
                            length_set = True
                            break

                if not length_set:
                    logger.warning("Length/LDM input not found.")

            # --- 6. Click Search ---
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
        Sets date securely using calendar navigation and ISO ID selectors.
        Value must be DD.MM.YYYY
        """
        try:
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

                logger.info(f"Setting date {name}[{index}]: {value}")
                
                # Parse target
                try:
                    target_day, target_month, target_year = map(int, value.split('.'))
                    target_iso = f"{target_year}-{target_month:02d}-{target_day:02d}"
                except ValueError:
                    logger.error(f"Invalid date format: {value}. Expected DD.MM.YYYY")
                    return

                # Open calendar
                await inp.click()
                
                # Wait for calendar header
                header_btn = self.page.locator('button[data-ctx="switch-mode"]')
                try:
                    await header_btn.wait_for(state="visible", timeout=3000)
                except:
                    logger.warning("Calendar header not found. Trying force click again.")
                    await inp.click(force=True)
                    await header_btn.wait_for(state="visible", timeout=3000)

                # Month Navigation Loop
                months_map = {
                    "январь": 1, "февраль": 2, "март": 3, "апрель": 4, "май": 5, "июнь": 6,
                    "июль": 7, "август": 8, "сентябрь": 9, "октябрь": 10, "ноябрь": 11, "декабрь": 12,
                    "january": 1, "february": 2, "march": 3, "april": 4, "may": 5, "june": 6,
                    "july": 7, "august": 8, "september": 9, "october": 10, "november": 11, "december": 12 
                }

                for _ in range(24): # Max 2 years
                    header_text = await header_btn.text_content()
                    header_text = header_text.lower().strip()
                    # Expect "Month Year" e.g. "январь 2026"
                    parts = header_text.split()
                    if len(parts) >= 2:
                        current_month_str = parts[0]
                        current_year_str = parts[-1]
                        current_month = months_map.get(current_month_str)
                        current_year = int(current_year_str) if current_year_str.isdigit() else 0
                        
                        if current_month is None or current_year == 0:
                            logger.warning(f"Could not parse calendar header: {header_text}")
                            break
                        
                        # Check match
                        if current_year == target_year and current_month == target_month:
                            break
                        
                        # Navigate
                        next_ok = (target_year > current_year) or (target_year == current_year and target_month > current_month)
                        nav_btn_sel = 'button[data-ctx="switch-next-page"]' if next_ok else 'button[data-ctx="switch-prev-page"]'
                        
                        await self.page.locator(nav_btn_sel).click()
                        await self.page.wait_for_timeout(200) # Wait for animation
                    else:
                        break

                # Pick Day by ID (most reliable)
                day_wrapper = self.page.locator(f'div[data-ctx-id="{target_iso}-wrapper"]')
                if await day_wrapper.count() > 0:
                    logger.info(f"Clicking day wrapper: {target_iso}")
                    await day_wrapper.click()
                else:
                    logger.warning(f"Day wrapper {target_iso} not found. Trying fuzzy search by text '{target_day}'.")
                    # Fallback (risky, might pick neighbor month)
                    # We try to ensure it's not grayed out (._1d3i7nl_jh_g)
                    fallback_day = self.page.locator(f'div._1d3i7nl_jh_e:has-text("{target_day}")')
                    # Find parent wrapper without 'g' class
                    valid_day = self.page.locator(f'div[data-ctx="option-wrapper"]:not([class*="_1d3i7nl_jh_g"]) div._1d3i7nl_jh_e') \
                                         .filter(has_text=f"^{target_day}$").first
                    
                    if await valid_day.count() > 0:
                        await valid_day.click()
                    else:
                        logger.error("Could not find day cell.")
                
                # Close (usually auto-closes)
                await self.page.wait_for_timeout(500)
                await self.page.keyboard.press("Escape")

            else:
                logger.warning(f"Date input {name} at index {index} not found.")
        except Exception as e:
            logger.error(f"Error setting date {name} via calendar: {e}")

    async def _set_location_field(self, container_selector: str, value: str, radius: int = 0):
        """
        Refined location setter following strict 5-step rule:
        1) {ISO}, {Index}, {City} (EN)
        2) {ISO}, {City} (EN)
        3) {City} (EN)
        --- If modal doesn't appear ---
        4) {City} (RU)
        5) {ISO}, {City} (RU)
        
        Requires modal window presence for success.
        """
        try:
            logger.info(f"Setting location in {container_selector}. Strict sequence for: '{value}'")
            container = self.page.locator(container_selector)
            await container.wait_for(state="visible", timeout=15000)

            # --- Parse Input Components ---
            import re
            parts = [p.strip() for p in value.split(',')]
            
            iso = ""
            zip_code = ""
            city_en = ""
            
            if len(parts) == 1:
                if re.match(r'^[A-Z]{2}$', parts[0]): iso = parts[0]
                elif re.search(r'\d', parts[0]): zip_code = parts[0]
                else: city_en = parts[0]
            elif len(parts) == 2:
                if len(parts[0]) == 2 and parts[0].isupper():
                    iso, city_en = parts[0], parts[1]
                    if re.search(r'\d', city_en): zip_code, city_en = city_en, ""
                else:
                    city_en, iso = parts[0], parts[1]
            elif len(parts) >= 3:
                iso, zip_code, city_en = parts[0], parts[1], parts[2]

            # Translation for Russian attempts (Step 4 & 5)
            # This is a basic map for critical test cases. In production, this would be a service.
            ru_map = {
                "Berlin": "Берлин", "Warszawa": "Варшава", "Prague": "Прага", 
                "Bratislava": "Братислава", "Dietfurt": "Дитфурт", "Šamorín": "Шаморин"
            }
            city_ru = ru_map.get(city_en, city_en)

            # --- Define the 5 attempts strictly ---
            attempts = []
            
            # Step 1: {ISO}, {Index}, {City} (EN)
            if iso and zip_code and city_en:
                attempts.append(f"{iso}, {zip_code}, {city_en}")
            elif iso and zip_code:
                attempts.append(f"{iso}, {zip_code}") # Fallback for AT, 8022
            
            # Step 1.5: {Index} {City} (Common format for DACH)
            if zip_code and city_en:
                attempts.append(f"{zip_code} {city_en}")
                attempts.append(f"{city_en}, {zip_code}")

            # Step 2: {ISO}, {City} (EN)
            if iso and city_en:
                attempts.append(f"{iso}, {city_en}")
            
            # Step 3: {City} (EN)
            if city_en:
                attempts.append(city_en)
            elif zip_code and not attempts: # Fallback if we only have index
                attempts.append(zip_code)

            # --- Fallback to Russian if no modal ---
            # Step 4: {City} (RU)
            if city_ru:
                attempts.append(city_ru)
            
            # Step 5: {ISO}, {City} (RU)
            if iso and city_ru:
                attempts.append(f"{iso}, {city_ru}")
            
            # Deduplicate while preserving order
            seen = set()
            attempts = [x for x in attempts if not (x in seen or seen.add(x))]
            
            modal_selector = 'div#mainRegionDropdowns span[class*="Option__option"]'
            success = False

            for i, attempt in enumerate(attempts):
                if not attempt: continue
                
                step_num = i + 1
                logger.info(f"Location Step {step_num}: Attempting '{attempt}'")
                
                # 1. Clear field
                clear_btn = container.locator('svg[data-ctx="clear"]')
                if await clear_btn.count() > 0 and await clear_btn.is_visible():
                    await clear_btn.click()
                else:
                    await container.click(force=True)
                    await self.page.keyboard.press("Control+A")
                    await self.page.keyboard.press("Backspace")
                await self.page.wait_for_timeout(500)

                # 2. Type
                await self.page.keyboard.type(attempt, delay=100) # Slower typing
                await self.page.wait_for_timeout(1000) # Wait for debounce
                
                # 3. Wait for Modal presence (Confirmation of active field)
                try:
                    await self.page.wait_for_selector(modal_selector, timeout=8000)
                    
                    # 4. Click best match to fixate
                    # We pick the first one as it's usually the most relevant on Trans.eu
                    dropdown_option = self.page.locator(modal_selector).first
                    await dropdown_option.click(force=True)
                    
                    logger.info(f"Success at Step {step_num} with '{attempt}'")
                    success = True
                    break
                except Exception:
                    logger.warning(f"Modal did not appear for step {step_num} ('{attempt}').")
                    continue

            if not success:
                logger.error(f"Failed to set location '{value}' after all steps.")
                raise ValueError(f"Location selection failed for {value}")

            # 5. Set Radius if requested
            if radius > 0:
                await self.page.wait_for_timeout(1000)
                range_input = container.locator('input[name="range"]')
                if await range_input.count() > 0:
                    logger.info(f"Setting radius to {radius} km")
                    await range_input.click(force=True)
                    await range_input.fill(str(radius))
                    await self.page.keyboard.press("Enter")

        except Exception as e:
            logger.error(f"Error in _set_location_field: {e}")
            await self.page.screenshot(path="location_error.png")
            raise e
