> [!NOTE]
> **Внимание:** Базовые архитектурные решения (включая выбор БД, шины сообщений, GPS-провайдера и единиц измерения) зафиксированы в PROJECT-CONFIG.md. Любые расхождения в данной спецификации следует трактовать в пользу центрального конфига.

# Р§РµРєР»РёСЃС‚ СЂР°Р·РІРµСЂС‚С‹РІР°РЅРёСЏ MiniTMS

## 1. РўСЂРµР±РѕРІР°РЅРёСЏ Рє РёРЅС„СЂР°СЃС‚СЂСѓРєС‚СѓСЂРµ

### 1.1 РћРїРµСЂР°С†РёРѕРЅРЅР°СЏ СЃРёСЃС‚РµРјР°
- [ ] **Windows 10/11** (РґР»СЏ Desktop РІРµСЂСЃРёРё) РёР»Рё **Linux Ubuntu 20.04+** (РґР»СЏ Server)
- [ ] **Docker Desktop** (Windows) РёР»Рё **Docker Engine** (Linux)
- [ ] **Git** РґР»СЏ РєР»РѕРЅРёСЂРѕРІР°РЅРёСЏ СЂРµРїРѕР·РёС‚РѕСЂРёСЏ

### 1.2 РЎРµСЂРІРµСЂРЅС‹Рµ СЂРµСЃСѓСЂСЃС‹ (Production)
- [ ] **CPU**: РјРёРЅРёРјСѓРј 4 СЏРґСЂР° (СЂРµРєРѕРјРµРЅРґСѓРµС‚СЃСЏ 8)
- [ ] **RAM**: РјРёРЅРёРјСѓРј 8 GB (СЂРµРєРѕРјРµРЅРґСѓРµС‚СЃСЏ 16 GB)
- [ ] **Р”РёСЃРє**: РјРёРЅРёРјСѓРј 50 GB SSD
- [ ] **РЎРµС‚СЊ**: СЃС‚Р°Р±РёР»СЊРЅРѕРµ РїРѕРґРєР»СЋС‡РµРЅРёРµ Рє РёРЅС‚РµСЂРЅРµС‚Сѓ

### 1.3 Р‘Р°Р·Р° РґР°РЅРЅС‹С…
- [ ] **PostgreSQL 15+** СѓСЃС‚Р°РЅРѕРІР»РµРЅ
- [ ] Р‘Р°Р·Р° РґР°РЅРЅС‹С… СЃРѕР·РґР°РЅР° (РЅР°РїСЂРёРјРµСЂ, `minitms_db`)
- [ ] РџРѕР»СЊР·РѕРІР°С‚РµР»СЊ Р‘Р” СЃ РїСЂР°РІР°РјРё CREATE, SELECT, INSERT, UPDATE, DELETE

### 1.4 Р”РѕРїРѕР»РЅРёС‚РµР»СЊРЅС‹Рµ СЃРµСЂРІРёСЃС‹
- [ ] **Redis** РґР»СЏ Celery Рё РєСЌС€РёСЂРѕРІР°РЅРёСЏ
- [ ] **SMTP-СЃРµСЂРІРµСЂ** РґР»СЏ email (РёР»Рё СѓС‡РµС‚РЅС‹Рµ РґР°РЅРЅС‹Рµ РІРЅРµС€РЅРµРіРѕ СЃРµСЂРІРёСЃР°, РЅР°РїСЂРёРјРµСЂ Gmail)

---

## 2. РџРµСЂРµРјРµРЅРЅС‹Рµ РѕРєСЂСѓР¶РµРЅРёСЏ

### 2.1 Backend (`backend/.env`)

