# Проверка MiniTMS на удалённом сервере 89.167.70.67

## Шаг 1: На сервере — проверить и при необходимости запустить сервисы

Подключитесь по SSH к `89.167.70.67`, перейдите в каталог проекта **/opt/minitms** и выполните:

```bash
cd /opt/minitms
# Если на VPS только docker-compose.yml:
docker compose up -d --build
# Если при логине ошибка 500 (Internal Server Error) — выполните один раз:
bash scripts/vps-fix-backend-network.sh
```

Либо: `bash scripts/vps-server-check-and-start.sh` (если есть docker-compose.vps.yml). Скрипт проверяет Docker, поднимает сервисы, проверяет `/health` и фронтенд.

## Шаг 2: С вашего компьютера — проверить доступность

В каталоге проекта (Windows, PowerShell):

```powershell
make vps-test-remote
```

или:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/test-remote.ps1
```

Проверяются:
1. Backend: `GET http://89.167.70.67:8000/health`
2. Backend: `GET http://89.167.70.67:8000/docs`
3. Frontend: `GET http://89.167.70.67:3000/`
4. OpenAPI: `GET http://89.167.70.67:8000/openapi.json`

## Шаг 3: Ручная проверка в браузере

- **Фронтенд:** http://89.167.70.67:3000  
- **API Docs:** http://89.167.70.67:8000/docs  

Дальше можно пошагово тестировать: логин, разделы приложения, API через Swagger.

## Связь с GPS трекером (API)

Приложение подключается к **GPS Dozor** (a1.gpsguard.eu). Чтобы связь работала на VPS, в `backend/.env` на сервере должны быть заданы:

```env
GPS_DOZOR_URL=https://a1.gpsguard.eu/api/v1/vehicle/
GPS_DOZOR_USERNAME=ваш-логин
GPS_DOZOR_PASSWORD=ваш-пароль
```

После изменения переменных перезапустите backend (на сервере используйте **docker compose** с пробелом):  
- Если на VPS используется **docker-compose.yml** (как в `/opt/minitms`):  
  `docker compose restart backend`  
- Если используется **docker-compose.vps.yml**:  
  `docker compose -f docker-compose.vps.yml restart backend`  
Учётные данные GPS бэкенд читает из **backend/.env** (файл `env_file` в compose).

**Проверка во фронтенде:** зайдите в **GPS трекер** в меню. Там отображаются статус подключения к API и список транспортных средств с координатами. Либо откройте Swagger: `GET /api/v1/gps/status` и `GET /api/v1/gps/vehicles` (с авторизацией).

### Проверка обновления локации ТС на VPS (почему в карточке всё ещё Dortmund)

1. **Убедитесь, что на сервере развёрнут новый backend** (файлы `backend/.../dozor_gps_adapter.py`, `backend/.../refresh_vehicle_location.py`, обновлённые `add_vehicle.py` и `update_vehicle.py`).
   - **Если на VPS есть git:** `git pull` в `/opt/minitms`, затем `docker compose restart backend`.
   - **Если git на VPS нет** — скопируйте файлы с ПК (см. ниже «Копирование backend на VPS»).

2. **Обязательно задайте Dozor в `backend/.env` на VPS** — иначе в карточке будет подставляться тестовая локация (Dortmund). На сервере:
   ```bash
   nano /opt/minitms/backend/.env
   ```
   Добавьте или проверьте строки (подставьте свои учётные данные Dozor):
   ```env
   GPS_DOZOR_URL=https://a1.gpsguard.eu/api/v1/vehicle/
   GPS_DOZOR_USERNAME=ваш_логин_dozor
   GPS_DOZOR_PASSWORD=ваш_пароль_dozor
   ```
   Сохраните, затем: `docker compose restart backend`.

3. **Запустите тест на сервере** (из каталога проекта):
   ```bash
   MINITMS_USER=admin MINITMS_PASSWORD=ваш_пароль bash scripts/vps-test-gps-refresh.sh
   ```
   Скрипт залогинится, найдёт ТС BT152DH, вызовет обновление локации и выведет ответ Dozor и ключи первого ТС (чтобы сверить формат API). По умолчанию проверяется BT152DH; для другого номера: `VEHICLE_PLATE=AA123BB bash scripts/vps-test-gps-refresh.sh`.

4. **Логи backend** (почему Dozor не сработал):
   ```bash
   docker compose logs --tail=100 backend | grep -i dozor
   ```
   Ожидаемые сообщения: `Dozor: credentials not set` (нет учётки), `Dozor: fetched N vehicles`, `Dozor: matched ...` или `Dozor: no vehicle matched` (тогда смотрите ключи из шага 3 и при необходимости добавьте поле в адаптер).

### Копирование backend на VPS (если на сервере нет git)

**С ПК (PowerShell), из каталога проекта `d:\MiniTMS`:**

```powershell
powershell -ExecutionPolicy Bypass -File scripts/deploy-backend-to-vps.ps1
```

Скрипт копирует через **scp** на `root@89.167.70.67` в `/opt/minitms` файлы:
- `backend/src/infrastructure/external_services/gps/dozor_gps_adapter.py`
- `backend/src/application/use_cases/fleet/add_vehicle.py`
- `backend/src/application/use_cases/fleet/update_vehicle.py`
- `backend/src/application/use_cases/fleet/refresh_vehicle_location.py`
- `backend/src/infrastructure/api/v1/endpoints/fleet.py`

Требуется: **ssh/scp** (например, [OpenSSH](https://docs.microsoft.com/en-us/windows-server/administration/openssh/openssh_install_firstuse) или Git Bash). При первом запросе введите пароль от `root` на VPS. После копирования на VPS выполните: `docker compose restart backend`.

**Ручное копирование (если scp недоступен):** создайте на ПК архив папки `backend` (или только указанных подпапок), загрузите его на VPS (например, через WinSCP или веб-панель), на VPS распакуйте в `/opt/minitms`, затем `docker compose restart backend`.

---

## Полезные команды на VPS

| Действие              | Команда |
|-----------------------|--------|
| Статус контейнеров    | `docker ps` |
| Логи backend          | `docker compose -f docker-compose.vps.yml logs -f backend` |
| Логи frontend         | `docker compose -f docker-compose.vps.yml logs -f frontend` |
| Остановить сервисы    | `make vps-down` или `docker compose -f docker-compose.vps.yml down` |
