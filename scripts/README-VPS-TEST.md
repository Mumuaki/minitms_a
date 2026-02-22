# Проверка MiniTMS на удалённом сервере 89.167.70.67

## Шаг 1: На сервере — проверить и при необходимости запустить сервисы

Подключитесь по SSH к `89.167.70.67`, перейдите в каталог проекта и выполните:

```bash
cd /path/to/MiniTMS   # ваш путь к проекту на VPS
bash scripts/vps-server-check-and-start.sh
```

Скрипт:
- проверит, что Docker запущен;
- при необходимости поднижет backend и frontend (`docker compose -f docker-compose.vps.yml up -d --build`);
- проверит ответы `/health` и главной страницы фронтенда.

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

1. **Убедитесь, что на сервере развёрнут новый backend** (файлы `backend/.../dozor_gps_adapter.py`, `backend/.../refresh_vehicle_location.py`, обновлённые `add_vehicle.py` и `update_vehicle.py`). Если деплой через git: `git pull` в `/opt/minitms`, затем `docker compose restart backend`.

2. **Проверьте `backend/.env` на VPS:** должны быть заданы `GPS_DOZOR_USERNAME` и `GPS_DOZOR_PASSWORD`. После правок: `docker compose restart backend`.

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

---

## Полезные команды на VPS

| Действие              | Команда |
|-----------------------|--------|
| Статус контейнеров    | `docker ps` |
| Логи backend          | `docker compose -f docker-compose.vps.yml logs -f backend` |
| Логи frontend         | `docker compose -f docker-compose.vps.yml logs -f frontend` |
| Остановить сервисы    | `make vps-down` или `docker compose -f docker-compose.vps.yml down` |