```env
# Database
DATABASE_URL=postgresql://admin:password@postgres:5432/minitms

# Security
SECRET_KEY=your-secret-key-here
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=30

# Redis
REDIS_URL=redis://redis:6379/0

# Trans.eu Credentials
TRANS_EU_LOGIN=your_login
TRANS_EU_PASSWORD=your_password

# OpenStreetMap / OSRM
OSM_TILE_SERVER=https://tile.openstreetmap.org/{z}/{x}/{y}.png
OSRM_SERVER=http://router.project-osrm.org
NOMINATIM_SERVER=https://nominatim.openstreetmap.org

# GPS Guard (a1.gpsguard.eu)
GPS_DOZOR_URL=https://a1.gpsguard.eu/api/v1/vehicle/
GPS_DOZOR_USERNAME=your_login@example.com
GPS_DOZOR_PASSWORD=your_password

# Google Services (С‚РѕР»СЊРєРѕ РґР»СЏ Google Sheets)
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

# Telegram (РѕРїС†РёРѕРЅР°Р»СЊРЅРѕ)
TELEGRAM_BOT_TOKEN=your_bot_token
```

### 2.2 Frontend (`frontend/.env`)

```env
VITE_API_BASE_URL=http://localhost:8000/api/v1
VITE_OSM_TILE_SERVER=https://tile.openstreetmap.org/{z}/{x}/{y}.png
VITE_TRANS_EU_CLIENT_ID=your_client_id
```

---

## 3. РЁР°РіРё РїРѕ СЂР°Р·РІРµСЂС‚С‹РІР°РЅРёСЋ

### 3.1 РљР»РѕРЅРёСЂРѕРІР°РЅРёРµ СЂРµРїРѕР·РёС‚РѕСЂРёСЏ
```bash
git clone https://github.com/Mumuaki/minitms_a.git
cd minitms_a
```

### 3.2 Backend Setup

#### 3.2.1 РЎРѕР·РґР°РЅРёРµ РІРёСЂС‚СѓР°Р»СЊРЅРѕРіРѕ РѕРєСЂСѓР¶РµРЅРёСЏ
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Linux/Mac
# РёР»Рё
venv\Scripts\activate  # Windows
```

#### 3.2.2 РЈСЃС‚Р°РЅРѕРІРєР° Р·Р°РІРёСЃРёРјРѕСЃС‚РµР№
```bash
pip install -r requirements.txt
```

#### 3.2.3 РЈСЃС‚Р°РЅРѕРІРєР° Playwright (РґР»СЏ СЃРєСЂР°РїРёРЅРіР°)
```bash
playwright install chromium
```

#### 3.2.4 РќР°СЃС‚СЂРѕР№РєР° РїРµСЂРµРјРµРЅРЅС‹С… РѕРєСЂСѓР¶РµРЅРёСЏ
```bash
cp .env.example .env
# РћС‚СЂРµРґР°РєС‚РёСЂРѕРІР°С‚СЊ .env С„Р°Р№Р»
```

#### 3.2.5 РњРёРіСЂР°С†РёРё Р±Р°Р·С‹ РґР°РЅРЅС‹С…
```bash
alembic upgrade head
```

#### 3.2.6 Р—Р°РіСЂСѓР·РєР° РЅР°С‡Р°Р»СЊРЅС‹С… РґР°РЅРЅС‹С… (РѕРїС†РёРѕРЅР°Р»СЊРЅРѕ)
```bash
python scripts/seed_data.py
```

### 3.3 Frontend Setup

#### 3.3.1 РЈСЃС‚Р°РЅРѕРІРєР° Node.js Р·Р°РІРёСЃРёРјРѕСЃС‚РµР№
```bash
cd frontend
npm install
```

#### 3.3.2 РќР°СЃС‚СЂРѕР№РєР° РїРµСЂРµРјРµРЅРЅС‹С… РѕРєСЂСѓР¶РµРЅРёСЏ
```bash
cp .env.example .env
# РћС‚СЂРµРґР°РєС‚РёСЂРѕРІР°С‚СЊ .env С„Р°Р№Р»
```

### 3.4 Р—Р°РїСѓСЃРє СЃРµСЂРІРёСЃРѕРІ

#### 3.4.1 Backend (Development)
```bash
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

