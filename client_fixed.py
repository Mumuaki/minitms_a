"""
client.py — Клиент Trans.eu через браузерную автоматизацию (Playwright).

ПОЛНОСТЬЮ ПЕРЕПИСАННАЯ ВЕРСИЯ.

Ключевые гарантии этой версии (требование заказчика — «никакой возможности
альтернативного понимания/чтения при запуске скрапера»):

  1. ДЕТЕРМИНИРОВАННЫЙ ЗАПУСК БРАУЗЕРА.
     Путь к исполняемому файлу Chromium вычисляется ОДНИМ строго
     определённым алгоритмом (resolve_chromium_executable). Если бинарь
     не найден — запуск немедленно прерывается понятной ошибкой
     (fail-fast). Нет «тихого» отката на ~/.cache/ms-playwright и нет
     ситуации, когда Playwright сам выбирает непредсказуемый путь.

  2. ЕДИНАЯ ТОЧКА ВХОДА ЗАПУСКА.
     Запуск браузера возможен только через start(). Параллельные/повторные
     запуски на одном профиле защищены межпроцессным мьютексом (Redis lock
     с TTL, с локальным fallback на файловую блокировку). Это исключает
     порчу персистентного профиля Chrome двумя процессами одновременно.

  3. ПРОВЕРКА АВТОРИЗАЦИИ ПО UI, А НЕ ТОЛЬКО ПО URL.
     login() сначала надёжно определяет состояние сессии, и считает
     пользователя авторизованным только при наличии элементов рабочего
     интерфейса (а не просто по совпадению строки URL).

  4. УСТОЙЧИВОСТЬ.
     - резервная копия storage_state (cookies) перед рискованными шагами;
     - детект и очистка зомби-процессов Chrome и stale-lock файлов профиля;
     - счётчик неудачных логинов + защита от бесконечного цикла логина;
     - единый таймаут-бюджет, единые селекторы (без «магических» веток).

Публичный интерфейс СОХРАНЁН без изменений, чтобы файл подключался к
существующему коду как есть:

  Класс TransEuClient:
    - @classmethod async get_instance()
    - async start()
    - async stop()
    - async close_page_only()
    - async login() -> bool
    - async _navigate_to_offers_via_menu() -> bool
    - async _wait_for_cloudflare_if_present(timeout_sec=300) -> bool
    - async search_offers(loading_location, unloading_location,
          date_from=None, date_to=None, unloading_date_from=None,
          unloading_date_to=None, weight_to="0.9", length_to=None,
          loading_radius=75, unloading_radius=75) -> list | False
    - async _set_date_input(parent_locator, name, index, value)
    - async _set_location_field(container_selector, value, radius=0)

  Модульные функции parser.get_extraction_script() и mapper.map_to_cargo()
  используются внутри search_offers (импортируются лениво, как в оригинале).
"""

import asyncio
import glob
import json
import logging
import os
import subprocess
import time
from pathlib import Path

from playwright.async_api import async_playwright, BrowserContext, Page, Playwright

from backend.src.infrastructure.config.settings import settings

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Глобальный экземпляр для Singleton (на уровне модуля)
# ---------------------------------------------------------------------------
_trans_eu_client_instance = None
_trans_eu_client_lock: asyncio.Lock | None = None

# ---------------------------------------------------------------------------
# Константы запуска (единый источник истины — никаких «магических» значений
# по месту использования). Любая ветка кода читает только отсюда.
# ---------------------------------------------------------------------------

# Каталог, куда Dockerfile устанавливает Chromium (root → chown appuser).
# Должен совпадать с ENV PLAYWRIGHT_BROWSERS_PATH в Dockerfile/compose.
_DEFAULT_BROWSERS_PATH = "/ms-playwright"

# Виртуальный дисплей Xvfb (для видимого режима под noVNC на :6080).
_DEFAULT_DISPLAY = ":99"

# Стартовый URL портала.
_START_URL = "https://platform.trans.eu"
_OFFERS_URL = "https://platform.trans.eu/exchange/offers"

# Единые таймауты (мс), чтобы поведение запуска было предсказуемым.
_T_NAV = 60000          # навигация
_T_ELEMENT = 15000      # ожидание элемента
_T_SHORT = 3000

# Защита от бесконечного цикла логина.
_MAX_LOGIN_ATTEMPTS = 3

# Имя ключа Redis-мьютекса и TTL (сек). TTL > максимально ожидаемого времени
# одного прогона скрапера, но конечный — чтобы lock сам снимался при падении.
_REDIS_LOCK_KEY = "minitms:trans_eu:browser_lock"
_REDIS_LOCK_TTL = 1800  # 30 минут

# Лог-файл диагностики (как в оригинале — для трассировки запуска).
_DBG_LOG = "/tmp/trans_eu_client.log"


