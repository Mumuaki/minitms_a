# MiniTMS — проверка и управление на VPS 89.167.70.67

## Быстрая проверка (с ПК)

```powershell
powershell -ExecutionPolicy Bypass -File scripts/test-remote.ps1
```

Проверяет: Backend `/health`, API `/docs`, Frontend на порту 80.

**Прямые URL в браузере:**
- Frontend: http://89.167.70.67
- API Docs: http://89.167.70.67:8000/docs
- **noVNC (браузер скрапера):** http://89.167.70.67:6080

---

## noVNC — ввод кода и управление браузером Trans.eu

Через noVNC вы можете **видеть** экран браузера, в котором работает скрапер Trans.eu, и **вручную вводить код (например 594959)** и выполнять другие действия, если автоматический ввод не сработал.

1. Откройте http://89.167.70.67:6080 и нажмите **Connect** (пароль не нужен). При запросе сертификата нажмите **Approve**.
2. **Чтобы можно было печатать и кликать:** откройте **Settings** (шестерёнка) в noVNC и **отключите «View Only»** (снимите галочку). Сохраните при необходимости.
3. В окне noVNC отображается виртуальный рабочий стол; когда скрапер откроет Trans.eu, вы увидите страницу авторизации. Вы можете:
   - ввести код (594959 или иной) в поле на странице Trans.eu;
   - нажать кнопки входа/подтверждения;
   - при необходимости выполнить другие действия (капча, смена пароля и т.д.).
4. Режим **Shared** позволяет одновременно видеть сессию и не мешать скраперу (ввод с вашей стороны тоже попадает в ту же сессию).

Код по умолчанию для автоматического ввода задаётся в `backend/.env`: `TRANS_EU_AUTH_CODE=594959`.

---

## Обновление приложения (push кода → VPS)

```powershell
# 1. Закоммитить и запушить изменения в GitHub
powershell -ExecutionPolicy Bypass -File scripts/sync-github.ps1

# 2. Применить на VPS (git pull + docker rebuild + restart)
powershell -ExecutionPolicy Bypass -File scripts/sync-remote-server.ps1
```

Или вручную на сервере:

```bash
cd /opt/minitms
git pull origin main
docker compose -f docker-compose.vps.yml build backend
docker compose -f docker-compose.vps.yml up -d
```

---

## Управление контейнерами на VPS

```bash
# Статус
docker compose -f docker-compose.vps.yml ps

# Логи backend
docker compose -f docker-compose.vps.yml logs -f backend

# Логи frontend
docker compose -f docker-compose.vps.yml logs -f frontend

# Перезапуск backend
docker compose -f docker-compose.vps.yml restart backend

# Полная пересборка
docker compose -f docker-compose.vps.yml build --no-cache backend
docker compose -f docker-compose.vps.yml up -d
```

---

## GPS трекер (GPS Guard / a1.gpsguard.eu)

Приложение использует **GPS Guard** API (`a1.gpsguard.eu`).

### Конфигурация в `backend/.env` на VPS

```env
GPS_DOZOR_URL=https://a1.gpsguard.eu/api/v1/vehicle/
GPS_DOZOR_USERNAME=ваш-email@example.com
GPS_DOZOR_PASSWORD=ваш-пароль
```

> Файл `.env` **не попадает** в git (`.dockerignore`). Docker Compose читает его через `env_file`
> и передаёт переменные в контейнер.

### Проверка GPS статуса

В браузере: **GPS трекер** в меню — показывает статус подключения и список ТС с координатами.

Или через API (нужен JWT-токен):

```bash
# На сервере:
TOKEN=$(curl -s http://localhost:8000/api/v1/auth/login \
  -X POST -d "username=admin@minitms.local&password=admin123" \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/v1/gps/status
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/v1/gps/vehicles
```

### Принцип работы GPS обновления

1. `GET /api/v1/groups` → получаем группу (напр. `IKOC`)
2. `GET /api/v1/vehicles/group/IKOC` → список ТС группы
3. Сопоставление по `gps_tracker_id` (= `Code` в GPS Guard) или госномеру
4. Координаты → обратное геокодирование через Nominatim → адрес в карточке ТС

---

## Переменные окружения на VPS (`/opt/minitms/backend/.env`)

| Переменная | Описание |
|---|---|
| `DATABASE_URL` | `postgresql://admin:<pwd>@postgres:5432/minitms` |
| `REDIS_URL` | `redis://redis:6379/0` |
| `SECRET_KEY` | JWT-секрет (мин. 32 символа) |
| `GPS_DOZOR_URL` | `https://a1.gpsguard.eu/api/v1/vehicle/` |
| `GPS_DOZOR_USERNAME` | Email аккаунта GPS Guard |
| `GPS_DOZOR_PASSWORD` | Пароль аккаунта GPS Guard |
| `TRANS_EU_USERNAME` | Логин Trans.eu |
| `TRANS_EU_PASSWORD` | Пароль Trans.eu |

> Хосты `postgres` и `redis` — имена Docker-контейнеров в сети `minitms_minitms-network`.

---

## Полезные команды на VPS

| Действие | Команда |
|---|---|
| Статус контейнеров | `docker compose -f docker-compose.vps.yml ps` |
| Логи backend | `docker compose -f docker-compose.vps.yml logs -f backend` |
| Проверить GPS credentials | `docker exec minitms-backend env \| grep GPS` |
| Подключиться к БД | `psql 'postgresql://admin:<pwd>@127.0.0.1:5432/minitms'` |
| Restart all | `docker compose -f docker-compose.vps.yml up -d` |
