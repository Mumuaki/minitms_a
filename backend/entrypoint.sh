#!/bin/bash
export DISPLAY=:99

# Cleanup stale X11 locks from previous runs to prevent Xvfb crash on container restart
rm -rf /tmp/.X99-lock /tmp/.X11-unix/X99

# X authority so x11vnc can connect to Xvfb
AUTH_FILE=/tmp/xvfb.auth
touch "$AUTH_FILE"
COOKIE=$(python3 -c "import secrets; print(secrets.token_hex(16))")
xauth -f "$AUTH_FILE" add :99 . "$COOKIE"
chmod 600 "$AUTH_FILE"

# Start virtual display (1920x1080, 24-bit color)
Xvfb :99 -screen 0 1920x1080x24 -ac -auth "$AUTH_FILE" &
sleep 2

# Start VNC server on the virtual display (no password, shared)
x11vnc -display :99 -auth "$AUTH_FILE" -forever -nopw -shared -rfbport 5900 -bg -o /tmp/x11vnc.log
sleep 1

# Start noVNC web proxy (browser access at port 6080)
websockify --web /opt/novnc 6080 localhost:5900 &

echo "=== noVNC ready at http://0.0.0.0:6080 ==="

echo "=== Applying database migrations ==="
# Запуск из корня проекта, alembic.ini должен быть доступен
alembic upgrade head

echo "=== Ensuring administrator account ==="
if [ -d "/app/backend" ]; then
    python3 /app/backend/create_admin.py
else
    python3 create_admin.py
fi

# Start the FastAPI application
# docker-compose mounts project to /app, standalone build uses /workspace
if [ -d "/app/backend" ]; then
    cd /app
    exec uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
else
    exec uvicorn main:app --host 0.0.0.0 --port 8000 --reload
fi