#### 3.4.2 Celery Worker (РѕС‚РґРµР»СЊРЅС‹Р№ С‚РµСЂРјРёРЅР°Р»)
```bash
cd backend
celery -A app.infrastructure.messaging.celery_app worker --loglevel=info
```

#### 3.4.3 Celery Beat (РґР»СЏ СЂР°СЃРїРёСЃР°РЅРёСЏ, РѕС‚РґРµР»СЊРЅС‹Р№ С‚РµСЂРјРёРЅР°Р»)
```bash
cd backend
celery -A app.infrastructure.messaging.celery_app beat --loglevel=info
```

#### 3.4.4 Frontend (Development)
```bash
cd frontend
npm run dev
```

### 3.5 Docker Compose (Р°Р»СЊС‚РµСЂРЅР°С‚РёРІР°)

Р”Р»СЏ Р±С‹СЃС‚СЂРѕРіРѕ СЂР°Р·РІРµСЂС‚С‹РІР°РЅРёСЏ РІСЃРµС… СЃРµСЂРІРёСЃРѕРІ:

```bash
docker-compose up --build
```

---

## 4. РџСЂРѕРІРµСЂРєРё СЂР°Р±РѕС‚РѕСЃРїРѕСЃРѕР±РЅРѕСЃС‚Рё

### 4.1 Backend Health Check
- [ ] `curl http://localhost:8000/health` РІРѕР·РІСЂР°С‰Р°РµС‚ `{"status": "ok"}`
- [ ] `curl http://localhost:8000/api/v1/auth/login` РґРѕСЃС‚СѓРїРµРЅ
- [ ] Swagger UI РґРѕСЃС‚СѓРїРµРЅ РЅР° `http://localhost:8000/docs`

### 4.2 Frontend Health Check
- [ ] Frontend РґРѕСЃС‚СѓРїРµРЅ РЅР° `http://localhost:5173` (Vite dev server) РёР»Рё `http://localhost` (Docker, РїРѕСЂС‚ 80)
- [ ] Р›РѕРіРёРЅ-СЃС‚СЂР°РЅРёС†Р° Р·Р°РіСЂСѓР¶Р°РµС‚СЃСЏ
- [ ] РќРµС‚ РѕС€РёР±РѕРє РІ РєРѕРЅСЃРѕР»Рё Р±СЂР°СѓР·РµСЂР°

### 4.3 Database Check
```bash
psql -U user -d minitms_db -c "SELECT * FROM users LIMIT 1;"
```

### 4.4 Redis Check
```bash
redis-cli ping  # Р”РѕР»Р¶РµРЅ РІРµСЂРЅСѓС‚СЊ PONG
```

### 4.5 Celery Check
- [ ] Celery Worker Р·Р°РїСѓС‰РµРЅ Р±РµР· РѕС€РёР±РѕРє
- [ ] Celery Beat РѕС‚РїСЂР°РІР»СЏРµС‚ Р·Р°РґР°С‡Рё РїРѕ СЂР°СЃРїРёСЃР°РЅРёСЋ
- [ ] Р—Р°РґР°С‡Рё РІС‹РїРѕР»РЅСЏСЋС‚СЃСЏ (РїСЂРѕРІРµСЂРёС‚СЊ Р»РѕРіРё)

### 4.6 External Services Check
- [ ] Trans.eu РґРѕСЃС‚СѓРїРµРЅ Рё Р°РІС‚РѕСЂРёР·Р°С†РёСЏ РїСЂРѕС…РѕРґРёС‚
- [ ] OpenStreetMap API РѕС‚РІРµС‡Р°РµС‚ (OSRM, Nominatim)
- [ ] GPS Guard API РґРѕСЃС‚СѓРїРµРЅ (`GET https://a1.gpsguard.eu/api/v1/groups` СЃ Basic Auth)
- [ ] Google Sheets API Р°РІС‚РѕСЂРёР·РѕРІР°РЅ (OAuth 2.0)
- [ ] SMTP РѕС‚РїСЂР°РІРєР° СЂР°Р±РѕС‚Р°РµС‚ (С‚РµСЃС‚РѕРІРѕРµ РїРёСЃСЊРјРѕ)

