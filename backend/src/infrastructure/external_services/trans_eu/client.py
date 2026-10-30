import asyncio
from playwright.async_api import async_playwright, BrowserContext, Page, Playwright
import logging
import os
import time
from backend.src.infrastructure.config.settings import settings
from backend.src.infrastructure.external_services.trans_eu import search_workflow
from backend.src.infrastructure.external_services.trans_eu import collection

logger = logging.getLogger(__name__)

# Глобальный экземпляр для Singleton (на уровне модуля)
_trans_eu_client_instance = None
_trans_eu_client_lock = None

# Legacy whole-page loading/end/empty markers were removed; the scoped result-list state is now probed by parser.get_result_state_script().
_LOAD_MORE_SELECTORS = (
    'button[data-ctx*="load-more"]',
    'button[data-ctx*="loadMore"]',
    'button:has-text("Показать ещё")',
    'button:has-text("Показать еще")',
    'button:has-text("Загрузить ещё")',
    'button:has-text("Загрузить еще")',
    'button:has-text("Load more")',
    'button:has-text("Załaduj więcej")',
)


# Scroll the *last rendered row* into view. The portal renders results in a
# virtualized container, so window.scrollBy does nothing when the scrollable
# element is an inner div; scrollIntoView on the last row scrolls whichever
# ancestor actually owns the viewport and makes the virtualizer append more rows.
_SCROLL_SCRIPT = """() => {
  const rows = document.querySelectorAll('div[data-ctx="row"]');
  if (!rows.length) {
    window.scrollBy(0, window.innerHeight);
    return;
  }
  // The portal renders rows lazily inside an inner scrollable container
  // (div[data-ctx="LoadsList"]), not the window. Scroll that container to its
  // absolute bottom so the virtualizer renders the remaining rows; scrollIntoView
  // on the last row alone does nothing once that row is already in view.
  let el = rows[rows.length - 1];
  while (el && el !== document.body && el !== document.documentElement
         && el.scrollHeight <= el.clientHeight + 1) {
    el = el.parentElement;
  }
  if (el && el !== document.body && el !== document.documentElement) {
    el.scrollTop = el.scrollHeight;
  } else {
    rows[rows.length - 1].scrollIntoView({ block: 'end' });
    window.scrollTo(0, document.body.scrollHeight);
  }
}"""


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
            # If already started, prove the context is genuinely alive with a real
            # protocol round-trip. Reading self.context.pages is NOT a liveness check:
            # it is a cached property and can succeed after the underlying loop/browser
            # is gone. cookies() forces a round-trip on the current loop; the result is
            # discarded and never logged (session data must stay out of logs).
            if self.context is not None:
                try:
                    _ = await self.context.cookies()
                    logger.info("TransEuClient already started and active.")
                    return
                except Exception:
                    logger.warning("Existing browser context appears dead. Restarting...")
                    # Release owned Playwright resources coherently before relaunch,
                    # while keeping this object and the global lock intact so it remains
                    # the canonical singleton for concurrent get_instance() callers.
                    try:
                        await self.context.close()
                    except Exception:
                        logger.exception("Error closing dead Trans.eu browser context")
                    self.context = None
                    self.page = None
                    if self.playwright is not None:
                        try:
                            await self.playwright.stop()
                        except Exception:
                            logger.exception("Error stopping dead Trans.eu Playwright")
                        self.playwright = None

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
                # await, not time.sleep: blocking the loop here would stall every
                # coroutine sharing it (Playwright callbacks included).
                await asyncio.sleep(1)

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

    async def stop(self):
        """
        Close Context and Playwright.
        WARNING: This closes the browser window.
        Use only when shutting down the service or restarting manually.
        """
        global _trans_eu_client_instance, _trans_eu_client_lock
        if self.context is not None:
            try:
                await self.context.close()
            except Exception:
                logger.exception("Error closing Trans.eu browser context")
        if self.playwright is not None:
            try:
                await self.playwright.stop()
            except Exception:
                logger.exception("Error stopping Trans.eu Playwright")
        self.context = None
        self.page = None
        self.playwright = None
        _trans_eu_client_instance = None
        _trans_eu_client_lock = None
        logger.info("TransEuClient (Persistent) stopped.")

    async def close_page_only(self):
        """Helper to close page without closing browser (if needed in future logic)."""
        if self.page:
            await self.page.close()

    def _alert_operator(self, message: str) -> None:
        """Best-effort operator alert; never raises into the scraping flow."""
        try:
            from backend.src.infrastructure.messaging.celery_app import celery_app

            celery_app.send_task(
                "backend.src.application.tasks.notification_tasks.send_telegram_alert",
                kwargs={"message": message},
            )
        except Exception as exc:
            logger.warning("Operator alert could not be queued (%s)", type(exc).__name__)

    async def session_state(self) -> str:
        """Return 'logged_in' | 'logged_out' | 'unavailable' without logging in.

        A cheap probe for the keepalive task: it never starts a login flow, so an
        absent operator cannot block the scraping queue.

        URL alone is not proof of an authenticated session: the offers route also
        renders while logged out, so a logged-in verdict additionally requires a
        marker only the authenticated shell has.
        """
        if self.context is None:
            return "unavailable"
        try:
            # Real protocol round-trip: proves both the browser and this loop are alive.
            await self.context.cookies()
        except Exception:
            return "unavailable"

        url = self.page.url if self.page is not None else ""
        if (
            "platform.trans.eu" not in url
            or "auth.platform.trans.eu" in url
            or "/login" in url
            or "/logout" in url
        ):
            return "logged_out"

        for selector in (
            '[data-ctx="filters"]',
            '[data-ctx="basic-filters"]',
            'a[href*="/exchange/offers"]',
        ):
            try:
                if await self.page.locator(selector).count() > 0:
                    return "logged_in"
            except Exception:
                continue
        return "logged_out"

    async def _wait_for_cloudflare_if_present(self, timeout_sec: int | None = None) -> bool:
        """
        Проверяет наличие капчи Cloudflare Turnstile на странице.
        Если капча обнаружена, приостанавливает выполнение и ждет её решения пользователем.

        Бюджет ожидания берётся из settings.TRANS_EU_CAPTCHA_WAIT_SEC, чтобы он всегда
        оставался меньше soft/hard лимитов Celery-задачи: иначе задача убивается
        по таймауту раньше, чем оператор успевает решить капчу.
        """
        if timeout_sec is None:
            timeout_sec = settings.TRANS_EU_CAPTCHA_WAIT_SEC
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
        if not settings.TRANS_EU_USERNAME or not settings.TRANS_EU_PASSWORD:
            logger.error("Trans.eu credentials are missing settings.")
            return False

        try:
            current_url = self.page.url
            logger.info(f"login() — Шаг 0: проверка состояния. Текущий URL: {current_url}")

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
                await self.page.goto(START_URL, timeout=60000)
                await self.page.wait_for_timeout(3000)
                logger.info(f"После goto START_URL, текущий URL: {self.page.url}")

            # --- Шаг 2: Ожидание полей и заполнение ---
            logger.info("Шаг 2: Ожидание поля ввода логина")
            
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
            await self.page.click('button[type="submit"]')

            # --- Шаг 4: Ожидание редиректа на /trans-info ---
            # Бюджет покрывает действия оператора: капчу и ввод кода из письма/SMS
            # в видимом окне noVNC. Окно при этом не закрывается.
            login_wait_ms = max(int(settings.TRANS_EU_LOGIN_WAIT_SEC), 30) * 1000
            logger.warning(
                "Шаг 4: ждём вход до %s с. Если появилась капча или запрос кода — "
                "решите это в окне noVNC; браузер останется открытым.",
                login_wait_ms // 1000,
            )
            self._alert_operator(
                "Trans.eu: требуется действие оператора (капча/код из письма). "
                "Откройте noVNC и завершите вход — сессия сохранится."
            )
            try:
                await self.page.wait_for_url("**/trans-info**", timeout=login_wait_ms)
                logger.info(f"Шаг 4: Успешный вход. Текущий URL: {self.page.url}")
            except Exception as wait_err:
                # Капча/код могут появиться уже после отправки формы: ждём их
                # решения и повторяем ожидание редиректа в том же бюджете.
                if await self._wait_for_cloudflare_if_present():
                    await self.page.wait_for_url("**/trans-info**", timeout=login_wait_ms)
                else:
                    logger.error(f"LOGIN_FAILED: Редирект на /trans-info не произошёл. URL: {self.page.url}")
                    await self.page.screenshot(path="/tmp/debug_login_failed.png")
                    return False

            # --- Шаг 5: Нажать «Поиск грузов» в левом меню ---
            return await self._navigate_to_offers_via_menu()

        except Exception as e:
            logger.error(f"Login/Navigation failed: {str(e)}")
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
            return True
        except Exception as e:
            logger.error(f"Шаг 5: Не удалось перейти на /exchange/offers через меню: {e}")
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
        # --- 0. Strict date validation BEFORE login/navigation/UI ---
        # Non-empty malformed/impossible dates must fail closed with no browser
        # side effects; blank/None values keep the automatic defaults.
        date_from, date_to, unloading_date_from, unloading_date_to = (
            search_workflow.validate_search_dates(
                date_from=date_from,
                date_to=date_to,
                unloading_date_from=unloading_date_from,
                unloading_date_to=unloading_date_to,
            )
        )

        # Blank inputs default to the authoritative maxima (0.9 t / 4.8 m).
        # The strict "reject wider" policy is enforced by the import use case
        # and the UI; the shared browser client must stay usable by the
        # per-vehicle workflow, which passes its own vehicle-derived values.
        weight_to = weight_to or search_workflow.MAX_WEIGHT_TONNES
        length_to = length_to or search_workflow.MAX_LENGTH_METRES

        try:
            # Check authorization first
            # ПРАВИЛО (STRICT RULE): Сначала надо войти на портал https://platform.trans.eu и авторизоваться.
            # Только после успешной авторизации на портале Trans.eu возможен запуск скрапера.
            if not await self.login():
                raise Exception("User is not authorized on Trans.eu portal.")

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

            # Let the SPA finish its own navigation before any page.evaluate runs.
            # With wait_until="domcontentloaded" the document can still be replaced
            # afterwards, which destroys the execution context of a later evaluate.
            try:
                await self.page.wait_for_load_state("load", timeout=30000)
            except Exception:
                logger.warning("Search page did not reach 'load'; continuing after render wait.")

            await self.page.wait_for_timeout(2000)  # Let React finish rendering

            # --- Filter preparation (Expand -> More -> Clear) BEFORE any input ---
            await self._prepare_filters()

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
            # The location step can re-collapse the advanced section; make sure
            # the date inputs are clickable again before typing into them.
            await self._ensure_advanced_filters_open()
            adv_filters = self.page.locator('div[data-ctx="filters"]')
            
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
            # Шаг 7 (docs/Поиск_процедура.md): левое «От» пусто, правое «До» = 0,9.
            # Живая проверка портала: поле «Вес (т)» — это
            # div[data-ctx="load_weight.valueTo"] input, значение хранится с точкой
            # («0.9»), т.е. fill("0.9") корректен как есть.
            logger.info(f"Setting Weight To: {weight_to}")
            weight_input = self.page.locator('div[data-ctx="load_weight.valueTo"] input')
            if await weight_input.count() > 0:
                await weight_input.click()
                await weight_input.fill(str(weight_to))
            else:
                raise Exception("Weight To input not found — cannot set mandatory 0.9 t limit.")

            # --- 5. Length (LDM) — RIGHT field «До» = 4.8; LEFT «С» stays empty ---
            # Strict rule: the minimum-length (left) field is never populated;
            # the maximum is set on the RIGHT «До» input only.
            logger.info("Setting Length (LDM) To (right field) to %s", length_to)
            length_set = False
            _ldm_labels = ["Длина (погрузочные метры)", "Погрузочные метры", "LDM", "Loading meters", "Długość ładunkowa", "Load meters"]
            for context in [adv_filters, self.page]:
                if length_set:
                    break
                for label in _ldm_labels:
                    try:
                        label_el = context.locator(f"label:has-text('{label}')").first
                        if await label_el.count() > 0 and await label_el.is_visible():
                            container = label_el.locator("..")
                            inputs = container.locator("input")
                            if await inputs.count() < 2:
                                container = container.locator("..")
                                inputs = container.locator("input")
                            if await inputs.count() >= 2:
                                target_input = inputs.nth(1)  # RIGHT = «До»
                                if await target_input.is_visible():
                                    await target_input.click()
                                    await self.page.keyboard.press("Control+A")
                                    await self.page.keyboard.press("Backspace")
                                    await self.page.wait_for_timeout(100)
                                    await target_input.fill(str(length_to))
                                    await target_input.press("Tab")
                                    await self.page.wait_for_timeout(500)
                                    current_val = await target_input.input_value()
                                    if current_val == str(length_to):
                                        logger.info("Set length To (right) via label '%s': %s", label, current_val)
                                        length_set = True
                                        break
                                    if "." in str(length_to):
                                        comma_val = str(length_to).replace(".", ",")
                                        await target_input.click()
                                        await self.page.keyboard.press("Control+A")
                                        await self.page.keyboard.press("Backspace")
                                        await target_input.fill(comma_val)
                                        await target_input.press("Tab")
                                        await self.page.wait_for_timeout(500)
                                        if await target_input.input_value() == comma_val:
                                            logger.info("Set length To (right) via label '%s' (comma): %s", label, comma_val)
                                            length_set = True
                                            break
                    except Exception:
                        pass

            if not length_set:
                # Живая проверка портала: поле «Длина (погрузочные метры)» — это
                # div[data-ctx="length.to"] (правое «До»). Прежние load_ldm/
                # load_meter/load_length на портале отсутствуют.
                ldm_ctxs = ["length.to", "load_ldm.valueTo", "load_meter.valueTo", "load_length.valueTo"]
                for ctx in ldm_ctxs:
                    inp = self.page.locator(f'div[data-ctx="{ctx}"] input').first
                    if await inp.count() > 0 and await inp.is_visible():
                        await inp.click()
                        await self.page.keyboard.press("Control+A")
                        await self.page.keyboard.press("Backspace")
                        await inp.fill(str(length_to))
                        length_set = True
                        break

            if not length_set:
                raise Exception("Length (LDM) right «До» input not found — cannot set mandatory 4.8 m limit.")

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
            logger.info("Collecting complete search results (virtualized scroll + pagination)...")
            from backend.src.infrastructure.external_services.trans_eu import mapper

            raw_offers = await self._collect_all_offers()
            logger.info(f"Collected {len(raw_offers)} unique raw items.")

            # Map to Domain. A mapping failure is fatal for the run (never
            # silently skipped) so we never return a truncated success.
            results = []
            for raw in raw_offers:
                try:
                    mapped = mapper.map_to_cargo(raw)
                except Exception as map_err:
                    logger.error(f"Failed to map item: {map_err}")
                    raise Exception("Trans.eu offer mapping failed") from map_err
                results.append(mapped)

            logger.info(f"Successfully mapped {len(results)} offers.")
            return results

        except Exception as e:
            logger.error(f"Search failed: {e}")
            if self.page is not None:
                try:
                    await self.page.screenshot(path="search_failed.png")
                except Exception as shot_err:
                    logger.warning(f"Could not save failure screenshot: {shot_err}")
            return False


    async def _click_load_more(self) -> bool:
        """Click the first visible load-more control; never raises."""
        for selector in _LOAD_MORE_SELECTORS:
            try:
                btn = self.page.locator(selector).first
                if await btn.count() > 0 and await btn.is_visible(timeout=500):
                    await btn.click(force=True)
                    return True
            except Exception:
                continue
        return False


    async def _evaluate_with_retry(self, script: str, *, attempts: int = 3, label: str = "script"):
        """Run ``page.evaluate`` tolerating a document swap underneath the call.

        Trans.eu is a single-page app: a late client-side redirect destroys the
        execution context that an in-flight ``page.evaluate`` is bound to. That is
        a navigation race, not a broken extraction script, so it is retried
        in place instead of failing the whole collection as incomplete.
        """
        for attempt in range(1, attempts + 1):
            try:
                return await self.page.evaluate(script)
            except Exception as exc:
                message = str(exc).lower()
                transient = (
                    "execution context was destroyed" in message
                    or "context was destroyed" in message
                    or "navigat" in message
                    or "target closed" in message
                    or "disconnected" in message
                )
                if not transient or attempt == attempts:
                    raise
                logger.warning(
                    "%s evaluate hit a navigation race (attempt %s/%s); retrying",
                    label,
                    attempt,
                    attempts,
                )
                try:
                    await self.page.wait_for_load_state("domcontentloaded", timeout=15000)
                except Exception:
                    pass
                await self.page.wait_for_timeout(1000 * attempt)


    async def _collect_all_offers(self) -> list:
        """Collect the complete, deduplicated result list.

        The extraction script is run repeatedly while the virtualized list is
        scrolled and a load-more control is clicked. The pure
        :class:`collection.CollectionController` owns dedup, expected-count
        matching, empty/end validation and the bounded stall detection; a run
        that stops changing without a verified end marker or expected-count
        match raises :class:`collection.CollectionIncompleteError` (never a
        truncated success), and a row without a stable external ID raises the
        same error.
        """
        from backend.src.infrastructure.external_services.trans_eu import parser

        js_script = parser.get_extraction_script()
        state_script = parser.get_result_state_script()
        controller = collection.CollectionController()

        # Small settle for delayed first render before the first read.
        await self.page.wait_for_timeout(500)

        root_missing_rounds = 0
        while True:
            try:
                rows = await self._evaluate_with_retry(js_script, label="extraction")
            except Exception as exc:
                raise collection.CollectionIncompleteError(
                    "Collection failed: extraction script error"
                ) from exc
            if not isinstance(rows, list):
                raise collection.CollectionIncompleteError(
                    "Collection failed: extraction did not return a list"
                )

            try:
                state = await self._evaluate_with_retry(state_script, label="state probe")
            except Exception as exc:
                raise collection.CollectionIncompleteError(
                    "Collection failed: result-list state probe error"
                ) from exc

            if not isinstance(state, dict) or not state.get("root_found"):
                # No verified result-list container: we cannot certify loading,
                # end, empty or the expected total, so this round is unknown.
                root_missing_rounds += 1
                if root_missing_rounds >= collection.MAX_STALL_ROUNDS:
                    raise collection.CollectionIncompleteError(
                        "Collection failed: result-list container not found"
                    )
                action = controller.observe(
                    rows,
                    loading=True,
                    end_reached=False,
                    empty=False,
                    expected_total=None,
                )
            else:
                root_missing_rounds = 0
                action = controller.observe(
                    rows,
                    loading=bool(state.get("loading")),
                    end_reached=bool(state.get("end_reached")),
                    empty=bool(state.get("empty")),
                    expected_total=state.get("total"),
                    scrolled_to_bottom=bool(state.get("scrolled_to_bottom")),
                )

            if action == collection.ACTION_DONE:
                break

            # Prefer pagination over scrolling when a load-more control exists.
            if await self._click_load_more():
                await self.page.wait_for_timeout(800)
                continue

            await self.page.evaluate(_SCROLL_SCRIPT)
            await self.page.wait_for_timeout(600)

        return controller.ordered_items()

    async def _locator_visible(self, selector: str, timeout: int = 1000) -> bool:
        """Return True when the first match for ``selector`` is visible."""
        try:
            return await self.page.locator(selector).first.is_visible(timeout=timeout)
        except Exception:
            return False

    async def _is_clickable(self, selector: str) -> bool:
        """Return True when the element is actually clickable.

        ``is_visible()`` is not enough: on the portal the date/length inputs are
        rendered (with a bounding box) but covered by the results list until the
        advanced panel is opened via «Больше фильтров». This probe checks that the
        element is the topmost one at its centre (``document.elementFromPoint``).
        """
        js = r"""(sel) => {
            const el = document.querySelector(sel);
            if (!el) return false;
            const r = el.getBoundingClientRect();
            if (r.width <= 0 || r.height <= 0) return false;
            const top = document.elementFromPoint(r.left + r.width / 2, r.top + r.height / 2);
            return el === top || (top !== null && el.contains(top));
        }"""
        try:
            return bool(await self.page.evaluate(js, selector))
        except Exception:
            return False

    async def _ensure_advanced_filters_open(self) -> None:
        """Ensure the advanced filter section (dates/weight/length) is open and
        clickable, clicking «Больше фильтров» when it has collapsed.

        The location step can re-collapse the advanced section, so this is also
        called again right before the date inputs are set — not only during
        filter preparation.
        """
        advanced_selector = 'div[data-ctx="dateinput-field"] input[name="from"]'
        more_filters_selectors = [
            'button[data-ctx="basicFilters.form.show.advanced.filters"]',
            'button:has-text("БОЛЬШЕ ФИЛЬТРОВ")',
            'button:has-text("Больше фильтров")',
            'button:has-text("MORE FILTERS")',
            'button:has-text("More filters")',
        ]
        if await self._is_clickable(advanced_selector):
            return
        for selector in more_filters_selectors:
            if await self._click_if_visible(selector, timeout=2000):
                await self.page.wait_for_timeout(2000)
                break
        if not await self._is_clickable(advanced_selector):
            raise Exception("Advanced filters panel is not visible. Cannot proceed safely.")

    async def _click_if_visible(self, selector: str, timeout: int = 2000) -> bool:
        """Click the first visible match for ``selector``. Never raises."""
        try:
            btn = self.page.locator(selector).first
            if await btn.is_visible(timeout=timeout):
                await btn.click(force=True)
                return True
        except Exception:
            return False
        return False

    async def _prepare_filters(self) -> None:
        """Prepare filters in the required order BEFORE entering any search data.

        Sequence: ensure the base panel is expanded (EXPAND FILTERS), open the
        advanced panel (MORE FILTERS) even when the base location field is
        already visible, verify the advanced panel is present, then clear all
        stale filters (Clear filters). The clear step is mandatory: a missing
        or unclickable clear control raises and stops the search so stale
        filters are never searched against.

        Panels that are already open are never collapsed by a needless click.
        """
        loading_selector = 'div[data-ctx="place-loading_place-0"] input'

        expand_step1_selectors = [
            'button:has-text("РАЗВЕРНУТЬ ФИЛЬТРЫ")',
            'button:has-text("Развернуть фильтры")',
            'button:has-text("EXPAND FILTERS")',
            'button:has-text("Expand filters")',
            'button[data-ctx="basic-filters-form-hide-filters-preview"]',
        ]
        clear_selectors = [
            # Проверено на живом портале: единственный «очистить фильтры» — этот
            # контрол. Прежний `basicFilters.form.clear` не существует, из-за чего
            # поиск всегда падал с «Refusing to search with stale filters».
            '[data-ctx="basic-filters-form-clear-filters"]',
            'button[data-ctx="basicFilters.form.clear"]',
            'button:has-text("Очистить фильтры")',
            'button:has-text("Очистить")',
            'button:has-text("Clear filters")',
            'button:has-text("Clear all")',
            'button:has-text("Wyczyść filtry")',
        ]

        # Step 1: ensure the base location field is visible (EXPAND FILTERS).
        if not await self._locator_visible(loading_selector, timeout=1000):
            expanded = False
            for selector in expand_step1_selectors:
                if await self._click_if_visible(selector, timeout=2000):
                    await self.page.wait_for_timeout(2000)
                    expanded = True
                    break

            if not await self._locator_visible(loading_selector, timeout=10000):
                logger.warning("Loading location field not visible. Checking for Cloudflare...")
                if await self._wait_for_cloudflare_if_present():
                    for selector in expand_step1_selectors:
                        if await self._click_if_visible(selector, timeout=2000):
                            await self.page.wait_for_timeout(2000)
                            break
                    if not await self._locator_visible(loading_selector, timeout=15000):
                        raise Exception(
                            "Loading location field not visible after re-expanding filters."
                        )
                else:
                    logger.error("Cloudflare Turnstile was not solved. Aborting search.")
                    if self.page is not None:
                        try:
                            await self.page.screenshot(path="/tmp/debug_filters_not_expanded.png")
                        except Exception:
                            pass
                    raise Exception("Cloudflare Turnstile was not solved. Search aborted.")
            if not expanded:
                logger.info("Step 1 — Expand Filters button not found — base panel already open.")

        # Step 2: open the advanced panel (MORE FILTERS) even when the base
        # field is already visible; skip the click when it is already open so
        # we never collapse an already-open panel.
        await self._ensure_advanced_filters_open()

        # Step 3: clear filters (mandatory when filters are actually set).
        # «Очистить фильтры» — это ссылка <a data-ctx="basic-filters-form-clear-filters">
        # (в левом нижнем углу, видима после «Больше фильтров»), а не <button>.
        # Если её вдруг нет — сбрасываем чипы предпросмотра фильтра по одному.
        cleared = False
        for selector in clear_selectors:
            if await self._click_if_visible(selector, timeout=1000):
                await self.page.wait_for_timeout(1000)
                cleared = True
                logger.info(f"Clearing filters using: {selector}")
                break
        if not cleared:
            chip_close = self.page.locator('[data-ctx="filter-preview"] button[data-ctx="close"]')
            removed = 0
            for _ in range(24):  # bounded: до 24 чипов предпросмотра
                first = chip_close.first
                try:
                    if await first.count() > 0 and await first.is_visible(timeout=500):
                        await first.click(force=True)
                        await self.page.wait_for_timeout(300)
                        removed += 1
                        continue
                except Exception:
                    pass
                break
            if removed:
                cleared = True
                logger.info(f"Cleared {removed} filter chip(s) via their close buttons.")
            else:
                logger.info("No clear control and no active filter chips: filters are already clean.")

    async def _set_date_input(self, parent_locator, name: str, index: int, value: str):
        """
        Sets date securely using calendar navigation and ISO ID selectors.
        Value must be DD.MM.YYYY. Failures raise ValueError so they propagate
        into the search failure path instead of silently proceeding with an
        unset or ambiguous date.
        """
        inp = parent_locator.locator(f'input[name="{name}"]').nth(index)
        if await inp.count() <= 0:
            raise ValueError(f"Date input {name}[{index}] not found.")

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

        # Parse target (raises ValueError for malformed/impossible values).
        target = search_workflow.parse_date_strict(value)
        if target is None:
            raise ValueError(f"Empty date value for {name}[{index}] is not expected here.")
        target_day, target_month, target_year = target.day, target.month, target.year
        target_iso = f"{target_year}-{target_month:02d}-{target_day:02d}"

        # Open calendar.
        await inp.click()

        # Wait for the calendar header; fail closed if it never appears.
        header_btn = self.page.locator('button[data-ctx="switch-mode"]')
        try:
            await header_btn.wait_for(state="visible", timeout=3000)
        except Exception:
            logger.warning("Calendar header not found. Trying force click again.")
            try:
                await inp.click(force=True)
                await header_btn.wait_for(state="visible", timeout=3000)
            except Exception as header_err:
                raise ValueError("Calendar header did not appear.") from header_err

        # Month navigation loop (max 2 years).
        reached = False
        for _ in range(24):
            header_text = await header_btn.text_content()
            parsed = search_workflow.parse_calendar_header(header_text)
            if parsed is None:
                raise ValueError(f"Could not parse calendar header: {header_text!r}")
            current_month, current_year = parsed
            if current_year == target_year and current_month == target_month:
                reached = True
                break
            next_ok = (target_year > current_year) or (
                target_year == current_year and target_month > current_month
            )
            nav_btn_sel = (
                'button[data-ctx="switch-next-page"]'
                if next_ok
                else 'button[data-ctx="switch-prev-page"]'
            )
            await self.page.locator(nav_btn_sel).click()
            await self.page.wait_for_timeout(200)

        if not reached:
            raise ValueError(
                f"Calendar target month {target_month:02d}.{target_year} was not reached."
            )

        # Pick day by exact ISO id (most reliable).
        day_wrapper = self.page.locator(f'div[data-ctx-id="{target_iso}-wrapper"]')
        if await day_wrapper.count() > 0:
            logger.info(f"Clicking day wrapper: {target_iso}")
            await day_wrapper.click()
        else:
            # Safe fallback: exact text match within the now-verified current
            # month; ambiguous neighboring-month days are never selected.
            day_cells = self.page.locator(
                'div[data-ctx="option-wrapper"]:not([class*="_1d3i7nl_jh_g"]) div._1d3i7nl_jh_e'
            )
            matched = False
            for cell in await day_cells.all():
                cell_text = (await cell.text_content() or "").strip()
                if cell_text == str(target_day):
                    await cell.click()
                    matched = True
                    break
            if not matched:
                raise ValueError(f"Day cell for {target_iso} not found.")

        # Close (usually auto-closes).
        await self.page.wait_for_timeout(500)
        await self.page.keyboard.press("Escape")

    async def _set_location_field(self, container_selector: str, value: str, radius: int = 0):
        """
        Set a location field following the documented strict input order:
        1) {ISO}, {postcode}, {city}, 2) {ISO}, {postcode}, 3) {ISO}, then the
        permitted Russian fallbacks only when no dropdown appears for the
        primary attempts. The user-specified ISO/postcode is preserved: a
        dropdown candidate with a different country or postcode is rejected.

        Requires modal window presence for success; fails closed otherwise.
        """
        query = search_workflow.parse_location_input(value)
        attempts = search_workflow.build_location_attempts(query)

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
                        for selector in [
                            'button:has-text("РАЗВЕРНУТЬ ФИЛЬТРЫ")',
                            'button:has-text("Развернуть фильтры")',
                            'button:has-text("EXPAND FILTERS")',
                            'button:has-text("MORE FILTERS")',
                            'button:has-text("Expand filters")',
                            'button:has-text("More filters")',
                            'button[data-ctx="basic-filters-form-hide-filters-preview"]',
                        ]:
                            if await self._click_if_visible(selector, timeout=2000):
                                await self.page.wait_for_timeout(2000)
                                break
                    await container.wait_for(state="attached", timeout=15000)
                    await container.locator('input').first.wait_for(state="visible", timeout=15000)
                else:
                    logger.error("Cloudflare Turnstile was not solved. Aborting location input.")
                    raise Exception("Cloudflare Turnstile was not solved. Location input aborted.")

            # Live portal renders each address candidate as <div role="option"
            # data-ctx="option"> inside a portal ("collapsed-address-select-options-container").
            # The legacy `#mainRegionDropdowns span[class*="Option__option"]` no longer exists.
            modal_selector = 'div[role="option"]'
            success = False
            
            # Шаг 4 (docs/Поиск_процедура.md): клик по полю, затем ПРЯМОЙ ввод.
            # Живая проверка портала: input — readonly и перекрыт
            # <span role="presentation">, поэтому клик по нему перехватывается.
            # Выпадающий список открывает клик по label[data-ctx="select"].
            select_label = container.locator('label[data-ctx="select"]').first

            for i, (attempt, city_for_ranking) in enumerate(attempts):
                step_num = i + 1
                logger.info(f"Location Step {step_num}: Attempting '{attempt}'")

                await select_label.click()
                await self.page.wait_for_timeout(400)

                # Резервная попытка: сбросить прежнее значение штатной кнопкой
                # очистки селекта (svg[data-ctx="clear"]) и раскрыть список заново.
                if i > 0:
                    clear_btn = container.locator('svg[data-ctx="clear"]').first
                    try:
                        if await clear_btn.count() > 0 and await clear_btn.is_visible(timeout=1000):
                            await clear_btn.click()
                            await self.page.wait_for_timeout(300)
                            await select_label.click()
                            await self.page.wait_for_timeout(300)
                    except Exception:
                        pass

                await self.page.keyboard.type(attempt, delay=60)
                await self.page.wait_for_timeout(2000)
                
                # 3. Wait for Modal presence (Confirmation of active field)
                try:
                    await self.page.wait_for_selector(modal_selector, timeout=8000)
                    
                    # 4. Rank dropdown candidates; reject incompatible options.
                    options_locator = self.page.locator(modal_selector)
                    options_count = await options_locator.count()
                    if options_count == 0:
                        logger.warning(f"Modal appeared but no options for step {step_num}.")
                        continue

                    option_texts = []
                    for idx in range(options_count):
                        option_texts.append(
                            (await options_locator.nth(idx).text_content() or "").strip()
                        )

                    best_index = search_workflow.rank_location_options(
                        option_texts,
                        iso=query.iso,
                        postcode=query.postcode,
                        city=city_for_ranking,
                    )
                    if best_index is None:
                        logger.warning(
                            f"No compatible option for step {step_num} ('{attempt}')."
                        )
                        continue

                    logger.info(
                        f"Selecting compatible option at index {best_index} "
                        f"for '{attempt}': {option_texts[best_index]!r}"
                    )
                    dropdown_option = options_locator.nth(best_index)
                    await dropdown_option.click(force=True)
                    
                    logger.info(f"Success at Step {step_num} with '{attempt}'")
                    success = True
                    break
                except Exception as modal_err:
                    logger.debug(f"Modal handling failed for step {step_num}: {modal_err}")
                    logger.warning(f"Modal did not appear for step {step_num} ('{attempt}').")
                    continue

            if not success:
                logger.error(f"Failed to set location '{value}' after all steps.")
                raise ValueError(f"Location selection failed for {value}")

            # 5. Set Radius if requested.
            # Радиус — комбобокс: после ввода числа появляется список
            # (ul[data-ctx="rangeOptionsList"] > div[data-ctx="rangeOption"]),
            # значение фиксируется вторым кликом по пункту («+75 km»).
            if radius > 0:
                await self.page.wait_for_timeout(1000)
                range_input = container.locator('input[name="range"]').first
                try:
                    if await range_input.count() > 0 and await range_input.is_visible(timeout=1000):
                        logger.info(f"Setting radius to {radius} km")
                        await range_input.click(force=True)
                        await self.page.wait_for_timeout(300)
                        await range_input.fill(str(radius))
                        await self.page.wait_for_timeout(500)
                        option = container.locator(f'[data-ctx-id="rangeOption{radius}"]').first
                        if await option.count() > 0 and await option.is_visible(timeout=1500):
                            await option.click()
                            await self.page.wait_for_timeout(500)
                            logger.info(f"Radius {radius} km fixed via option click.")
                        else:
                            opt_text = container.locator(
                                f'[data-ctx="rangeOption"]:has-text("+{radius} km")'
                            ).first
                            if await opt_text.count() > 0 and await opt_text.is_visible(timeout=1500):
                                await opt_text.click()
                                await self.page.wait_for_timeout(500)
                                logger.info(f"Radius {radius} km fixed via option text click.")
                            else:
                                await self.page.keyboard.press("Enter")
                                await self.page.wait_for_timeout(300)
                                logger.info("Radius option not found; pressed Enter as fallback.")
                except Exception as ex:
                    logger.info(f"Radius input not visible or not found ({ex}). Skipping as per instructions.")

        except Exception as e:
            logger.error(f"Error in _set_location_field: {e}")
            if self.page is not None:
                try:
                    await self.page.screenshot(path="location_error.png")
                except Exception:
                    pass
            raise e
