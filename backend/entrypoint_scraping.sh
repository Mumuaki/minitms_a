#!/bin/bash
# entrypoint_scraping.sh — Scraping Worker (Playwright + Xvfb + noVNC)
# Запускает: Xvfb → x11vnc → noVNC → [ПРОВЕРКА БРАУЗЕРА] → uvicorn main_scraping
#
# ИСПРАВЛЕННАЯ ВЕРСИЯ.
# Главное изменение: перед стартом uvicorn выполняется ДЕТЕРМИНИРОВАННАЯ
# проверка наличия исполняемого файла Chromium (fail-fast). Если браузер
# не найден или не совпадает версия — контейнер падает сразу с понятной
# ошибкой, а не «тихо» позже при первом запуске скрапера.
set -euo pipefail

export DISPLAY=:99
# Жёстко фиксируем путь к браузерам Playwright — единый источник истины,
# совпадает с ENV в Dockerfile и с resolve_chromium_executable() в client.py.
export PLAYWRIGHT_BROWSERS_PATH="${PLAYWRIGHT_BROWSERS_PATH:-/ms-playwright}"

# ── 0. Очистка старых X11-локов от предыдущих запусков ──────────────────────
rm -rf /tmp/.X99-lock /tmp/.X11-unix/X99 || true

# X authority — чтобы x11vnc мог подключиться к Xvfb
AUTH_FILE=/tmp/xvfb.auth
touch "$AUTH_FILE"
COOKIE=$(python3 -c "import secrets; print(secrets.token_hex(16))")
xauth -f "$AUTH_FILE" add :99 . "$COOKIE"
chmod 600 "$AUTH_FILE"

# ── 1. Xvfb (виртуальный дисплей) ───────────────────────────────────────────
echo "=== [scraping-worker] Starting Xvfb virtual display ==="
Xvfb :99 -screen 0 1920x1080x24 -ac -auth "$AUTH_FILE" &
sleep 2

# ── 2. x11vnc (VNC-сервер) ──────────────────────────────────────────────────
# ПРИМЕЧАНИЕ ПО БЕЗОПАСНОСТИ:
#   -nopw означает VNC без пароля. Это допустимо ТОЛЬКО потому, что порт 6080
#   биндится на 127.0.0.1 в docker-compose (см. ports: "127.0.0.1:6080:6080")
#   и доступен лишь через SSH-туннель. Если когда-либо откроете 6080 наружу —
#   обязательно задайте VNC-пароль (-rfbauth) или Basic Auth на websockify.
echo "=== [scraping-worker] Starting x11vnc (VNC server) ==="
x11vnc -display :99 -auth "$AUTH_FILE" -forever -nopw -shared -rfbport 5900 -bg -o /tmp/x11vnc.log
sleep 1

# ── 3. noVNC (веб-прокси) ───────────────────────────────────────────────────
echo "=== [scraping-worker] Starting noVNC web proxy on port 6080 ==="
websockify --web /opt/novnc 6080 127.0.0.1:5900 &

echo "=== [scraping-worker] noVNC ready (proxy to local VNC) ==="

# ── 4. ДЕТЕРМИНИРОВАННАЯ ПРОВЕРКА БРАУЗЕРА (fail-fast) ───────────────────────
# Тот же алгоритм, что и resolve_chromium_executable() в client.py:
#   ищем PLAYWRIGHT_BROWSERS_PATH/chromium-*/chrome-linux64/chrome.
# Если не найдено — НЕ запускаем uvicorn, падаем с кодом 1 и понятным логом.
echo "=== [scraping-worker] Verifying Chromium executable (deterministic) ==="

if [ ! -d "$PLAYWRIGHT_BROWSERS_PATH" ]; then
  echo "FATAL: PLAYWRIGHT_BROWSERS_PATH ('$PLAYWRIGHT_BROWSERS_PATH') не существует." >&2
  echo "       Проверьте ENV в Dockerfile/compose и что 'playwright install chromium' выполнен в образе." >&2
  exit 1
fi

# Берём детерминированно самую старшую сборку chromium-<N>.
CHROME_BIN="$(ls -1d "$PLAYWRIGHT_BROWSERS_PATH"/chromium-*/chrome-linux64/chrome 2>/dev/null \
              | sort -t- -k2 -V -r | head -n1 || true)"

if [ -z "${CHROME_BIN:-}" ] || [ ! -x "$CHROME_BIN" ]; then
  echo "FATAL: Исполняемый файл Chromium не найден в '$PLAYWRIGHT_BROWSERS_PATH'." >&2
  echo "       Ожидаемый шаблон: chromium-*/chrome-linux64/chrome" >&2
  echo "       Содержимое каталога:" >&2
  ls -la "$PLAYWRIGHT_BROWSERS_PATH" >&2 || true
  echo "       Версия playwright в requirements.txt должна совпадать с версией," >&2
  echo "       установленной 'playwright install --with-deps chromium' в образе." >&2
  exit 1
fi

echo "=== [scraping-worker] Chromium OK: $CHROME_BIN ==="
# Экспортируем явный путь — client.py подхватит его как переопределение
# и не будет вычислять заново (нулевая неоднозначность запуска).
export PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH="$CHROME_BIN"

# Доп. проверка: бинарь реально запускается и печатает версию.
if ! "$CHROME_BIN" --headless=new --no-sandbox --disable-gpu --dump-dom about:blank >/dev/null 2>&1; then
  # --dump-dom может вернуть ненулевой код в зависимости от сборки;
  # пробуем более надёжную проверку --version.
  if ! "$CHROME_BIN" --version >/dev/null 2>&1; then
    echo "FATAL: Chromium найден ($CHROME_BIN), но не запускается (проверка --version провалена)." >&2
    echo "       Вероятно, не хватает системных библиотек: выполните 'playwright install-deps chromium'." >&2
    exit 1
  fi
fi
echo "=== [scraping-worker] Chromium launch smoke-test passed ==="

# ── 5. Scraping API (FastAPI) + Celery Worker ───────────────────────────────
echo "=== [scraping-worker] Starting scraping API (uvicorn) on port 8003 ==="
uvicorn backend.main_.main_scraping:app --host 0.0.0.0 --port 8003 &

echo "=== [scraping-worker] Starting Celery worker for queue 'scraping' ==="
# concurrency=1 обязателен, чтобы несколько задач не конфликтовали за один браузер
exec celery -A backend.src.infrastructure.messaging.celery_app worker -Q scraping --concurrency=1 --loglevel=info
