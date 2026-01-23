# Чеклист развертывания MiniTMS

## 1. Требования к инфраструктуре

### 1.1 Операционная система
- [ ] **Windows 10/11** (для Desktop версии) или **Linux Ubuntu 20.04+** (для Server)
- [ ] **Docker Desktop** (Windows) или **Docker Engine** (Linux)
- [ ] **Git** для клонирования репозитория

### 1.2 Серверные ресурсы (Production)
- [ ] **CPU**: минимум 4 ядра (рекомендуется 8)
- [ ] **RAM**: минимум 8 GB (рекомендуется 16 GB)
- [ ] **Диск**: минимум 50 GB SSD
- [ ] **Сеть**: стабильное подключение к интернету

### 1.3 База данных
- [ ] **PostgreSQL 14+** установлен
- [ ] База данных создана (например, `minitms_db`)
- [ ] Пользователь БД с правами CREATE, SELECT, INSERT, UPDATE, DELETE

### 1.4 Дополнительные сервисы
- [ ] **Redis** для Celery и кэширования
- [ ] **SMTP-сервер** для email (или учетные данные внешнего сервиса, например Gmail)

---

## 2. Переменные окружения

### 2.1 Backend (`backend/.env`)

```env
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/minitms_db

# Security
SECRET_KEY=your-secret-key-here
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=30

# Redis
REDIS_URL=redis://localhost:6379/0

# Trans.eu Credentials
TRANS_EU_LOGIN=your_login
TRANS_EU_PASSWORD=your_password

# OpenStreetMap / OSRM
OSM_TILE_SERVER=https://tile.openstreetmap.org/{z}/{x}/{y}.png
OSRM_SERVER=http://router.project-osrm.org
NOMINATIM_SERVER=https://nominatim.openstreetmap.org

# GPS Integration
GPS_PROVIDER=wialon  # wialon, gps-trace, navixy
GPS_API_URL=https://hst-api.wialon.com
GPS_API_TOKEN=your_gps_token

# Google Services (только для Google Sheets)
GOOGLE_CREDENTIALS_PATH=./credentials/google-service-account.json
GOOGLE_SHEET_ID=your_google_sheet_id

# Email (SMTP)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_app_password
EMAIL_FROM=your_email@gmail.com

# Celery
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Telegram (опционально)
TELEGRAM_BOT_TOKEN=your_bot_token
```

### 2.2 Frontend (`frontend/.env`)

```env
VITE_API_BASE_URL=http://localhost:8000/api/v1
VITE_OSM_TILE_SERVER=https://tile.openstreetmap.org/{z}/{x}/{y}.png
VITE_TRANS_EU_CLIENT_ID=your_client_id
```

---

## 3. Шаги по развертыванию

### 3.1 Клонирование репозитория
```bash
git clone https://github.com/Mumuaki/TMS_v1.git
cd TMS_v1
```

### 3.2 Backend Setup

#### 3.2.1 Создание виртуального окружения
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Linux/Mac
# или
venv\Scripts\activate  # Windows
```

#### 3.2.2 Установка зависимостей
```bash
pip install -r requirements.txt
```

#### 3.2.3 Установка Playwright (для скрапинга)
```bash
playwright install chromium
```

#### 3.2.4 Настройка переменных окружения
```bash
cp .env.example .env
# Отредактировать .env файл
```

#### 3.2.5 Миграции базы данных
```bash
alembic upgrade head
```

#### 3.2.6 Загрузка начальных данных (опционально)
```bash
python scripts/seed_data.py
```

### 3.3 Frontend Setup

#### 3.3.1 Установка Node.js зависимостей
```bash
cd frontend
npm install
```

#### 3.3.2 Настройка переменных окружения
```bash
cp .env.example .env
# Отредактировать .env файл
```

### 3.4 Запуск сервисов

#### 3.4.1 Backend (Development)
```bash
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

#### 3.4.2 Celery Worker (отдельный терминал)
```bash
cd backend
celery -A app.infrastructure.messaging.celery_app worker --loglevel=info
```

#### 3.4.3 Celery Beat (для расписания, отдельный терминал)
```bash
cd backend
celery -A app.infrastructure.messaging.celery_app beat --loglevel=info
```

