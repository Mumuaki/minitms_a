# Dockerfile для Backend (FastAPI)
FROM python:3.11-slim

# Установка переменных окружения
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    DISPLAY=:99

# Установка системных зависимостей + виртуальный дисплей + VNC для видимого браузера
RUN apt-get update && apt-get install -y \
    postgresql-client \
    gcc \
    xvfb \
    x11vnc \
    xauth \
    procps \
    && pip install websockify \
    && rm -rf /var/lib/apt/lists/*

# noVNC — веб-клиент для просмотра браузера из обычного браузера
RUN mkdir -p /opt/novnc \
    && python3 -c "import urllib.request; urllib.request.urlretrieve('https://github.com/novnc/noVNC/archive/refs/tags/v1.5.0.tar.gz', '/tmp/novnc.tar.gz')" \
    && tar -xzf /tmp/novnc.tar.gz -C /opt/novnc --strip-components=1 \
    && rm /tmp/novnc.tar.gz \
    && ln -s /opt/novnc/vnc.html /opt/novnc/index.html

WORKDIR /workspace

COPY requirements.txt ./backend/
RUN pip install --no-cache-dir -r ./backend/requirements.txt

# Playwright: OS-level dependencies
RUN playwright install-deps chromium

COPY . ./backend/

RUN useradd -m -u 1000 appuser \
    && mkdir -p /workspace/browser_profile \
    && chown -R appuser:appuser /workspace /opt/novnc

USER appuser

# Playwright: browser binaries as appuser
RUN playwright install chromium

ENV PYTHONPATH=/workspace
WORKDIR /workspace/backend

COPY --chown=appuser:appuser entrypoint.sh /workspace/backend/entrypoint.sh
RUN sed -i 's/\r$//' /workspace/backend/entrypoint.sh && chmod +x /workspace/backend/entrypoint.sh

EXPOSE 8000 6080

ENTRYPOINT ["/workspace/backend/entrypoint.sh"]
