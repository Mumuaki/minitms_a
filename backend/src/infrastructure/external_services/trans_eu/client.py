import asyncio
from playwright.async_api import async_playwright, BrowserContext, Page, Playwright
import logging
import os
import json
import time
from backend.src.infrastructure.config.settings import settings

logger = logging.getLogger(__name__)

# Глобальный экземпляр для Singleton (на уровне модуля)
_trans_eu_client_instance = None
_trans_eu_client_lock = None

# #region agent log
_DBG_LOG = "/tmp/debug-73ed43.log"
def _dbg(msg, data=None, hyp=""):
    try:
        entry = {"sessionId":"73ed43","timestamp":int(time.time()*1000),"location":"client.py","message":msg,"hypothesisId":hyp}
        if data is not None: entry["data"] = data
        with open(_DBG_LOG, "a") as f: f.write(json.dumps(entry)+"\n")
    except: pass
# #endregion

class TransEuClient:
    """
    Client for interacting with Trans.eu platform via Browser Automation.
    Uses Persistent Context to maintain session and avoid multiple logins.
    Implemented as a Singleton to prevent multiple browser instances using the same profile.
    """

    @classmethod
    async def get_instance(cls):
        """Returns the shared instance of TransEuClient."""
        global _trans_eu_client_instance, _trans_eu_client_lock
        if _trans_eu_client_lock is None:
            _trans_eu_client_lock = asyncio.Lock()
            
        async with _trans_eu_client_lock:
            if _trans_eu_client_instance is None:
                _trans_eu_client_instance = cls()
            return _trans_eu_client_instance

    def __init__(self):
        self.playwright: Playwright = None
        self.context: BrowserContext = None
        self.page: Page = None
        # ALWAYS run visible so user can watch via noVNC (http://server:6080)
        self.headless = False
        self.user_data_dir = settings.BROWSER_PROFILE_DIR

    async def start(self):
        """
        Initialize Playwright with Persistent Context.
        This keeps cookies/storage in 'browser_profile' folder.
        """
        global _trans_eu_client_lock
        if _trans_eu_client_lock is None:
            _trans_eu_client_lock = asyncio.Lock()
            
        async with _trans_eu_client_lock:
            # If already started and context is valid, do nothing
            if self.context:
                try:
                    # Check if context is still alive
                    if len(self.context.pages) >= 0:
                        logger.info("TransEuClient already started and active.")
                        return
                except Exception:
                    logger.warning("Existing browser context appears dead. Restarting...")
                    self.context = None

            # Ensure DISPLAY is set for Xvfb virtual display (Linux only)
            if os.name != 'nt' and not os.environ.get("DISPLAY"):
                os.environ["DISPLAY"] = ":99"

            logger.info(f"Starting TransEuClient: headless={self.headless}, DISPLAY={os.environ.get('DISPLAY')}, profile={self.user_data_dir}")
            
            if not os.path.exists(self.user_data_dir):
                os.makedirs(self.user_data_dir, exist_ok=True)

            # --- Cleanup stale SingletonLock (protection against crashed browser) ---
            import subprocess
            from pathlib import Path
            
            # Kill any zombie chrome processes first
            try:
                # Use -9 for guaranteed termination in Docker
                subprocess.run(["pkill", "-9", "-f", "chrome"], timeout=5, capture_output=True)
                logger.info("Killed stale chrome processes with SIGKILL.")
            except Exception as kill_err:
                logger.warning(f"Could not kill chrome processes: {kill_err}")

            # Remove the lock files (including symlinks)
            locks_cleaned = False
            for file_name in ["SingletonLock", "SingletonCookie", "SingletonSocket"]:
                file_path = Path(self.user_data_dir) / file_name
                if file_path.exists() or file_path.is_symlink():
                    logger.warning(f"Found stale {file_name} at {file_path}. Cleaning up...")
                    try:
                        # lexists + unlink handles broken symlinks correctly
                        file_path.unlink(missing_ok=True)
                        logger.info(f"{file_name} removed successfully.")
                        locks_cleaned = True
                    except OSError as rm_err:
                        logger.error(f"Failed to remove {file_name}: {rm_err}")
            
            if locks_cleaned:
                # Crucial for Docker/Slow FS: give OS time to sync before Chrome starts
                logger.info("Lock files were cleaned. Waiting 1s for FS sync...")
                time.sleep(1)

            if not self.playwright:
                self.playwright = await async_playwright().start()
            
            # --- Dynamic Chrome Executable Discovery ---
            pw_path = os.environ.get("PLAYWRIGHT_BROWSERS_PATH", "/ms-playwright")
            os.environ["PLAYWRIGHT_BROWSERS_PATH"] = pw_path
            chrome_exe = None
            if os.name != 'nt' and os.path.exists(pw_path):
                import glob
                matches = glob.glob(f"{pw_path}/chromium-*/chrome-linux64/chrome")
                if matches:
                    chrome_exe = matches[0]
                    logger.info(f"Dynamically found Chrome executable at: {chrome_exe}")
            
            launch_args = {
                "user_data_dir": self.user_data_dir,
                "headless": self.headless,
                "slow_mo": 200,
                "viewport": None,
                "args": ["--start-maximized", "--disable-blink-features=AutomationControlled", "--no-sandbox"]
            }
            if chrome_exe:
                launch_args["executable_path"] = chrome_exe
            
            self.context = await self.playwright.chromium.launch_persistent_context(**launch_args)
            
            # Внедряем stealth-скрипт для маскировки под человека и обхода Cloudflare Turnstile
            await self.context.add_init_script("""
                // Маскировка navigator.webdriver
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });

                // Маскировка window.chrome
                window.chrome = {
                    runtime: {},
                    loadTimes: function() {},
                    csi: function() {},
                    app: {}
                };

                // Маскировка navigator.permissions.query
                const originalQuery = window.navigator.permissions.query;
                window.navigator.permissions.query = (parameters) => (
                    parameters.name === 'notifications' ?
                        Promise.resolve({ state: Notification.permission }) :
                        originalQuery(parameters)
                );

                // Маскировка плагинов (navigator.plugins)
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5]
                });

                // Маскировка языков
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['ru-RU', 'ru', 'en-US', 'en']
                });
            """)
        
        if self.context.pages:
            self.page = self.context.pages[0]
        else:
            self.page = await self.context.new_page()
        # #region agent log
        _dbg("start() browser launched OK", {"pages_count": len(self.context.pages)}, "H-B")
        # #endregion

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

    async def _wait_for_cloudflare_if_present(self, timeout_sec: int = 300) -> bool:
        """
        Проверяет наличие капчи Cloudflare Turnstile на странице.
        Если капча обнаружена, приостанавливает выполнение и ждет её решения пользователем.
        """
        cf_indicators = [
            'iframe[src*="challenges.cloudflare.com"]',
            'iframe[src*="challenge-platform"]',
            'iframe[src*="turnstile"]',
            'iframe[src*="cdn-cgi"]',
            'iframe[src*="/challenge"]',
            'iframe._39ie2m9_a_c',
            'iframe[class*="_39ie2m"]',
            'div:has-text("Подтвердите, что вы человек")',
            'div:has-text("Verify you are human")',
            'div:has-text("выполнив задание ниже")',
            '*:has-text("Подтвердите, что вы человек")',
            '*:has-text("Verify you are human")',
            '*:has-text("выполнив задание ниже")'
        ]
        
        async def log_iframes():
            try:
                iframes = await self.page.locator('iframe').all()
                for idx, iframe in enumerate(iframes):
                    src = await iframe.get_attribute('src') or ""
                    id_attr = await iframe.get_attribute('id') or ""
                    class_attr = await iframe.get_attribute('class') or ""
                    logger.info(f"[CF-Debug] Iframe {idx}: id='{id_attr}', class='{class_attr}', src='{src}'")
            except Exception as e:
                logger.warning(f"[CF-Debug] Failed to list iframes: {e}")

        # Отладочный листинг фреймов
        await log_iframes()
            
        detected = False
        for indicator in cf_indicators:
            try:
                el = self.page.locator(indicator).first
                if await el.count() > 0 and await el.is_visible():
                    detected = True
                    logger.warning(f"Cloudflare Turnstile detected via indicator: '{indicator}'")
                    break
            except Exception:
                pass
                
        if not detected:
            logger.info("Cloudflare Turnstile not detected by current indicators.")
            return False
            
        logger.warning(f"!!! CLOUDFLARE CAPTCHA DETECTED !!!")
        logger.warning(f"Please open noVNC at http://89.167.70.67:6080 (or localhost:6080 via start.ps1) and solve the captcha.")
        
        # Обновляем статус в Celery и отправляем уведомление
        try:
            from celery import current_task
            from backend.src.infrastructure.messaging.celery_app import celery_app
            if current_task:
                current_task.update_state(state='WAITING_CAPTCHA')
                celery_app.send_task(
                    "backend.src.application.tasks.notification_tasks.send_telegram_alert", 
                    kwargs={"message": "Cloudflare CAPTCHA detected. Please solve it via noVNC: http://89.167.70.67:6080"}
                )
        except Exception as e:
            logger.warning(f"Failed to update Celery state or send alert: {e}")

        try:
            await self.page.screenshot(path="/tmp/cloudflare_detected.png")
        except Exception:
            pass
            
        start_time = time.time()
        consecutive_resolves = 0
        required_resolves = 3  # Нужно 3 успешных проверки подряд с интервалом, чтобы подтвердить решение
        
        while time.time() - start_time < timeout_sec:
            # Логируем фреймы на каждой итерации для отладки
            await log_iframes()
            
            still_visible = False
            for indicator in cf_indicators:
                try:
                    el = self.page.locator(indicator).first
                    if await el.count() > 0 and await el.is_visible():
                        still_visible = True
                        break
                except Exception:
                    pass
            
            if not still_visible:
                consecutive_resolves += 1
                if consecutive_resolves >= required_resolves:
                    logger.info("Cloudflare Turnstile captcha resolved or disappeared! Resuming...")
                    return True
                logger.info(f"Captcha not detected (resolve check {consecutive_resolves}/{required_resolves}). Waiting...")
            else:
                consecutive_resolves = 0
                logger.info("Waiting for Cloudflare Turnstile to be solved by user...")
                
            await self.page.wait_for_timeout(3000)
            
        logger.error(f"Cloudflare Turnstile was not solved within {timeout_sec} seconds. Aborting.")
        return False

    async def login(self) -> bool:
        """
        Выполняет вход в Trans.eu согласно spec_trans_eu.md п. 2.1.

        Шаг 0: Проверка состояния сессии по текущему URL.
        Шаг 1: goto https://platform.trans.eu (автоматический редирект на auth.).
        Шаг 2: Заполнить [aria-label="TransID"] и [aria-label="Пароль"] из .env.
        Шаг 3: Нажать button[type="submit"] (кнопка «Вход»).
        Шаг 4: Дождаться редиректа на /trans-info (LOGIN_FAILED если не произошло).
        Шаг 5: Нажать «Поиск грузов» в левом меню → дождаться /exchange/offers.
        """
        # #region agent log
        _dbg("login() called", {"username": settings.TRANS_EU_USERNAME[:3]+"***" if settings.TRANS_EU_USERNAME else "(empty)", "has_password": bool(settings.TRANS_EU_PASSWORD)}, "H-E")
        # #endregion
        if not settings.TRANS_EU_USERNAME or not settings.TRANS_EU_PASSWORD:
            logger.error("Trans.eu credentials are missing settings.")
            # #region agent log
            _dbg("login() ABORT: credentials missing", {}, "H-E")
            # #endregion
            return False

        try:
            current_url = self.page.url
            logger.info(f"login() — Шаг 0: проверка состояния. Текущий URL: {current_url}")
            # #region agent log
            _dbg("login() step0 check", {"current_url": current_url}, "H-C")
            # #endregion

            # Если мы запускаемся в первый раз и URL пустой (about:blank), сначала переходим на стартовый URL,
            # чтобы браузер применил сохраненные куки и мы узнали реальный статус авторизации.
            if current_url == "about:blank" or not current_url:
                START_URL = "https://platform.trans.eu"
                logger.info(f"Начальный URL пуст. Выполняем переход на {START_URL} для инициализации сессии...")
                await self.page.goto(START_URL, timeout=60000)
                await self.page.wait_for_timeout(3000)
                await self._wait_for_cloudflare_if_present()
                current_url = self.page.url
                logger.info(f"Текущий URL после перехода на стартовую страницу: {current_url}")

            # Если мы попали на страницу выхода /logout, значит сессия сброшена — очищаем куки
            if "/logout" in current_url:
                START_URL = "https://platform.trans.eu"
                logger.info("Текущий URL указывает на выход из системы (/logout). Очищаем куки контекста...")
                await self.context.clear_cookies()
                logger.info("Куки очищены. Повторно переходим на стартовую страницу...")
                await self.page.goto(START_URL, timeout=60000)
                await self.page.wait_for_timeout(3000)
                await self._wait_for_cloudflare_if_present()
                current_url = self.page.url
                logger.info(f"Текущий URL после повторного перехода на стартовую страницу: {current_url}")

            # --- Шаг 0: Проверка состояния сессии ---

            # Состояние 1: уже на нужной странице
            if "platform.trans.eu/exchange/offers" in current_url:
                logger.info("Шаг 0: Уже на странице поиска грузов. Авторизация не требуется.")
                return True

            # Состояние 2: авторизован, страница /trans-info
            if "platform.trans.eu/trans-info" in current_url:
                logger.info("Шаг 0: На /trans-info — переходим через меню «Поиск грузов».")
                return await self._navigate_to_offers_via_menu()

            # Состояние 3: авторизован, другая страница platform.trans.eu (не auth., не login и не logout)
            if "platform.trans.eu" in current_url and "auth.platform.trans.eu" not in current_url and "/login" not in current_url and "/logout" not in current_url:
                logger.info("Шаг 0: Авторизован, другая страница. Переходим через меню «Поиск грузов».")
                return await self._navigate_to_offers_via_menu()

            # Состояние 4: не авторизован — выполнить полную процедуру
            logger.info("Шаг 0: Не авторизован. Запускаем процедуру логина.")

            # Если мы еще не на странице авторизации, перейдем на START_URL
            if "auth.platform.trans.eu" not in current_url and "/login" not in current_url:
                START_URL = "https://platform.trans.eu"
                logger.info(f"Шаг 1: goto {START_URL}")
                # #region agent log
                _dbg("login() step1 goto START_URL", {"url": START_URL}, "H-C")
                # #endregion
                await self.page.goto(START_URL, timeout=60000)
                await self.page.wait_for_timeout(3000)
                logger.info(f"После goto START_URL, текущий URL: {self.page.url}")

            # --- Шаг 2: Ожидание полей и заполнение ---
            logger.info("Шаг 2: Ожидание поля ввода логина")
            # #region agent log
            _dbg("login() step2 waiting for login field", {"url": self.page.url}, "H-D")
            # #endregion
            
            login_selector = 'input[name="login"]'
            password_selector = 'input[name="password"]'
            
            try:
                await self.page.wait_for_selector(login_selector, timeout=15000)
            except Exception:
                logger.warning("Селектор input[name='login'] не найден, используем фолбэк [aria-label='TransID']")
                login_selector = '[aria-label="TransID"]'
                await self.page.wait_for_selector(login_selector, timeout=15000)
                
            try:
                await self.page.wait_for_selector(password_selector, timeout=5000)
            except Exception:
                logger.warning("Селектор input[name='password'] не найден, используем фолбэк [aria-label='Пароль']")
                password_selector = '[aria-label="Пароль"]'
                
            logger.info("Шаг 2: Заполняю TransID и Пароль из .env")
            await self.page.fill(login_selector, settings.TRANS_EU_USERNAME)
            await self.page.fill(password_selector, settings.TRANS_EU_PASSWORD)
            await self.page.screenshot(path="/tmp/debug_before_submit.png")

            # --- Шаг 3: Нажать кнопку «Вход» ---
            logger.info("Шаг 3: Нажимаю button[type='submit'] (кнопка «Вход»)")
            # #region agent log
            _dbg("login() step3 clicking submit", {}, "H-D")
            # #endregion
            await self.page.click('button[type="submit"]')

            # --- Шаг 4: Ожидание редиректа на /trans-info ---
            logger.info("Шаг 4: Ожидание редиректа на /trans-info (timeout=30s)")
            # #region agent log
            _dbg("login() step4 waiting for trans-info", {}, "H-D")
            # #endregion
            try:
                await self.page.wait_for_url("**/trans-info**", timeout=30000)
                logger.info(f"Шаг 4: Успешный вход. Текущий URL: {self.page.url}")
                # #region agent log
                _dbg("login() step4 trans-info reached", {"url": self.page.url}, "H-D")
                # #endregion
            except Exception as wait_err:
                if await self._wait_for_cloudflare_if_present():
                    await self.page.wait_for_url("**/trans-info**", timeout=30000)
                else:
                    logger.error(f"LOGIN_FAILED: Редирект на /trans-info не произошёл. URL: {self.page.url}")
                    # #region agent log
                    _dbg("login() LOGIN_FAILED step4", {"error": str(wait_err), "url": self.page.url}, "H-D")
                    # #endregion
                    await self.page.screenshot(path="/tmp/debug_login_failed.png")
                    return False

            # --- Шаг 5: Нажать «Поиск грузов» в левом меню ---
            return await self._navigate_to_offers_via_menu()

        except Exception as e:
            logger.error(f"Login/Navigation failed: {str(e)}")
            # #region agent log
            _dbg("login() EXCEPTION", {"error": str(e), "url": self.page.url if self.page else "no-page"}, "H-C,H-D")
            # #endregion
            try:
                await self.page.screenshot(path="/tmp/debug_login_failed.png")
            except: pass
            return False

    async def _navigate_to_offers_via_menu(self) -> bool:
        """
        Шаг 5 (spec_trans_eu.md п. 2.1):
        Найти ссылку «Поиск грузов» в левом меню и нажать её.
        Ожидает открытия /exchange/offers.
        """
        try:
            await self._wait_for_cloudflare_if_present()
            logger.info("Шаг 5: Ожидание ссылки «Поиск грузов» (a[href*='/exchange/offers'])")
            # #region agent log
            _dbg("_navigate_to_offers_via_menu() waiting for menu link", {"url": self.page.url}, "H-C")
            # #endregion
            await self.page.wait_for_selector('a[href*="/exchange/offers"]', timeout=15000)
            
            # --- Вариант 1: Попытка закрыть модальное окно, если оно перекрывает интерфейс ---
            modal_selectors = [
                'div[data-ctx="modals-region"]',
                'div[class*="_qpnf86_b_d"]',
                'div.qIODY8rrX08nnWOcOFtA'
            ]
            for sel in modal_selectors:
                try:
                    modal = self.page.locator(sel).first
                    if await modal.is_visible(timeout=500):
                        logger.info(f"Обнаружено модальное окно ({sel}). Пытаемся закрыть его кнопкой Escape...")
                        await self.page.keyboard.press("Escape")
                        await self.page.wait_for_timeout(1000)
                        
                        close_btn = modal.locator('button:has-text("Close"), button:has-text("Закрыть"), button:has-text("Accept"), button:has-text("Принять")').first
                        if await close_btn.is_visible(timeout=500):
                            logger.info("Найдена кнопка закрытия/принятия в модалке. Кликаем...")
                            await close_btn.click()
                            await self.page.wait_for_timeout(1000)
                except Exception as modal_err:
                    logger.debug(f"Ошибка при попытке закрыть модальное окно: {modal_err}")

            # --- Вариант 2: Клик по меню (обычный, а при ошибке перекрытия — с force=True) ---
            logger.info("Шаг 5: Нажимаю ссылку «Поиск грузов»")
            try:
                await self.page.click('a[href*="/exchange/offers"]', timeout=10000)
            except Exception as click_err:
                await self._wait_for_cloudflare_if_present()
                logger.warning(f"Обычный клик не удался ({click_err}). Пробуем клик с force=True...")
                await self.page.click('a[href*="/exchange/offers"]', force=True)
                
            try:
                await self.page.wait_for_url("**/exchange/offers**", timeout=15000)
            except Exception as url_err:
                if await self._wait_for_cloudflare_if_present():
                    logger.info("Trying to click and wait for URL again after solving captcha...")
                    await self.page.click('a[href*="/exchange/offers"]', force=True)
                    await self.page.wait_for_url("**/exchange/offers**", timeout=15000)
                else:
                    raise url_err

            logger.info(f"Шаг 5: Открыта страница поиска. URL: {self.page.url}")
            # #region agent log
            _dbg("_navigate_to_offers_via_menu() success", {"url": self.page.url}, "H-C")
            # #endregion
            return True
        except Exception as e:
            logger.error(f"Шаг 5: Не удалось перейти на /exchange/offers через меню: {e}")
            # #region agent log
            _dbg("_navigate_to_offers_via_menu() FAILED", {"error": str(e), "url": self.page.url}, "H-C")
            # #endregion
            await self.page.screenshot(path="/tmp/debug_menu_navigation_failed.png")
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
            # Check authorization first
            # ПРАВИЛО (STRICT RULE): Сначала надо войти на портал https://platform.trans.eu и авторизоваться.
            # Только после успешной авторизации на портале Trans.eu возможен запуск скрапера.
            if not await self.login():
                raise Exception("User is not authorized on Trans.eu portal.")

            # --- 0. Date Validation (Strict) ---
            from datetime import datetime
            
            def get_next_working_day():
                from datetime import timedelta
                from_date = datetime.now()
                next_day = from_date + timedelta(days=1)
                while next_day.weekday() >= 5:
                    next_day += timedelta(days=1)
                return next_day

            def parse_dt(d_str):
                if not d_str: return None
                try:
                    return datetime.strptime(d_str, "%d.%m.%Y")
                except ValueError:
                    logger.error(f"Invalid date format: {d_str}")
                    return None

            # Apply default dates if not provided according to requirements
            if not date_from:
                date_from = datetime.now().strftime("%d.%m.%Y")
            if not date_to:
                date_to = date_from
            if not unloading_date_from:
                from datetime import timedelta
                ld_to_dt = parse_dt(date_to) or datetime.now()
                unloading_date_from = (ld_to_dt + timedelta(days=1)).strftime("%d.%m.%Y")
            if not unloading_date_to:
                unloading_date_to = unloading_date_from

            ld_from = parse_dt(date_from)
            ld_to = parse_dt(date_to)
            ud_from = parse_dt(unloading_date_from)
            ud_to = parse_dt(unloading_date_to)
            now_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

            # 1. Basic Validity Checks
            if ld_from and ld_from < now_date:
                raise ValueError(f"Loading Date (From) {date_from} cannot be in the past.")
            
            if ld_from and ld_to and ld_from > ld_to:
                raise ValueError(f"Loading Date: From ({date_from}) > To ({date_to})")
                
            if ud_from and ud_to and ud_from > ud_to:
                raise ValueError(f"Unloading Date: From ({unloading_date_from}) > To ({unloading_date_to})")

            # 2. Business Rule: Unloading Dates >= Loading Date (To)
            # "Ни одна дата разгрузки не может быть меньше даты, указанной в правом поле Даты загрузки"
            if ld_to:
                if ud_from and ud_from < ld_to:
                    raise ValueError(f"Business Rule Violation: Unloading From ({unloading_date_from}) must be >= Loading To ({date_to})")
                
                # Check Unloading To as well (if unloading starts later, it obviously ends later, but if from is None...)
                if ud_to and ud_to < ld_to:
                    raise ValueError(f"Business Rule Violation: Unloading To ({unloading_date_to}) must be >= Loading To ({date_to})")

            logger.info("Initializing search workflow...")

            # --- STEP 0: Navigate to the Search page and wait for it to fully load ---
            search_url = "https://platform.trans.eu/exchange/offers"
            logger.info(f"Navigating to search page: {search_url}")
            await self.page.goto(search_url, timeout=60000, wait_until="domcontentloaded")
            # Wait for the submit button to appear in DOM (it may be hidden if filters are collapsed)
            try:
                await self.page.wait_for_selector(
                    'button[data-ctx="basicFilters.form.submit"]', state="attached", timeout=30000
                )
                logger.info("Search page loaded — submit button found in DOM.")
            except Exception as nav_err:
                logger.error(f"Search page did not load properly: {nav_err}")
                raise Exception(f"Trans.eu search page failed to load: {nav_err}")

            await self.page.wait_for_timeout(2000)  # Let React finish rendering

            # --- EXPAND FILTERS (must happen BEFORE filling any fields) ---
            # Check if place-loading_place-0 is already visible (filters already expanded)
            loading_field = self.page.locator('div[data-ctx="place-loading_place-0"] input').first
            already_expanded = False
            try:
                if await loading_field.is_visible(timeout=1000):
                    already_expanded = True
                    logger.info("Filters are already expanded (location field is visible).")
            except Exception:
                pass

            # Шаг 1: Нажать «РАЗВЕРНУТЬ ФИЛЬТРЫ» (EXPAND FILTERS)
            expand_step1_selectors = [
                'button:has-text("РАЗВЕРНУТЬ ФИЛЬТРЫ")',
                'button:has-text("Развернуть фильтры")',
                'button:has-text("EXPAND FILTERS")',
                'button:has-text("Expand filters")',
                'button[data-ctx="basic-filters-form-hide-filters-preview"]',
            ]
            # Шаг 2: Нажать «БОЛЬШЕ ФИЛЬТРОВ» (MORE FILTERS) — отдельный шаг
            more_filters_selectors = [
                'button:has-text("БОЛЬШЕ ФИЛЬТРОВ")',
                'button:has-text("Больше фильтров")',
                'button:has-text("MORE FILTERS")',
                'button:has-text("More filters")',
            ]

            if not already_expanded:
                # Шаг 1: РАЗВЕРНУТЬ ФИЛЬТРЫ
                expanded = False
                for selector in expand_step1_selectors:
                    try:
                        expand_btn = self.page.locator(selector).first
                        if await expand_btn.is_visible(timeout=2000):
                            logger.info(f"Step 1 — Expanding filters using: {selector}")
                            await expand_btn.click(force=True)
                            await self.page.wait_for_timeout(2000)
                            expanded = True
                            break
                    except Exception:
                        continue

                if not expanded:
                    logger.info("Step 1 — Expand Filters button not found — may already be expanded.")

                # Шаг 2: БОЛЬШЕ ФИЛЬТРОВ
                for selector in more_filters_selectors:
                    try:
                        more_btn = self.page.locator(selector).first
                        if await more_btn.is_visible(timeout=2000):
                            logger.info(f"Step 2 — Expanding more filters using: {selector}")
                            await more_btn.click(force=True)
                            await self.page.wait_for_timeout(2000)
                            break
                    except Exception:
                        continue

            # Verify the loading location field is now visible
            try:
                await self.page.wait_for_selector(
                    'div[data-ctx="place-loading_place-0"] input', state="visible", timeout=10000
                )
                logger.info("Loading location field is visible.")
            except Exception as expand_err:
                logger.warning("Loading location field still not visible. Checking for Cloudflare...")
                if await self._wait_for_cloudflare_if_present():
                    logger.info("Retrying expanding filters after solving captcha...")
                    # Step 1 retry: РАЗВЕРНУТЬ ФИЛЬТРЫ
                    for selector in expand_step1_selectors:
                        try:
                            expand_btn = self.page.locator(selector).first
                            if await expand_btn.is_visible(timeout=2000):
                                logger.info(f"Step 1 retry — Expanding filters using: {selector}")
                                await expand_btn.click(force=True)
                                await self.page.wait_for_timeout(2000)
                                break
                        except Exception:
                            continue
                    # Step 2 retry: БОЛЬШЕ ФИЛЬТРОВ
                    for selector in more_filters_selectors:
                        try:
                            more_btn = self.page.locator(selector).first
                            if await more_btn.is_visible(timeout=2000):
                                logger.info(f"Step 2 retry — Expanding more filters using: {selector}")
                                await more_btn.click(force=True)
                                await self.page.wait_for_timeout(2000)
                                break
                        except Exception:
                            continue
                    await self.page.wait_for_selector(
                        'div[data-ctx="place-loading_place-0"] input', state="visible", timeout=15000
                    )
                else:
                    logger.error("Cloudflare Turnstile was not solved. Aborting search.")
                    await self.page.screenshot(path="/tmp/debug_filters_not_expanded.png")
                    raise Exception("Cloudflare Turnstile was not solved. Search aborted.")

            # --- Clear Filters ---
            try:
                clear_selectors = [
                    'button[data-ctx="basicFilters.form.clear"]',
                    'button:has-text("Clear filters")',
                    'button:has-text("Clear all")',
                    'button:has-text("Очистить фильтры")',
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

            # --- 1. Loading Location ---
            await self._set_location_field('div[data-ctx="place-loading_place-0"]', loading_location, radius=loading_radius)

            # --- 2. Unloading Location ---
            if unloading_location and unloading_location.strip():
                await self._set_location_field('div[data-ctx="place-unloading_place-0"]', unloading_location, radius=unloading_radius)
            else:
                logger.info("Unloading location not specified, skipping.")

            # Note: Expand Filters was already done above (STEP 0) to make location fields visible.
            # Date fields should already be visible too.

            # --- 3. Dates ---
            adv_filters = self.page.locator('div[data-ctx="advanced-filters"]')
            
            # Unloading Date To
            logger.info(f"Setting Unloading date to: {unloading_date_to}")
            await self._set_date_input(adv_filters, "to", 1, unloading_date_to)
            
            # Unloading Date From
            logger.info(f"Setting Unloading date from: {unloading_date_from}")
            await self._set_date_input(adv_filters, "from", 1, unloading_date_from)

            # Loading Date To
            logger.info(f"Setting Loading date to: {date_to}")
            await self._set_date_input(adv_filters, "to", 0, date_to)

            # Loading Date From
            logger.info(f"Setting Loading date from: {date_from}")
            await self._set_date_input(adv_filters, "from", 0, date_from)

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

            # --- 5. Length (LDM) — Left field «С» = 4.8 (всегда, по спецификации) ---
            logger.info("Setting LDM From (left field) to default 4.8 per spec")
            ldm_from_set = False
            _ldm_labels = ["Длина (погрузочные метры)", "Погрузочные метры", "LDM", "Loading meters", "Długość ładunkowa", "Load meters"]
            for _ctx in [adv_filters, self.page]:
                if ldm_from_set:
                    break
                for _label in _ldm_labels:
                    try:
                        _label_el = _ctx.locator(f"label:has-text('{_label}')").first
                        if await _label_el.count() > 0 and await _label_el.is_visible():
                            _container = _label_el.locator("..")
                            _inputs = _container.locator("input")
                            if await _inputs.count() < 1:
                                _container = _container.locator("..")
                                _inputs = _container.locator("input")
                            if await _inputs.count() >= 1:
                                _inp = _inputs.nth(0)
                                if await _inp.is_visible():
                                    await _inp.click()
                                    await self.page.keyboard.press("Control+A")
                                    await self.page.keyboard.press("Backspace")
                                    await _inp.fill("4.8")
                                    await _inp.press("Tab")
                                    await self.page.wait_for_timeout(500)
                                    _val = await _inp.input_value()
                                    if "4" in _val:
                                        logger.info(f"LDM From set to 4.8 via label '{_label}': {_val}")
                                        ldm_from_set = True
                                        break
                                    # Повтор с запятой (европейский формат)
                                    await _inp.click()
                                    await self.page.keyboard.press("Control+A")
                                    await self.page.keyboard.press("Backspace")
                                    await _inp.fill("4,8")
                                    await _inp.press("Tab")
                                    await self.page.wait_for_timeout(500)
                                    _val = await _inp.input_value()
                                    if "4" in _val:
                                        logger.info(f"LDM From set to 4,8 via label '{_label}': {_val}")
                                        ldm_from_set = True
                                        break
                    except Exception:
                        pass
            if not ldm_from_set:
                logger.warning("LDM From (left field) input not found — панель 'БОЛЬШЕ ФИЛЬТРОВ' может быть не открыта.")

            # --- 5b. Length (LDM) — Right field «До» (из параметра запроса) ---
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
            
            await self.page.wait_for_timeout(8000)
            
            # Save debug screenshot and HTML dump
            try:
                await self.page.screenshot(path="/tmp/search_results.png")
                html_content = await self.page.content()
                with open("/tmp/search_results.html", "w", encoding="utf-8") as f:
                    f.write(html_content)
                logger.info("Saved search results screenshot to /tmp/search_results.png and HTML to /tmp/search_results.html")
            except Exception as debug_err:
                logger.warning(f"Failed to save debug info: {debug_err}")
            
            # --- 7. Data Extraction (Import) ---
            logger.info("Extracting search results...")
            from backend.src.infrastructure.external_services.trans_eu import parser, mapper
            
            # Execute JS parser
            js_script = parser.get_extraction_script()
            raw_offers = await self.page.evaluate(js_script)
            logger.info(f"Extracted {len(raw_offers)} raw items.")
            
            # Map to Domain
            results = []
            for raw in raw_offers:
                try:
                    mapped = mapper.map_to_cargo(raw)
                    results.append(mapped)
                except Exception as map_err:
                    logger.warning(f"Failed to map item: {map_err}")
            
            logger.info(f"Successfully mapped {len(results)} offers.")
            return results

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
            try:
                await container.wait_for(state="attached", timeout=15000)
                await container.locator('input').first.wait_for(state="visible", timeout=15000)
            except Exception as wait_err:
                logger.warning(f"Location input not visible. Checking for Cloudflare... ({wait_err})")
                if await self._wait_for_cloudflare_if_present():
                    input_el = container.locator('input').first
                    if not await input_el.is_visible():
                        logger.info("Location input is still not visible after solving captcha. Re-expanding filters...")
                        expand_button_selectors = [
                            'button:has-text("РАЗВЕРНУТЬ ФИЛЬТРЫ")',
                            'button:has-text("Развернуть фильтры")',
                            'button:has-text("EXPAND FILTERS")',
                            'button:has-text("MORE FILTERS")',
                            'button:has-text("Expand filters")',
                            'button:has-text("More filters")',
                            'button[data-ctx="basic-filters-form-hide-filters-preview"]',
                        ]
                        for selector in expand_button_selectors:
                            try:
                                expand_btn = self.page.locator(selector).first
                                if await expand_btn.is_visible(timeout=2000):
                                    logger.info(f"Expanding filters using: {selector}")
                                    await expand_btn.click(force=True)
                                    await self.page.wait_for_timeout(2000)
                                    break
                            except Exception:
                                continue
                    await container.wait_for(state="attached", timeout=15000)
                    await container.locator('input').first.wait_for(state="visible", timeout=15000)
                else:
                    logger.error("Cloudflare Turnstile was not solved. Aborting location input.")
                    raise Exception("Cloudflare Turnstile was not solved. Location input aborted.")

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
                    if re.search(r'\d', city_en):
                        match = re.match(r'^([\d\s-]+)\s+(.+)$', city_en.strip())
                        if match:
                            zip_code = match.group(1).strip()
                            city_en = match.group(2).strip()
                        else:
                            zip_code, city_en = city_en, ""
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
            elif iso and not attempts: # Country-only search
                attempts.append(iso)

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
            
            # Find the input element inside container
            input_el = container.locator('input').first

            for i, attempt in enumerate(attempts):
                if not attempt: continue
                
                step_num = i + 1
                logger.info(f"Location Step {step_num}: Attempting '{attempt}'")
                
                # 1. Clear field
                clear_btn = container.locator('svg[data-ctx="clear"]')
                if await clear_btn.count() > 0 and await clear_btn.is_visible():
                    await clear_btn.click()
                else:
                    await input_el.evaluate("el => { el.removeAttribute('readonly'); el.readOnly = false; }")
                    await input_el.click(force=True)
                    await input_el.focus()
                    await self.page.keyboard.press("Control+A")
                    await self.page.keyboard.press("Backspace")
                await self.page.wait_for_timeout(1000)

                # 2. Focus and Type
                await input_el.evaluate("el => { el.removeAttribute('readonly'); el.readOnly = false; }")
                
                label_parent = container.locator('label[data-ctx="select"]').first
                if await label_parent.count() > 0:
                    await label_parent.click(force=True)
                    await self.page.wait_for_timeout(500)
                    
                await input_el.click(force=True)
                await input_el.focus()
                
                await self.page.wait_for_timeout(1000)
                await self.page.keyboard.type(attempt, delay=150)
                await self.page.wait_for_timeout(2000)
                
                # 3. Wait for Modal presence (Confirmation of active field)
                try:
                    await self.page.wait_for_selector(modal_selector, timeout=8000)
                    
                    # 4. Click best match to fixate (pick the one with maximum information / longest text)
                    options_locator = self.page.locator(modal_selector)
                    options_count = await options_locator.count()
                    if options_count == 0:
                        raise Exception("No options in dropdown")
                        
                    best_index = 0
                    longest_len = 0
                    for idx in range(options_count):
                        text = await options_locator.nth(idx).text_content()
                        text_len = len(text.strip()) if text else 0
                        if text_len > longest_len:
                            longest_len = text_len
                            best_index = idx
                            
                    logger.info(f"Selecting option at index {best_index} with text length {longest_len}")
                    dropdown_option = options_locator.nth(best_index)
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
                range_input = container.locator('input[name="range"]').first
                try:
                    if await range_input.count() > 0 and await range_input.is_visible(timeout=1000):
                        logger.info(f"Setting radius to {radius} km")
                        await range_input.click(force=True)
                        await range_input.fill(str(radius))
                        await self.page.keyboard.press("Enter")
                        await self.page.wait_for_timeout(500)
                except Exception as ex:
                    logger.info(f"Radius input not visible or not found ({ex}). Skipping as per instructions.")

        except Exception as e:
            logger.error(f"Error in _set_location_field: {e}")
            await self.page.screenshot(path="location_error.png")
            raise e