#### 3.4.4 Frontend (Development)
```bash
cd frontend
npm run dev
```

### 3.5 Docker Compose (альтернатива)

Для быстрого развертывания всех сервисов:

```bash
docker-compose up --build
```

---

## 4. Проверки работоспособности

### 4.1 Backend Health Check
- [ ] `curl http://localhost:8000/health` возвращает `{"status": "ok"}`
- [ ] `curl http://localhost:8000/api/v1/auth/login` доступен
- [ ] Swagger UI доступен на `http://localhost:8000/docs`

### 4.2 Frontend Health Check
- [ ] Frontend доступен на `http://localhost:5173` (Vite dev server)
- [ ] Логин-страница загружается
- [ ] Нет ошибок в консоли браузера

### 4.3 Database Check
```bash
psql -U user -d minitms_db -c "SELECT * FROM users LIMIT 1;"
```

### 4.4 Redis Check
```bash
redis-cli ping  # Должен вернуть PONG
```

### 4.5 Celery Check
- [ ] Celery Worker запущен без ошибок
- [ ] Celery Beat отправляет задачи по расписанию
- [ ] Задачи выполняются (проверить логи)

### 4.6 External Services Check
- [ ] Trans.eu доступен и авторизация проходит
- [ ] OpenStreetMap API отвечает (OSRM, Nominatim)
- [ ] GPS-провайдер API доступен
- [ ] Google Sheets API авторизован (OAuth 2.0)
- [ ] SMTP отправка работает (тестовое письмо)

---

## 5. Создание первого пользователя

```bash
cd backend
python scripts/create_admin_user.py \
  --login admin \
  --password SecurePassword123 \
  --role ADMINISTRATOR
```

---

## 6. Production Deployment

### 6.1 Backend Production
- [ ] Настроить Gunicorn вместо Uvicorn напрямую
  ```bash
  gunicorn main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
  ```
- [ ] Настроить Nginx как reverse proxy
- [ ] Настроить HTTPS (SSL сертификат)
- [ ] Настроить systemd сервисы для автозапуска

### 6.2 Frontend Production
```bash
cd frontend
npm run build
# Файлы будут в dist/
```
- [ ] Настроить веб-сервер (Nginx/Apache) для раздачи статики
- [ ] Настроить HTTPS

### 6.3 Database Production
- [ ] Настроить автоматические бэкапы (pg_dump)
- [ ] Настроить мониторинг (pg_stat_statements)
- [ ] Оптимизировать индексы

### 6.4 Мониторинг
- [ ] Настроить логирование (ELK Stack или аналог)
- [ ] Настроить мониторинг метрик (Prometheus + Grafana)
- [ ] Настроить алерты о проблемах

---

## 7. Troubleshooting

### 7.1 Backend не запускается
- Проверить логи: `tail -f backend/logs/app.log`
- Проверить подключение к БД
- Проверить переменные окружения

### 7.2 Celery не обрабатывает задачи
- Проверить подключение к Redis
- Проверить логи Celery Worker
- Убедиться что Celery Beat запущен

### 7.3 Scraping не работает
- Проверить учетные данные Trans.eu
- Проверить что Playwright установлен
- Проверить интернет-соединение

### 7.4 GPS-данные не обновляются
- Проверить учетные данные GPS-провайдера
- Проверить API endpoint
- Проверить формат ответа API

---

## 8. Обновление системы

```bash
# Остановить сервисы
docker-compose down  # если используется Docker

# Обновить код
git pull origin main

# Backend
cd backend
pip install -r requirements.txt
alembic upgrade head

# Frontend
cd frontend
npm install
npm run build

# Запустить сервисы
docker-compose up -d
```

---

## 9. Безопасность

- [ ] Изменены все дефолтные пароли
- [ ] SECRET_KEY уникальный и не хранится в репозитории
- [ ] HTTPS настроен для Production
- [ ] Firewall настроен (закрыты неиспользуемые порты)
- [ ] База данных не доступна извне
- [ ] Логи не содержат чувствительную информацию
- [ ] Регулярные обновления безопасности

---

**Дата последнего обновления**: 23 января 2026
**Версия документа**: 1.0
