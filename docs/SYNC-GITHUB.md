# Синхронизация проекта с GitHub (minitms_a)

Репозиторий: **https://github.com/Mumuaki/minitms_a.git**

## Первая выгрузка (если папка ещё не git-репозиторий)

Выполните в терминале **в каталоге проекта** (например `d:\MiniTMS`):

```bash
# 1. Инициализация (если ещё не сделано)
git init

# 2. Подключить удалённый репозиторий
git remote add origin https://github.com/Mumuaki/minitms_a.git

# 3. Добавить все файлы (исключения — из .gitignore: .env, node_modules и т.д.)
git add .

# 4. Первый коммит
git commit -m "Initial commit: MiniTMS backend, frontend, Docker, scripts"

# 5. Имя ветки (обычно main или master)
git branch -M main

# 6. Отправить в GitHub (потребуется авторизация)
git push -u origin main
```

## Если репозиторий уже инициализирован и remote уже есть

```bash
git remote set-url origin https://github.com/Mumuaki/minitms_a.git
git add .
git status
git commit -m "Sync: MiniTMS project"
git push -u origin main
```

## Дальнейшие обновления

После изменений в коде:

```bash
git add .
git status
git commit -m "Описание изменений"
git push
```

## Синхронизация удалённого сервера (VPS) с GitHub

После того как вы сделали `git push` с ПК в **minitms_a**, нужно подтянуть код на сервер и перезапустить сервисы.

### Вариант 1: скрипт с ПК (по SSH)

Из корня проекта на ПК выполните:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/sync-remote-server.ps1
```

Скрипт подключится по SSH к серверу (по умолчанию `root@89.167.70.67`), в каталоге проекта на сервере (**/opt/minitms**) выполнит:
- `git remote set-url origin https://github.com/Mumuaki/minitms_a.git`
- `git fetch origin` и `git pull origin main`; при ошибке (конфликты или «untracked would be overwritten») — `git reset --hard origin/main`, чтобы сервер совпал с репозиторием
- перезапуск backend (и frontend): через Docker Compose или systemd, в зависимости от того, что установлено.

Если проект на сервере лежит в другом каталоге, откройте `scripts/sync-remote-server.ps1` и измените переменную `$REMOTE_PROJECT`.

### Вариант 2: вручную на сервере

Подключитесь по SSH к серверу и выполните в каталоге проекта:

```bash
cd /opt/minitms
git remote set-url origin https://github.com/Mumuaki/minitms_a.git
git fetch origin
git pull origin main
# перезапуск (один из вариантов):
docker compose -f docker-compose.vps.yml restart backend frontend
# или, если без Docker:
systemctl restart minitms-backend minitms-frontend
```

---

## Важно

- Файлы **backend/.env** и **.env** в корне **не попадают** в репозиторий (указаны в `.gitignore`) — секреты не загружаются.
- На VPS после обновления кода из GitHub используйте скрипт `scripts/sync-remote-server.ps1` или команды из раздела выше.
