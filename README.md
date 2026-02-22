# 🚛 MiniTMS - Transport Management System

Система управления перевозками (TMS) с интеграцией Trans.eu, GPS-трекинга и автоматического планирования маршрутов.

## 🏗️ Архитектура

- **Backend**: FastAPI + SQLAlchemy + PostgreSQL
- **Frontend**: React + TypeScript + Vite
- **Database**: PostgreSQL 18
- **Cache**: Redis 7
- **Deployment**: Docker + Docker Compose

## 📋 Структура проекта

```
MiniTMS/
├── backend/               # FastAPI приложение
│   ├── src/
│   │   ├── domain/       # Бизнес-логика и сущности
│   │   ├── application/  # Use cases иDTO
│   │   └── infrastructure/ # БД, API, внешние сервисы
│   ├── main.py           # Точка входа
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env
├── frontend/             # React приложение
│   ├── src/
│   │   ├── features/     # Модули приложения
│   │   ├── components/   # UI компоненты
│   │   └── infrastructure/ # API клиент
│   ├── package.json
│   ├── Dockerfile
│   └── nginx.conf
├── docker-compose.yml         # Production
├── docker-compose.dev.yml     # Development
├── docker-compose.vps.yml     # Для VPS с установленными БД
└── DEPLOYMENT.md              # Подробная инструкция
```

## 🚀 Быстрый старт

### Локальная разработка

#### Вариант 1: С Docker (рекомендуется)

```bash
# Клонирование репозитория
git clone <repository-url>
cd MiniTMS

# Копирование .env файлов
cp backend/.env.example backend/.env

# Запуск в режиме разработки
docker-compose -f docker-compose.dev.yml up --build

# Приложение доступно:
# - Frontend: http://localhost:5173
# - Backend API: http://localhost:8000
# - API Docs: http://localhost:8000/docs
```

#### Вариант 2: Без Docker

**Backend:**
```bash
cd backend
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
uvicorn main:app --reload
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

### Production развертывание на VPS

См. подробную инструкцию в [DEPLOYMENT.md](./DEPLOYMENT.md)

#### Краткая версия для VPS с PostgreSQL и Redis

```bash
# На VPS
git clone <repository-url> /opt/minitms
cd /opt/minitms

# Настройка .env
cp backend/.env.example backend/.env
nano backend/.env  # Укажите DATABASE_URL и другие параметры

# Запуск
docker-compose -f docker-compose.vps.yml up -d --build

# Проверка
docker-compose -f docker-compose.vps.yml ps
docker-compose -f docker-compose.vps.yml logs -f
```

## 🔧 Основные возможности

### Реализовано ✅

- **Аутентификация и авторизация**
  - JWT токены (access + refresh)
  - RBAC (Role-Based Access Control)
  - Управление пользователями

- **Управление грузами (Cargo)**
  - Импорт предложений с Trans.eu
  - Фильтрация по параметрам груза
  - Расчет рентабельности
  - Поиск грузов

- **Управление автопарком (Fleet)**
  - CRUD операции с транспортными средствами
  - Интеграция с GPS-системами (GPS Dozor/Guard)
  - Отображение местоположения в реальном времени
  - Статусы транспорта

- **Планирование маршрутов**
  - Интеграция с OSRM для расчета маршрутов
  - Оптимизация расстояния и времени
  - Расчет стоимости топлива
  - Geocoding через Nominatim

- **Внешние интеграции**
  - Trans.eu (веб-скрейпинг предложений)
  - GPS Dozor/GPS Guard API
  - Google Sheets (синхронизация заказов)
  - OSRM (маршрутизация)
  - Email уведомления (SMTP)

### В разработке 🚧

- Мобильное приложение для водителей
- Push-уведомления
- Офлайн режим
- Расширенная аналитика и отчетность
- Интеграция с ERP системами

## 🛠️ Технологический стек

### Backend
- Python 3.11+
- FastAPI
- SQLAlchemy 2.0 (async)
- Alembic (миграции)
- Pydantic v2
- asyncpg / psycopg2
- Playwright (веб-скрейпинг)
- python-jose (JWT)
- passlib (хеширование паролей)

### Frontend
- React 18
- TypeScript
- Vite
- React Router v6
- Axios
- Lucide React (иконки)
- Framer Motion (анимации)

### Infrastructure
- PostgreSQL 18
- Redis 7
- Docker & Docker Compose
- Nginx (reverse proxy)

## 📝 Конфигурация

### Backend Environment Variables

```env
# Database
DATABASE_URL=postgresql://user:password@host:port/database

# Security
SECRET_KEY=your-secret-key-min-32-chars
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=30

# External Services
TRANS_EU_USERNAME=your-username
TRANS_EU_PASSWORD=your-password
HEADLESS_MODE=True

GPS_DOZOR_URL=https://a1.gpsguard.eu/api/v1/vehicle/
GPS_DOZOR_USERNAME=your-email
GPS_DOZOR_PASSWORD=your-password

# Redis (optional)
REDIS_URL=redis://localhost:6379/0

# Application
DEBUG=False
```

### Frontend Environment Variables

```env
VITE_API_URL=http://localhost:8000
```

## 🧪 Тестирование

```bash
# Backend тесты
cd backend
pytest

# Frontend тесты
cd frontend
npm run test
```

## 📊 API документация

После запуска backend, документация доступна по адресам:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- OpenAPI Schema: http://localhost:8000/openapi.json

## 🔐 Безопасность

- JWT токены с коротким временем жизни
- Refresh tokens для автоматического обновления
- Хеширование паролей с bcrypt
- CORS настройка
- Role-Based Access Control (RBAC)
- SQL Injection защита (SQLAlchemy ORM)

## 📦 Миграции базы данных

```bash
# Создание новой миграции
docker-compose exec backend alembic revision --autogenerate -m "описание"

# Применение миграций
docker-compose exec backend alembic upgrade head

# Откат последней миграции
docker-compose exec backend alembic downgrade -1
```

## 🐛 Отладка

### Просмотр логов

```bash
# Все сервисы
docker-compose logs -f

# Конкретный сервис
docker-compose logs -f backend
docker-compose logs -f frontend
```

### Подключение к базе данных

```bash
# Через Docker
docker compose exec postgres psql -U admin -d minitms

# Напрямую
psql -h localhost -U admin -d minitms
```

### Вход в контейнер

```bash
docker-compose exec backend bash
docker-compose exec frontend sh
```

## 🤝 Contributing

1. Fork проекта
2. Создайте feature branch (`git checkout -b feature/amazing-feature`)
3. Commit изменения (`git commit -m 'Add amazing feature'`)
4. Push в branch (`git push origin feature/amazing-feature`)
5. Откройте Pull Request

## 📄 Лицензия

Этот проект распространяется под лицензией MIT.

## 👥 Авторы

- Команда разработки MiniTMS

## 📞 Поддержка

Для вопросов и предложений создавайте Issues в репозитории.

---

**Создано с ❤️ для оптимизации логистических процессов**
