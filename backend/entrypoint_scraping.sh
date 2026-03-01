#!/bin/bash
# entrypoint_scraping.sh — Scraping Worker (Playwright + Xvfb + noVNC)
# Запускает: Xvfb → x11vnc → noVNC → uvicorn main_scraping
set -e

export DISPLAY=:99

# Очистка старых X11-локов от предыдущих запусков
rm -rf /tmp/.X99-lock /tmp/.X11-unix/X99

# X authority — чтобы x11vnc мог подключиться к Xvfb
AUTH_FILE=/tmp/xvfb.auth
touch "$AUTH_FILE"
COOKIE=$(python3 -c "import secrets; print(secrets.token_hex(16))")
xauth -f "$AUTH_FILE" add :99 . "$COOKIE"
chmod 600 "$AUTH_FILE"

echo "=== [scraping-worker] Starting Xvfb virtual display ==="
Xvfb :99 -screen 0 1920x1080x24 -ac -auth "$AUTH_FILE" &
sleep 2

echo "=== [scraping-worker] Starting x11vnc (VNC server) ==="
x11vnc -display :99 -auth "$AUTH_FILE" -forever -nopw -shared -rfbport 5900 -bg -o /tmp/x11vnc.log
sleep 1

echo "=== [scraping-worker] Starting noVNC web proxy on port 6080 ==="
websockify --web /opt/novnc 6080 localhost:5900 &

echo "=== [scraping-worker] noVNC ready at http://0.0.0.0:6080 ==="

echo "=== [scraping-worker] Starting uvicorn on port 8003 ==="
exec uvicorn backend.main_.main_scraping:app --host 0.0.0.0 --port 8003