---

## 5. РЎРѕР·РґР°РЅРёРµ РїРµСЂРІРѕРіРѕ РїРѕР»СЊР·РѕРІР°С‚РµР»СЏ

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
- [ ] РќР°СЃС‚СЂРѕРёС‚СЊ Gunicorn РІРјРµСЃС‚Рѕ Uvicorn РЅР°РїСЂСЏРјСѓСЋ
  ```bash
  gunicorn main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
  ```
- [ ] РќР°СЃС‚СЂРѕРёС‚СЊ Nginx РєР°Рє reverse proxy
- [ ] РќР°СЃС‚СЂРѕРёС‚СЊ HTTPS (SSL СЃРµСЂС‚РёС„РёРєР°С‚)
- [ ] РќР°СЃС‚СЂРѕРёС‚СЊ systemd СЃРµСЂРІРёСЃС‹ РґР»СЏ Р°РІС‚РѕР·Р°РїСѓСЃРєР°

### 6.2 Frontend Production
```bash
cd frontend
npm run build
# Р¤Р°Р№Р»С‹ Р±СѓРґСѓС‚ РІ dist/
```
- [ ] РќР°СЃС‚СЂРѕРёС‚СЊ РІРµР±-СЃРµСЂРІРµСЂ (Nginx/Apache) РґР»СЏ СЂР°Р·РґР°С‡Рё СЃС‚Р°С‚РёРєРё
- [ ] РќР°СЃС‚СЂРѕРёС‚СЊ HTTPS

### 6.3 Database Production
- [ ] РќР°СЃС‚СЂРѕРёС‚СЊ Р°РІС‚РѕРјР°С‚РёС‡РµСЃРєРёРµ Р±СЌРєР°РїС‹ (pg_dump)
- [ ] РќР°СЃС‚СЂРѕРёС‚СЊ РјРѕРЅРёС‚РѕСЂРёРЅРі (pg_stat_statements)
- [ ] РћРїС‚РёРјРёР·РёСЂРѕРІР°С‚СЊ РёРЅРґРµРєСЃС‹

### 6.4 РњРѕРЅРёС‚РѕСЂРёРЅРі
- [ ] РќР°СЃС‚СЂРѕРёС‚СЊ Р»РѕРіРёСЂРѕРІР°РЅРёРµ (ELK Stack РёР»Рё Р°РЅР°Р»РѕРі)
- [ ] РќР°СЃС‚СЂРѕРёС‚СЊ РјРѕРЅРёС‚РѕСЂРёРЅРі РјРµС‚СЂРёРє (Prometheus + Grafana)
- [ ] РќР°СЃС‚СЂРѕРёС‚СЊ Р°Р»РµСЂС‚С‹ Рѕ РїСЂРѕР±Р»РµРјР°С…

---

## 7. Troubleshooting

### 7.1 Backend РЅРµ Р·Р°РїСѓСЃРєР°РµС‚СЃСЏ
- РџСЂРѕРІРµСЂРёС‚СЊ Р»РѕРіРё: `tail -f backend/logs/app.log`
- РџСЂРѕРІРµСЂРёС‚СЊ РїРѕРґРєР»СЋС‡РµРЅРёРµ Рє Р‘Р”
- РџСЂРѕРІРµСЂРёС‚СЊ РїРµСЂРµРјРµРЅРЅС‹Рµ РѕРєСЂСѓР¶РµРЅРёСЏ

### 7.2 Celery РЅРµ РѕР±СЂР°Р±Р°С‚С‹РІР°РµС‚ Р·Р°РґР°С‡Рё
- РџСЂРѕРІРµСЂРёС‚СЊ РїРѕРґРєР»СЋС‡РµРЅРёРµ Рє Redis
- РџСЂРѕРІРµСЂРёС‚СЊ Р»РѕРіРё Celery Worker
- РЈР±РµРґРёС‚СЊСЃСЏ С‡С‚Рѕ Celery Beat Р·Р°РїСѓС‰РµРЅ

