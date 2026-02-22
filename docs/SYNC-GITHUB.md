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

## Важно

- Файлы **backend/.env** и **.env** в корне **не попадают** в репозиторий (указаны в `.gitignore`) — секреты не загружаются.
- На VPS после обновления кода из GitHub: `cd /opt/minitms && git pull && docker compose restart backend` (если на сервере настроен git и remote).