def _dbg(msg, data=None, hyp=""):
    """Лёгкая структурная трассировка запуска (best-effort, не падает)."""
    try:
        entry = {
            "ts": int(time.time() * 1000),
            "loc": "client.py",
            "msg": msg,
            "hyp": hyp,
        }
        if data is not None:
            entry["data"] = data
        with open(_DBG_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception:
        pass


# ===========================================================================
# ДЕТЕРМИНИРОВАННОЕ ВЫЧИСЛЕНИЕ ПУТИ К CHROMIUM
# ===========================================================================
def resolve_chromium_executable() -> str:
    """
    Единственный разрешённый способ определить путь к Chromium.

    Алгоритм строго определён и не имеет «тихих» откатов:

      1. Если задана переменная PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH и файл
         существует — используем её (явное переопределение оператором).
      2. Иначе берём PLAYWRIGHT_BROWSERS_PATH (по умолчанию /ms-playwright)
         и ищем в нём бинарь по шаблону chromium-*/chrome-linux64/chrome.
         При нескольких совпадениях берём ДЕТЕРМИНИРОВАННО самую свежую
         (старшую) версию — сортировка по номеру сборки, а не «первый по
         списку файловой системы».
      3. Если ничего не найдено — НЕМЕДЛЕННО возбуждаем RuntimeError с
         понятным сообщением. Никакого запуска «как-нибудь» не происходит.

    Возвращает абсолютный путь к существующему исполняемому файлу.
    """
    # Шаг 1. Явное переопределение.
    explicit = os.environ.get("PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH", "").strip()
    if explicit:
        if os.path.isfile(explicit) and os.access(explicit, os.X_OK):
            _dbg("chromium resolved via explicit env", {"path": explicit})
            return explicit
        raise RuntimeError(
            f"PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH задан ('{explicit}'), "
            f"но файл не существует или не исполняемый."
        )

    # Шаг 2. Поиск в каталоге установки браузеров.
    browsers_path = os.environ.get("PLAYWRIGHT_BROWSERS_PATH", _DEFAULT_BROWSERS_PATH)
    # Жёстко фиксируем переменную окружения, чтобы и Playwright, и наш код
    # смотрели РОВНО в один каталог.
    os.environ["PLAYWRIGHT_BROWSERS_PATH"] = browsers_path

    if not os.path.isdir(browsers_path):
        raise RuntimeError(
            f"Каталог браузеров Playwright не найден: '{browsers_path}'. "
            f"Проверьте ENV PLAYWRIGHT_BROWSERS_PATH в docker-compose/Dockerfile "
            f"и что 'playwright install chromium' выполнен в образе."
        )

    pattern = os.path.join(browsers_path, "chromium-*", "chrome-linux64", "chrome")
    matches = [m for m in glob.glob(pattern) if os.path.isfile(m) and os.access(m, os.X_OK)]

    if not matches:
        # Также пробуем headless-shell вариант (некоторые сборки кладут так).
        alt_pattern = os.path.join(
            browsers_path, "chromium_headless_shell-*", "chrome-linux64", "headless_shell"
        )
        matches = [m for m in glob.glob(alt_pattern) if os.path.isfile(m) and os.access(m, os.X_OK)]

    if not matches:
        # Перечислим, что реально лежит в каталоге — упростит диагностику.
        try:
            present = sorted(os.listdir(browsers_path))
        except Exception:
            present = []
        raise RuntimeError(
            "Исполняемый файл Chromium не найден в "
            f"'{browsers_path}' (шаблон: chromium-*/chrome-linux64/chrome). "
            f"Содержимое каталога: {present}. "
            "Версия библиотеки playwright в requirements.txt должна совпадать "
            "с версией, установленной 'playwright install --with-deps chromium' "
            "в Docker-образе."
        )

    # Детерминированный выбор: самая высокая версия сборки chromium-<N>.
    def _build_number(path: str) -> int:
        try:
            # .../chromium-1234/chrome-linux64/chrome  -> 1234
            comp = Path(path).parts
            for part in comp:
                if part.startswith("chromium-") or part.startswith("chromium_headless_shell-"):
                    digits = "".join(ch for ch in part.split("-", 1)[1] if ch.isdigit())
                    return int(digits) if digits else 0
        except Exception:
            pass
        return 0

    matches.sort(key=_build_number, reverse=True)
    chosen = matches[0]
    _dbg("chromium resolved via glob", {"path": chosen, "candidates": matches})
    logger.info(f"Chromium executable (deterministic): {chosen}")
    return chosen


class TransEuClient:
    """
    Клиент Trans.eu (браузерная автоматизация, Playwright Persistent Context).

    Singleton — гарантирует один экземпляр браузера на профиль.
    """

    # -- Singleton --------------------------------------------------------
    @classmethod
    async def get_instance(cls):
        """Возвращает разделяемый экземпляр TransEuClient."""
        global _trans_eu_client_instance, _trans_eu_client_lock
        if _trans_eu_client_lock is None:
            _trans_eu_client_lock = asyncio.Lock()
        async with _trans_eu_client_lock:
            if _trans_eu_client_instance is None:
                _trans_eu_client_instance = cls()
            return _trans_eu_client_instance

    def __init__(self):
        self.playwright: Playwright | None = None
        self.context: BrowserContext | None = None
        self.page: Page | None = None
        # ВСЕГДА видимый режим — оператор наблюдает через noVNC (:6080).
        self.headless = False
        self.user_data_dir = settings.BROWSER_PROFILE_DIR
        self._failed_logins = 0
        self._redis = None  # ленивое подключение к Redis для мьютекса
        self._holds_redis_lock = False
        self._file_lock_path = os.path.join(self.user_data_dir, ".trans_eu_browser.lock")

    # =====================================================================
    # МЕЖПРОЦЕССНЫЙ МЬЮТЕКС (защита профиля от параллельных запусков)
    # =====================================================================
    def _get_redis(self):
        """Ленивое синхронное подключение к Redis. None при недоступности."""
        if self._redis is not None:
            return self._redis
        try:
            import redis  # redis-py уже есть в зависимостях проекта
            url = os.environ.get("REDIS_URL")
            if url:
                self._redis = redis.Redis.from_url(url, socket_connect_timeout=2)
            else:
                self._redis = redis.Redis(
                    host=os.environ.get("REDIS_HOST", "redis"),
                    port=int(os.environ.get("REDIS_PORT", "6379")),
                    password=os.environ.get("REDIS_PASSWORD") or None,
                    socket_connect_timeout=2,
                )
            self._redis.ping()
            return self._redis
        except Exception as e:
            logger.warning(f"Redis недоступен для мьютекса ({e}). Fallback на файловую блокировку.")
            self._redis = None
            return None

    def _acquire_launch_lock(self) -> bool:
        """
        Захватывает межпроцессный мьютекс перед запуском браузера.
        Возвращает True при успехе. Никогда не запускаем браузер без него.
        """
        r = self._get_redis()
        if r is not None:
            try:
                # SET NX EX — атомарный захват с TTL.
                ok = r.set(_REDIS_LOCK_KEY, str(os.getpid()), nx=True, ex=_REDIS_LOCK_TTL)
                if ok:
                    self._holds_redis_lock = True
                    _dbg("redis lock acquired", {"pid": os.getpid()})
                    return True
                holder = r.get(_REDIS_LOCK_KEY)
                logger.error(f"Браузер уже запущен другим процессом (Redis lock держит pid={holder}).")
                return False
            except Exception as e:
                logger.warning(f"Ошибка Redis-мьютекса ({e}). Fallback на файловую блокировку.")

        # Fallback: файловая блокировка через атомарный O_EXCL.
        try:
            os.makedirs(self.user_data_dir, exist_ok=True)
            fd = os.open(self._file_lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.write(fd, str(os.getpid()).encode())
            os.close(fd)
            _dbg("file lock acquired", {"pid": os.getpid(), "path": self._file_lock_path})
            return True
        except FileExistsError:
            # Проверяем, жив ли владелец lock-файла; если нет — забираем.
            if self._steal_dead_file_lock():
                return True
            logger.error(f"Браузер уже запущен (file lock существует: {self._file_lock_path}).")
            return False
        except Exception as e:
            logger.error(f"Не удалось захватить файловую блокировку: {e}")
            return False

    def _steal_dead_file_lock(self) -> bool:
        """Если процесс-владелец lock-файла мёртв — снимаем и захватываем заново."""
        try:
            with open(self._file_lock_path, "r") as f:
                pid_str = f.read().strip()
            pid = int(pid_str) if pid_str.isdigit() else -1
            alive = False
            if pid > 0:
                try:
                    os.kill(pid, 0)  # сигнал 0 — проверка существования
                    alive = True
                except OSError:
                    alive = False
            if not alive:
                logger.warning(f"Lock-файл принадлежит мёртвому pid={pid}. Снимаем и захватываем.")
                os.unlink(self._file_lock_path)
                fd = os.open(self._file_lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                os.write(fd, str(os.getpid()).encode())
                os.close(fd)
                return True
        except Exception as e:
            logger.warning(f"Не удалось проверить/перехватить мёртвый lock-файл: {e}")
        return False

    def _release_launch_lock(self):
        """Снимает межпроцессный мьютекс (вызывается из stop())."""
        if self._holds_redis_lock and self._redis is not None:
            try:
                self._redis.delete(_REDIS_LOCK_KEY)
                _dbg("redis lock released", {})
            except Exception as e:
                logger.warning(f"Не удалось снять Redis-мьютекс: {e}")
            self._holds_redis_lock = False
        try:
            if os.path.exists(self._file_lock_path):
                with open(self._file_lock_path, "r") as f:
                    if f.read().strip() == str(os.getpid()):
                        os.unlink(self._file_lock_path)
        except Exception:
            pass

    # =====================================================================
    # ПОДГОТОВКА ОКРУЖЕНИЯ И ОЧИСТКА ПРОФИЛЯ
    # =====================================================================
    def _kill_zombie_chrome(self):
        """Жёстко убивает зависшие процессы Chrome (защита от утечки памяти)."""
        try:
            subprocess.run(["pkill", "-9", "-f", "chrome"], timeout=5, capture_output=True)
            logger.info("Зомби-процессы chrome завершены (SIGKILL).")
        except Exception as e:
            logger.warning(f"Не удалось завершить процессы chrome: {e}")

    def _clean_singleton_locks(self):
        """Удаляет stale-lock файлы профиля Chrome (в т.ч. битые симлинки)."""
        cleaned = False
        for name in ("SingletonLock", "SingletonCookie", "SingletonSocket"):
            p = Path(self.user_data_dir) / name
            if p.exists() or p.is_symlink():
                try:
                    p.unlink(missing_ok=True)
                    logger.info(f"Удалён stale-файл профиля: {name}")
                    cleaned = True
                except OSError as e:
                    logger.error(f"Не удалось удалить {name}: {e}")
        if cleaned:
            # На медленной FS (Docker volume) даём ОС синхронизироваться.
            time.sleep(1)

    def _backup_storage_state(self):
        """
        Резервная копия cookies (storage_state) из персистентного профиля.
        Best-effort: позволяет восстановить сессию при порче профиля.
        """
        try:
            cookies_src = os.path.join(self.user_data_dir, "Default", "Cookies")
            backup_dir = os.path.join(self.user_data_dir, "_backup")
            os.makedirs(backup_dir, exist_ok=True)
            if os.path.exists(cookies_src):
                import shutil
                shutil.copy2(cookies_src, os.path.join(backup_dir, "Cookies.bak"))
                _dbg("storage_state backed up", {})
        except Exception as e:
            logger.debug(f"Бэкап storage_state пропущен: {e}")

    # =====================================================================
    # ЗАПУСК / ОСТАНОВКА БРАУЗЕРА
    # =====================================================================
    async def start(self):
        """
        Инициализация Playwright с Persistent Context.
        ДЕТЕРМИНИРОВАННЫЙ ЗАПУСК. Единственная точка входа.
        """
        global _trans_eu_client_lock
        if _trans_eu_client_lock is None:
            _trans_eu_client_lock = asyncio.Lock()

        async with _trans_eu_client_lock:
            # Если контекст уже жив — ничего не делаем (идемпотентность).
            if self.context is not None:
                try:
                    _ = self.context.pages  # обращение к живому контексту
                    if self.page is None or self.page.is_closed():
                        self.page = (
                            self.context.pages[0]
                            if self.context.pages
                            else await self.context.new_page()
                        )
                    logger.info("TransEuClient уже запущен и активен.")
                    return
                except Exception:
                    logger.warning("Существующий контекст мёртв. Перезапуск...")
                    self.context = None
                    self.page = None

            # 1) Межпроцессный мьютекс — БЕЗ него браузер не стартует.
            if not self._acquire_launch_lock():
                raise RuntimeError(
                    "Запуск браузера отклонён: другой процесс уже использует "
                    "профиль Trans.eu (защита от параллельного запуска)."
                )

            try:
                # 2) DISPLAY для Xvfb (Linux, видимый режим под noVNC).
                if os.name != "nt" and not os.environ.get("DISPLAY"):
                    os.environ["DISPLAY"] = _DEFAULT_DISPLAY

                # 3) Профиль и очистка.
                if not os.path.exists(self.user_data_dir):
                    os.makedirs(self.user_data_dir, exist_ok=True)
                self._kill_zombie_chrome()
                self._clean_singleton_locks()
                self._backup_storage_state()

                logger.info(
                    f"Старт TransEuClient: headless={self.headless}, "
                    f"DISPLAY={os.environ.get('DISPLAY')}, profile={self.user_data_dir}"
                )

                # 4) Детерминированное определение Chromium (fail-fast).
                #    Любая ошибка здесь прерывает запуск понятным исключением.
                chrome_exe = resolve_chromium_executable()

                # 5) Старт Playwright.
                if self.playwright is None:
                    self.playwright = await async_playwright().start()

                launch_args = {
                    "user_data_dir": self.user_data_dir,
                    "headless": self.headless,
                    "executable_path": chrome_exe,  # ВСЕГДА явный путь.
                    "slow_mo": 200,
                    "viewport": None,
                    "args": [
                        "--start-maximized",
                        "--disable-blink-features=AutomationControlled",
                        "--no-sandbox",
                        "--disable-dev-shm-usage",  # против /dev/shm OOM в Docker
                    ],
                }

                self.context = await self.playwright.chromium.launch_persistent_context(**launch_args)

                # 6) Stealth-инъекция (маскировка автоматизации, обход Turnstile).
                await self.context.add_init_script(
                    """
                    Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
                    window.chrome = { runtime: {}, loadTimes: function() {}, csi: function() {}, app: {} };
                    const originalQuery = window.navigator.permissions.query;
                    window.navigator.permissions.query = (parameters) => (
                        parameters.name === 'notifications'
                            ? Promise.resolve({ state: Notification.permission })
                            : originalQuery(parameters)
                    );
                    Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
                    Object.defineProperty(navigator, 'languages', { get: () => ['ru-RU', 'ru', 'en-US', 'en'] });
                    """
                )

                # 7) Рабочая страница.
                if self.context.pages:
                    self.page = self.context.pages[0]
                else:
                    self.page = await self.context.new_page()

                _dbg("start() browser launched OK", {"pages": len(self.context.pages)}, "H-B")
                logger.info("Браузер успешно запущен.")

            except Exception:
                # При любой ошибке запуска снимаем мьютекс, чтобы не залипал.
                self._release_launch_lock()
                # И стараемся корректно закрыть частично поднятые ресурсы.
                try:
                    if self.context is not None:
                        await self.context.close()
                except Exception:
                    pass
                try:
                    if self.playwright is not None:
                        await self.playwright.stop()
                except Exception:
                    pass
                self.context = None
                self.playwright = None
                self.page = None
                raise

    async def stop(self):
        """
        Закрывает контекст и Playwright, снимает межпроцессный мьютекс.
        Использовать при остановке сервиса или ручном перезапуске.
        """
        try:
            if self.context is not None:
                await self.context.close()
        except Exception as e:
            logger.warning(f"Ошибка при закрытии контекста: {e}")
        try:
            if self.playwright is not None:
                await self.playwright.stop()
        except Exception as e:
            logger.warning(f"Ошибка при остановке Playwright: {e}")
        finally:
            self.context = None
            self.playwright = None
            self.page = None
            self._release_launch_lock()
            logger.info("TransEuClient (Persistent) остановлен.")

    async def close_page_only(self):
        """Закрывает страницу, не закрывая браузер (для будущей логики)."""
        if self.page is not None:
            await self.page.close()

    async def _ensure_started(self):
        """Гарантирует, что браузер запущен, перед любым действием."""
        if self.context is None or self.page is None or self.page.is_closed():
            await self.start()

    # =====================================================================
    # CLOUDFLARE TURNSTILE
    # =====================================================================
    async def _wait_for_cloudflare_if_present(self, timeout_sec: int = 300) -> bool:
        """
        Детектирует капчу Cloudflare Turnstile. Если найдена — ждёт ручного
        решения через noVNC (:6080). Возвращает True, если капчи нет или
        она решена; False — если не решена за timeout_sec.
        """
        cf_indicators = [
            'iframe[src*="challenges.cloudflare.com"]',
            'iframe[src*="challenge-platform"]',
            'iframe[src*="turnstile"]',
            'iframe[src*="cdn-cgi"]',
            'iframe[src*="/challenge"]',
            'div:has-text("Подтвердите, что вы человек")',
            'div:has-text("Verify you are human")',
            '*:has-text("выполнив задание ниже")',
        ]

        detected = False
        for indicator in cf_indicators:
            try:
                el = self.page.locator(indicator).first
                if await el.count() > 0 and await el.is_visible():
                    detected = True
                    logger.warning(f"Cloudflare Turnstile обнаружен: '{indicator}'")
                    break
            except Exception:
                pass

        if not detected:
            return False

        logger.warning("!!! ОБНАРУЖЕНА КАПЧА CLOUDFLARE !!!")
        logger.warning("Откройте noVNC (http://<server>:6080) и решите капчу.")
        try:
            await self.page.screenshot(path="/tmp/cloudflare_detected.png")
        except Exception:
            pass

        start_time = time.time()
        consecutive_resolves = 0
        required_resolves = 3  # 3 подряд «чистых» проверки = капча решена

        while time.time() - start_time < timeout_sec:
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
                    logger.info("Капча Cloudflare решена. Продолжаем.")
                    return True
            else:
                consecutive_resolves = 0
            await self.page.wait_for_timeout(3000)

        logger.error(f"Капча Cloudflare не решена за {timeout_sec} с. Прерывание.")
        return False

    # =====================================================================
    # АВТОРИЗАЦИЯ
    # =====================================================================
    async def _is_authenticated_ui(self) -> bool:
        """
        Надёжная проверка авторизации ПО UI (а не только по строке URL).
        Возвращает True, если на странице присутствует элемент рабочего
        интерфейса портала (меню/ссылка «Поиск грузов»).
        """
        try:
            # Ссылка на биржу грузов есть только у авторизованного пользователя.
            offers_link = self.page.locator('a[href*="/exchange/offers"]').first
            if await offers_link.count() > 0:
                return True
            # Уже находимся на странице биржи и видим форму фильтров.
            submit_btn = self.page.locator('button[data-ctx="basicFilters.form.submit"]').first
            if await submit_btn.count() > 0:
                return True
        except Exception:
            pass
        return False

    async def login(self) -> bool:
        """
        Вход в Trans.eu.

        Шаг 0: определить состояние сессии (URL + проверка по UI).
        Шаг 1: goto https://platform.trans.eu (редирект на auth.).
        Шаг 2: заполнить логин/пароль из настроек.
        Шаг 3: нажать «Вход» (button[type="submit"]).
        Шаг 4: дождаться /trans-info.
        Шаг 5: перейти на /exchange/offers через меню.

        Защита от цикла: не более _MAX_LOGIN_ATTEMPTS неудачных попыток подряд.
        """
        await self._ensure_started()

        _dbg(
            "login() called",
            {
                "user": (settings.TRANS_EU_USERNAME[:3] + "***") if settings.TRANS_EU_USERNAME else "(empty)",
                "has_password": bool(settings.TRANS_EU_PASSWORD),
                "failed_logins": self._failed_logins,
            },
            "H-E",
        )

        if not settings.TRANS_EU_USERNAME or not settings.TRANS_EU_PASSWORD:
            logger.error("Учётные данные Trans.eu не заданы в настройках.")
            return False

        if self._failed_logins >= _MAX_LOGIN_ATTEMPTS:
            logger.error(
                f"Достигнут лимит неудачных логинов ({_MAX_LOGIN_ATTEMPTS}). "
                "Прерывание во избежание блокировки аккаунта. Проверьте учётные "
                "данные / решите капчу вручную и сбросьте счётчик перезапуском."
            )
            return False

        try:
            current_url = self.page.url
            logger.info(f"login() — Шаг 0. Текущий URL: {current_url}")

            # Первичная инициализация: применяем сохранённые куки.
            if current_url == "about:blank" or not current_url:
                logger.info(f"URL пуст. Переход на {_START_URL} для инициализации сессии...")
                await self.page.goto(_START_URL, timeout=_T_NAV)
                await self.page.wait_for_timeout(_T_SHORT)
                await self._wait_for_cloudflare_if_present()
                current_url = self.page.url

            # Сессия сброшена (/logout) — чистим куки.
            if "/logout" in current_url:
                logger.info("URL = /logout. Очищаем куки и переходим заново...")
                await self.context.clear_cookies()
                await self.page.goto(_START_URL, timeout=_T_NAV)
                await self.page.wait_for_timeout(_T_SHORT)
                await self._wait_for_cloudflare_if_present()
                current_url = self.page.url

            # --- Шаг 0: определение состояния ---
            on_offers = "platform.trans.eu/exchange/offers" in current_url
            on_portal = (
                "platform.trans.eu" in current_url
                and "auth.platform.trans.eu" not in current_url
                and "/login" not in current_url
                and "/logout" not in current_url
            )

            # Уже на бирже + UI подтверждает авторизацию.
            if on_offers and await self._is_authenticated_ui():
                logger.info("Шаг 0: уже на странице биржи и авторизованы.")
                self._failed_logins = 0
                return True

            # На портале (не auth/login) + UI подтверждает авторизацию.
            if on_portal and await self._is_authenticated_ui():
                logger.info("Шаг 0: авторизованы (UI подтверждён). Переход через меню.")
                if await self._navigate_to_offers_via_menu():
                    self._failed_logins = 0
                    return True
                # если переход не удался — провалимся в полный логин ниже

            # --- Шаг 1: переход на страницу авторизации ---
            logger.info("Шаг 0: не авторизованы. Запуск полной процедуры логина.")
            if "auth.platform.trans.eu" not in current_url and "/login" not in current_url:
                await self.page.goto(_START_URL, timeout=_T_NAV)
                await self.page.wait_for_timeout(_T_SHORT)

            await self._wait_for_cloudflare_if_present()

            # --- Шаг 2: поля логина/пароля ---
            login_selector = 'input[name="login"]'
            password_selector = 'input[name="password"]'
            try:
                await self.page.wait_for_selector(login_selector, timeout=_T_ELEMENT)
            except Exception:
                login_selector = '[aria-label="TransID"]'
                await self.page.wait_for_selector(login_selector, timeout=_T_ELEMENT)
            try:
                await self.page.wait_for_selector(password_selector, timeout=5000)
            except Exception:
                password_selector = '[aria-label="Пароль"]'

            logger.info("Шаг 2: заполняю TransID и пароль.")
            await self.page.fill(login_selector, settings.TRANS_EU_USERNAME)
            await self.page.fill(password_selector, settings.TRANS_EU_PASSWORD)
            try:
                await self.page.screenshot(path="/tmp/debug_before_submit.png")
            except Exception:
                pass

            # --- Шаг 3: submit ---
            logger.info("Шаг 3: нажимаю «Вход».")
            await self.page.click('button[type="submit"]')

            # --- Шаг 4: ждём /trans-info ---
            logger.info("Шаг 4: ожидание редиректа на /trans-info.")
            try:
                await self.page.wait_for_url("**/trans-info**", timeout=30000)
            except Exception:
                if await self._wait_for_cloudflare_if_present():
                    await self.page.wait_for_url("**/trans-info**", timeout=30000)
                else:
                    self._failed_logins += 1
                    logger.error(
                        f"LOGIN_FAILED: нет редиректа на /trans-info. URL: {self.page.url}. "
                        f"Неудачных попыток: {self._failed_logins}/{_MAX_LOGIN_ATTEMPTS}."
                    )
                    try:
                        await self.page.screenshot(path="/tmp/debug_login_failed.png")
                    except Exception:
                        pass
                    return False

            # --- Шаг 5: меню → /exchange/offers ---
            if await self._navigate_to_offers_via_menu():
                self._failed_logins = 0
                self._backup_storage_state()  # фиксируем удачную сессию
                return True

            self._failed_logins += 1
            return False

        except Exception as e:
            self._failed_logins += 1
            logger.error(f"Login/Navigation failed: {e} (попытка {self._failed_logins}/{_MAX_LOGIN_ATTEMPTS})")
            try:
                await self.page.screenshot(path="/tmp/debug_login_failed.png")
            except Exception:
                pass
            return False

    async def _navigate_to_offers_via_menu(self) -> bool:
        """
        Шаг 5: найти ссылку «Поиск грузов» в меню и перейти на /exchange/offers.
        """
        try:
            await self._wait_for_cloudflare_if_present()
            logger.info("Шаг 5: ожидание ссылки «Поиск грузов».")
            await self.page.wait_for_selector('a[href*="/exchange/offers"]', timeout=_T_ELEMENT)

            # Попытка закрыть перекрывающее модальное окно.
            modal_selectors = [
                'div[data-ctx="modals-region"]',
                'div[class*="_qpnf86_b_d"]',
                "div.qIODY8rrX08nnWOcOFtA",
            ]
            for sel in modal_selectors:
                try:
                    modal = self.page.locator(sel).first
                    if await modal.is_visible(timeout=500):
                        await self.page.keyboard.press("Escape")
                        await self.page.wait_for_timeout(1000)
                        close_btn = modal.locator(
                            'button:has-text("Close"), button:has-text("Закрыть"), '
                            'button:has-text("Accept"), button:has-text("Принять")'
                        ).first
                        if await close_btn.is_visible(timeout=500):
                            await close_btn.click()
                            await self.page.wait_for_timeout(1000)
                except Exception:
                    pass

            logger.info("Шаг 5: нажимаю «Поиск грузов».")
            try:
                await self.page.click('a[href*="/exchange/offers"]', timeout=10000)
            except Exception:
                await self._wait_for_cloudflare_if_present()
                await self.page.click('a[href*="/exchange/offers"]', force=True)

            try:
                await self.page.wait_for_url("**/exchange/offers**", timeout=_T_ELEMENT)
            except Exception as url_err:
                if await self._wait_for_cloudflare_if_present():
                    await self.page.click('a[href*="/exchange/offers"]', force=True)
                    await self.page.wait_for_url("**/exchange/offers**", timeout=_T_ELEMENT)
                else:
                    raise url_err

            logger.info(f"Шаг 5: открыта страница биржи. URL: {self.page.url}")
            return True
        except Exception as e:
            logger.error(f"Шаг 5: не удалось перейти на /exchange/offers: {e}")
            try:
                await self.page.screenshot(path="/tmp/debug_menu_navigation_failed.png")
            except Exception:
                pass
            return False

    # =====================================================================
    # ПОИСК ГРУЗОВ
    # =====================================================================
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
        unloading_radius: int = 75,
    ):
        """
        Выполняет полный сценарий поиска со всеми фильтрами.
        Возвращает список замапленных предложений (list) или False при ошибке.
        """
        try:
            await self._ensure_started()

            # ПРАВИЛО: сначала авторизация на портале, только потом скрапинг.
            if not await self.login():
                raise Exception("Пользователь не авторизован на портале Trans.eu.")

            # --- 0. Валидация дат (строгая) ---
            from datetime import datetime, timedelta

            def parse_dt(d_str):
                if not d_str:
                    return None
                try:
                    return datetime.strptime(d_str, "%d.%m.%Y")
                except ValueError:
                    logger.error(f"Неверный формат даты: {d_str}")
                    return None

            if not date_from:
                date_from = datetime.now().strftime("%d.%m.%Y")
            if not date_to:
                date_to = date_from
            if not unloading_date_from:
                ld_to_dt = parse_dt(date_to) or datetime.now()
                unloading_date_from = (ld_to_dt + timedelta(days=1)).strftime("%d.%m.%Y")
            if not unloading_date_to:
                unloading_date_to = unloading_date_from

            ld_from = parse_dt(date_from)
            ld_to = parse_dt(date_to)
            ud_from = parse_dt(unloading_date_from)
            ud_to = parse_dt(unloading_date_to)
            now_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

            if ld_from and ld_from < now_date:
                raise ValueError(f"Дата загрузки (с) {date_from} не может быть в прошлом.")
            if ld_from and ld_to and ld_from > ld_to:
                raise ValueError(f"Дата загрузки: с ({date_from}) > по ({date_to})")
            if ud_from and ud_to and ud_from > ud_to:
                raise ValueError(f"Дата выгрузки: с ({unloading_date_from}) > по ({unloading_date_to})")
            if ld_to:
                if ud_from and ud_from < ld_to:
                    raise ValueError(
                        f"Бизнес-правило: дата выгрузки (с) {unloading_date_from} "
                        f"должна быть >= даты загрузки (по) {date_to}"
                    )
                if ud_to and ud_to < ld_to:
                    raise ValueError(
                        f"Бизнес-правило: дата выгрузки (по) {unloading_date_to} "
                        f"должна быть >= даты загрузки (по) {date_to}"
                    )

            logger.info("Инициализация сценария поиска...")

            # --- STEP 0: переход на страницу поиска ---
            logger.info(f"Навигация на страницу поиска: {_OFFERS_URL}")
            await self.page.goto(_OFFERS_URL, timeout=_T_NAV, wait_until="domcontentloaded")
            try:
                await self.page.wait_for_selector(
                    'button[data-ctx="basicFilters.form.submit"]', state="attached", timeout=30000
                )
                logger.info("Страница поиска загружена (кнопка submit в DOM).")
            except Exception as nav_err:
                logger.error(f"Страница поиска не загрузилась: {nav_err}")
                raise Exception(f"Страница поиска Trans.eu не загрузилась: {nav_err}")

            await self.page.wait_for_timeout(2000)

            # --- РАЗВЕРНУТЬ ФИЛЬТРЫ (до заполнения полей) ---
            loading_field = self.page.locator('div[data-ctx="place-loading_place-0"] input').first
            already_expanded = False
            try:
                if await loading_field.is_visible(timeout=1000):
                    already_expanded = True
                    logger.info("Фильтры уже развёрнуты.")
            except Exception:
                pass

            expand_step1_selectors = [
                'button:has-text("РАЗВЕРНУТЬ ФИЛЬТРЫ")',
                'button:has-text("Развернуть фильтры")',
                'button:has-text("EXPAND FILTERS")',
                'button:has-text("Expand filters")',
                'button[data-ctx="basic-filters-form-hide-filters-preview"]',
            ]
            more_filters_selectors = [
                'button:has-text("БОЛЬШЕ ФИЛЬТРОВ")',
                'button:has-text("Больше фильтров")',
                'button:has-text("MORE FILTERS")',
                'button:has-text("More filters")',
            ]

            async def _expand_filters():
                for selector in expand_step1_selectors:
                    try:
                        btn = self.page.locator(selector).first
                        if await btn.is_visible(timeout=2000):
                            logger.info(f"Развернуть фильтры: {selector}")
                            await btn.click(force=True)
                            await self.page.wait_for_timeout(2000)
                            break
                    except Exception:
                        continue
                for selector in more_filters_selectors:
                    try:
                        btn = self.page.locator(selector).first
                        if await btn.is_visible(timeout=2000):
                            logger.info(f"Больше фильтров: {selector}")
                            await btn.click(force=True)
                            await self.page.wait_for_timeout(2000)
                            break
                    except Exception:
                        continue

            if not already_expanded:
                await _expand_filters()

            try:
                await self.page.wait_for_selector(
                    'div[data-ctx="place-loading_place-0"] input', state="visible", timeout=10000
                )
                logger.info("Поле места загрузки видимо.")
            except Exception:
                logger.warning("Поле загрузки не видно. Проверяем Cloudflare...")
                if await self._wait_for_cloudflare_if_present():
                    await _expand_filters()
                    await self.page.wait_for_selector(
                        'div[data-ctx="place-loading_place-0"] input', state="visible", timeout=_T_ELEMENT
                    )
                else:
                    try:
                        await self.page.screenshot(path="/tmp/debug_filters_not_expanded.png")
                    except Exception:
                        pass
                    raise Exception("Капча Cloudflare не решена. Поиск прерван.")

            # --- Очистка фильтров ---
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
                        await btn.click()
                        await self.page.wait_for_timeout(1000)
                        break
            except Exception as e:
                logger.warning(f"Не удалось очистить фильтры (игнорируется): {e}")

            logger.info(f"Старт поиска: {loading_location} -> {unloading_location}")

            # --- 1. Место загрузки ---
            await self._set_location_field(
                'div[data-ctx="place-loading_place-0"]', loading_location, radius=loading_radius
            )

            # --- 2. Место выгрузки ---
            if unloading_location and unloading_location.strip():
                await self._set_location_field(
                    'div[data-ctx="place-unloading_place-0"]', unloading_location, radius=unloading_radius
                )
            else:
                logger.info("Место выгрузки не задано, пропускаем.")

            # --- 3. Даты ---
            adv_filters = self.page.locator('div[data-ctx="advanced-filters"]')
            await self._set_date_input(adv_filters, "to", 1, unloading_date_to)
            await self._set_date_input(adv_filters, "from", 1, unloading_date_from)
            await self._set_date_input(adv_filters, "to", 0, date_to)
            await self._set_date_input(adv_filters, "from", 0, date_from)

            # --- 4. Вес ---
            if weight_to:
                logger.info(f"Вес (до): {weight_to}")
                weight_input = self.page.locator('div[data-ctx="load_weight.valueTo"] input')
                if await weight_input.count() > 0:
                    await weight_input.click()
                    await weight_input.fill(weight_to)
                else:
                    logger.warning("Поле веса не найдено по data-ctx.")

            # --- 5. LDM (левое поле «С» = 4.8 по спецификации) ---
            logger.info("LDM (с) = 4.8 по спецификации.")
            ldm_labels = [
                "Длина (погрузочные метры)", "Погрузочные метры", "LDM",
                "Loading meters", "Długość ładunkowa", "Load meters",
            ]
            ldm_from_set = False
            for ctx in (adv_filters, self.page):
                if ldm_from_set:
                    break
                for label in ldm_labels:
                    try:
                        label_el = ctx.locator(f"label:has-text('{label}')").first
                        if await label_el.count() > 0 and await label_el.is_visible():
                            container = label_el.locator("..")
                            inputs = container.locator("input")
                            if await inputs.count() < 1:
                                container = container.locator("..")
                                inputs = container.locator("input")
                            if await inputs.count() >= 1:
                                inp = inputs.nth(0)
                                if await inp.is_visible():
                                    for val in ("4.8", "4,8"):
                                        await inp.click()
                                        await self.page.keyboard.press("Control+A")
                                        await self.page.keyboard.press("Backspace")
                                        await inp.fill(val)
                                        await inp.press("Tab")
                                        await self.page.wait_for_timeout(500)
                                        if "4" in (await inp.input_value()):
                                            logger.info(f"LDM (с) = {val} через '{label}'")
                                            ldm_from_set = True
                                            break
                                if ldm_from_set:
                                    break
                    except Exception:
                        pass
            if not ldm_from_set:
                logger.warning("Поле LDM (с) не найдено — панель «БОЛЬШЕ ФИЛЬТРОВ» может быть закрыта.")

            # --- 5b. LDM правое поле «До» (из параметра) ---
            if length_to:
                logger.info(f"LDM (до): {length_to}")
                length_set = False
                for ctx in (adv_filters, self.page):
                    if length_set:
                        break
                    for label in ldm_labels:
                        try:
                            label_el = ctx.locator(f"label:has-text('{label}')").first
                            if await label_el.count() > 0 and await label_el.is_visible():
                                container = label_el.locator("..")
                                inputs = container.locator("input")
                                if await inputs.count() < 2:
                                    container = container.locator("..")
                                    inputs = container.locator("input")
                                if await inputs.count() >= 2:
                                    target = inputs.nth(1)
                                    if await target.is_visible():
                                        val_str = str(length_to)
                                        for val in (val_str, val_str.replace(".", ",")):
                                            await target.click()
                                            await self.page.keyboard.press("Control+A")
                                            await self.page.keyboard.press("Backspace")
                                            await target.fill(val)
                                            await target.press("Tab")
                                            await self.page.wait_for_timeout(500)
                                            if (await target.input_value()) == val:
                                                logger.info(f"LDM (до) = {val} через '{label}'")
                                                length_set = True
                                                break
                                    if length_set:
                                        break
                        except Exception:
                            pass
                if not length_set:
                    for ctx_name in ("load_ldm.valueTo", "load_meter.valueTo", "load_length.valueTo"):
                        inp = self.page.locator(f'div[data-ctx="{ctx_name}"] input').first
                        if await inp.count() > 0 and await inp.is_visible():
                            await inp.click()
                            await self.page.keyboard.press("Control+A")
                            await self.page.keyboard.press("Backspace")
                            await inp.fill(str(length_to))
                            length_set = True
                            break
                if not length_set:
                    logger.warning("Поле LDM (до) не найдено.")

            # --- 6. Поиск ---
            logger.info("Нажимаю «Искать».")
            search_btn = self.page.locator('button[data-ctx="basicFilters.form.submit"]')
            await search_btn.click()
            await self.page.wait_for_timeout(8000)

            try:
                await self.page.screenshot(path="/tmp/search_results.png")
                with open("/tmp/search_results.html", "w", encoding="utf-8") as f:
                    f.write(await self.page.content())
            except Exception as debug_err:
                logger.warning(f"Не удалось сохранить отладочные файлы: {debug_err}")

            # --- 7. Извлечение и маппинг ---
            logger.info("Извлечение результатов...")
            from backend.src.infrastructure.external_services.trans_eu import parser, mapper

            raw_offers = await self.page.evaluate(parser.get_extraction_script())
            logger.info(f"Извлечено сырых элементов: {len(raw_offers)}")

            results = []
            for raw in raw_offers:
                try:
                    results.append(mapper.map_to_cargo(raw))
                except Exception as map_err:
                    logger.warning(f"Не удалось замапить элемент: {map_err}")

            logger.info(f"Успешно замаплено предложений: {len(results)}")
            return results

        except Exception as e:
            logger.error(f"Поиск не удался: {e}")
            try:
                await self.page.screenshot(path="/tmp/search_failed.png")
            except Exception:
                pass
            return False

    # =====================================================================
    # ВВОД ДАТЫ ЧЕРЕЗ КАЛЕНДАРЬ
    # =====================================================================
    async def _set_date_input(self, parent_locator, name: str, index: int, value: str):
        """Устанавливает дату через навигацию по календарю. Формат: DD.MM.YYYY."""
        try:
            inp = parent_locator.locator(f'input[name="{name}"]').nth(index)
            if await inp.count() == 0:
                logger.warning(f"Поле даты {name}[{index}] не найдено.")
                return

            await inp.scroll_into_view_if_needed()

            if not value:
                logger.info(f"Очистка даты {name}[{index}]")
                await inp.click()
                await self.page.keyboard.press("Control+A")
                await self.page.keyboard.press("Backspace")
                await self.page.keyboard.press("Escape")
                return

            logger.info(f"Установка даты {name}[{index}]: {value}")
            try:
                target_day, target_month, target_year = map(int, value.split("."))
                target_iso = f"{target_year}-{target_month:02d}-{target_day:02d}"
            except ValueError:
                logger.error(f"Неверный формат даты: {value} (ожидается DD.MM.YYYY)")
                return

            await inp.click()
            header_btn = self.page.locator('button[data-ctx="switch-mode"]')
            try:
                await header_btn.wait_for(state="visible", timeout=3000)
            except Exception:
                await inp.click(force=True)
                await header_btn.wait_for(state="visible", timeout=3000)

            months_map = {
                "январь": 1, "февраль": 2, "март": 3, "апрель": 4, "май": 5, "июнь": 6,
                "июль": 7, "август": 8, "сентябрь": 9, "октябрь": 10, "ноябрь": 11, "декабрь": 12,
                "january": 1, "february": 2, "march": 3, "april": 4, "may": 5, "june": 6,
                "july": 7, "august": 8, "september": 9, "october": 10, "november": 11, "december": 12,
            }

            for _ in range(24):
                header_text = (await header_btn.text_content() or "").lower().strip()
                parts = header_text.split()
                if len(parts) < 2:
                    break
                current_month = months_map.get(parts[0])
                current_year = int(parts[-1]) if parts[-1].isdigit() else 0
                if current_month is None or current_year == 0:
                    logger.warning(f"Не удалось разобрать заголовок календаря: {header_text}")
                    break
                if current_year == target_year and current_month == target_month:
                    break
                go_next = (target_year > current_year) or (
                    target_year == current_year and target_month > current_month
                )
                nav_sel = 'button[data-ctx="switch-next-page"]' if go_next else 'button[data-ctx="switch-prev-page"]'
                await self.page.locator(nav_sel).click()
                await self.page.wait_for_timeout(200)

            day_wrapper = self.page.locator(f'div[data-ctx-id="{target_iso}-wrapper"]')
            if await day_wrapper.count() > 0:
                logger.info(f"Выбор дня: {target_iso}")
                await day_wrapper.click()
            else:
                logger.warning(f"Обёртка дня {target_iso} не найдена. Фоллбэк по тексту '{target_day}'.")
                valid_day = (
                    self.page.locator(
                        'div[data-ctx="option-wrapper"]:not([class*="_1d3i7nl_jh_g"]) div._1d3i7nl_jh_e'
                    )
                    .filter(has_text=f"^{target_day}$")
                    .first
                )
                if await valid_day.count() > 0:
                    await valid_day.click()
                else:
                    logger.error("Ячейка дня не найдена.")

            await self.page.wait_for_timeout(500)
            await self.page.keyboard.press("Escape")

        except Exception as e:
            logger.error(f"Ошибка установки даты {name} через календарь: {e}")

    # =====================================================================
    # ВВОД МЕСТА (5-шаговая стратегия)
    # =====================================================================
    async def _set_location_field(self, container_selector: str, value: str, radius: int = 0):
        """
        Установка места по строгой 5-шаговой стратегии:
          1) {ISO}, {Index}, {City} (EN)
          2) {ISO}, {City} (EN)
          3) {City} (EN)
          4) {City} (RU)
          5) {ISO}, {City} (RU)
        Успех = появление модального окна с вариантами и выбор лучшего.
        """
        try:
            import re

            logger.info(f"Установка места в {container_selector}: '{value}'")
            container = self.page.locator(container_selector)
            try:
                await container.wait_for(state="attached", timeout=_T_ELEMENT)
                await container.locator("input").first.wait_for(state="visible", timeout=_T_ELEMENT)
            except Exception as wait_err:
                logger.warning(f"Поле места не видно. Проверяем Cloudflare... ({wait_err})")
                if await self._wait_for_cloudflare_if_present():
                    await container.wait_for(state="attached", timeout=_T_ELEMENT)
                    await container.locator("input").first.wait_for(state="visible", timeout=_T_ELEMENT)
                else:
                    raise Exception("Капча Cloudflare не решена. Ввод места прерван.")

            parts = [p.strip() for p in value.split(",")]
            iso = zip_code = city_en = ""

            if len(parts) == 1:
                if re.match(r"^[A-Z]{2}$", parts[0]):
                    iso = parts[0]
                elif re.search(r"\d", parts[0]):
                    zip_code = parts[0]
                else:
                    city_en = parts[0]
            elif len(parts) == 2:
                if len(parts[0]) == 2 and parts[0].isupper():
                    iso, city_en = parts[0], parts[1]
                    if re.search(r"\d", city_en):
                        m = re.match(r"^([\d\s-]+)\s+(.+)$", city_en.strip())
                        if m:
                            zip_code, city_en = m.group(1).strip(), m.group(2).strip()
                        else:
                            zip_code, city_en = city_en, ""
                else:
                    city_en, iso = parts[0], parts[1]
            elif len(parts) >= 3:
                iso, zip_code, city_en = parts[0], parts[1], parts[2]

            ru_map = {
                "Berlin": "Берлин", "Warszawa": "Варшава", "Prague": "Прага",
                "Bratislava": "Братислава", "Dietfurt": "Дитфурт", "Šamorín": "Шаморин",
            }
            city_ru = ru_map.get(city_en, city_en)

            attempts = []
            if iso and zip_code and city_en:
                attempts.append(f"{iso}, {zip_code}, {city_en}")
            elif iso and zip_code:
                attempts.append(f"{iso}, {zip_code}")
            if zip_code and city_en:
                attempts.append(f"{zip_code} {city_en}")
                attempts.append(f"{city_en}, {zip_code}")
            if iso and city_en:
                attempts.append(f"{iso}, {city_en}")
            if city_en:
                attempts.append(city_en)
            elif zip_code and not attempts:
                attempts.append(zip_code)
            elif iso and not attempts:
                attempts.append(iso)
            if city_ru:
                attempts.append(city_ru)
            if iso and city_ru:
                attempts.append(f"{iso}, {city_ru}")

            seen = set()
            attempts = [x for x in attempts if x and not (x in seen or seen.add(x))]

            modal_selector = 'div#mainRegionDropdowns span[class*="Option__option"]'
            input_el = container.locator("input").first
            success = False

            for i, attempt in enumerate(attempts):
                step_num = i + 1
                logger.info(f"Место, шаг {step_num}: '{attempt}'")

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

                try:
                    await self.page.wait_for_selector(modal_selector, timeout=8000)
                    options = self.page.locator(modal_selector)
                    count = await options.count()
                    if count == 0:
                        raise Exception("Нет вариантов в выпадающем списке")

                    best_index, longest = 0, 0
                    for idx in range(count):
                        text = await options.nth(idx).text_content()
                        tlen = len(text.strip()) if text else 0
                        if tlen > longest:
                            longest, best_index = tlen, idx

                    await options.nth(best_index).click(force=True)
                    logger.info(f"Место выбрано на шаге {step_num}: '{attempt}'")
                    success = True
                    break
                except Exception:
                    logger.warning(f"Модальное окно не появилось на шаге {step_num} ('{attempt}').")
                    continue

            if not success:
                logger.error(f"Не удалось установить место '{value}' после всех шагов.")
                raise ValueError(f"Выбор места не удался: {value}")

            if radius > 0:
                await self.page.wait_for_timeout(1000)
                range_input = container.locator('input[name="range"]').first
                try:
                    if await range_input.count() > 0 and await range_input.is_visible(timeout=1000):
                        logger.info(f"Радиус: {radius} км")
                        await range_input.click(force=True)
                        await range_input.fill(str(radius))
                        await self.page.keyboard.press("Enter")
                        await self.page.wait_for_timeout(500)
                except Exception as ex:
                    logger.info(f"Поле радиуса недоступно ({ex}). Пропускаем.")

        except Exception as e:
            logger.error(f"Ошибка в _set_location_field: {e}")
            try:
                await self.page.screenshot(path="/tmp/location_error.png")
            except Exception:
                pass
            raise e