### 7.3 Scraping РЅРµ СЂР°Р±РѕС‚Р°РµС‚
- РџСЂРѕРІРµСЂРёС‚СЊ СѓС‡РµС‚РЅС‹Рµ РґР°РЅРЅС‹Рµ Trans.eu
- РџСЂРѕРІРµСЂРёС‚СЊ С‡С‚Рѕ Playwright СѓСЃС‚Р°РЅРѕРІР»РµРЅ
- РџСЂРѕРІРµСЂРёС‚СЊ РёРЅС‚РµСЂРЅРµС‚-СЃРѕРµРґРёРЅРµРЅРёРµ

### 7.4 GPS-РґР°РЅРЅС‹Рµ РЅРµ РѕР±РЅРѕРІР»СЏСЋС‚СЃСЏ
- РџСЂРѕРІРµСЂРёС‚СЊ СѓС‡РµС‚РЅС‹Рµ РґР°РЅРЅС‹Рµ GPS-РїСЂРѕРІР°Р№РґРµСЂР°
- РџСЂРѕРІРµСЂРёС‚СЊ API endpoint
- РџСЂРѕРІРµСЂРёС‚СЊ С„РѕСЂРјР°С‚ РѕС‚РІРµС‚Р° API

---

## 8. РћР±РЅРѕРІР»РµРЅРёРµ СЃРёСЃС‚РµРјС‹

```bash
# РћСЃС‚Р°РЅРѕРІРёС‚СЊ СЃРµСЂРІРёСЃС‹
docker-compose down  # РµСЃР»Рё РёСЃРїРѕР»СЊР·СѓРµС‚СЃСЏ Docker

# РћР±РЅРѕРІРёС‚СЊ РєРѕРґ
git pull origin main

# Backend
cd backend
pip install -r requirements.txt
alembic upgrade head

# Frontend
cd frontend
npm install
npm run build

# Р—Р°РїСѓСЃС‚РёС‚СЊ СЃРµСЂРІРёСЃС‹
docker-compose up -d
```

---

## 9. Р‘РµР·РѕРїР°СЃРЅРѕСЃС‚СЊ

- [ ] РР·РјРµРЅРµРЅС‹ РІСЃРµ РґРµС„РѕР»С‚РЅС‹Рµ РїР°СЂРѕР»Рё
- [ ] SECRET_KEY СѓРЅРёРєР°Р»СЊРЅС‹Р№ Рё РЅРµ С…СЂР°РЅРёС‚СЃСЏ РІ СЂРµРїРѕР·РёС‚РѕСЂРёРё
- [ ] HTTPS РЅР°СЃС‚СЂРѕРµРЅ РґР»СЏ Production
- [ ] Firewall РЅР°СЃС‚СЂРѕРµРЅ (Р·Р°РєСЂС‹С‚С‹ РЅРµРёСЃРїРѕР»СЊР·СѓРµРјС‹Рµ РїРѕСЂС‚С‹)
- [ ] Р‘Р°Р·Р° РґР°РЅРЅС‹С… РЅРµ РґРѕСЃС‚СѓРїРЅР° РёР·РІРЅРµ
- [ ] Р›РѕРіРё РЅРµ СЃРѕРґРµСЂР¶Р°С‚ С‡СѓРІСЃС‚РІРёС‚РµР»СЊРЅСѓСЋ РёРЅС„РѕСЂРјР°С†РёСЋ
- [ ] Р РµРіСѓР»СЏСЂРЅС‹Рµ РѕР±РЅРѕРІР»РµРЅРёСЏ Р±РµР·РѕРїР°СЃРЅРѕСЃС‚Рё

---

**Р”Р°С‚Р° РїРѕСЃР»РµРґРЅРµРіРѕ РѕР±РЅРѕРІР»РµРЅРёСЏ**: 23 СЏРЅРІР°СЂСЏ 2026
**Р’РµСЂСЃРёСЏ РґРѕРєСѓРјРµРЅС‚Р°**: 1.0


