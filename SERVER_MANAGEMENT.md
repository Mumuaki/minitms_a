# MiniTMS Server Management Guide

## Обзор

Этот документ содержит инструкции по управлению и диагностике развернутого приложения MiniTMS на удаленном сервере.

**Сервер:** 89.167.70.67  
**Пользователь:** root  
**Аутентификация:** SSH ключ

---

## Доступные скрипты

### 1. `connect_server.ps1` - Быстрое подключение к серверу

Простое SSH подключение к серверу.

```powershell
.\connect_server.ps1
```

**Использование:**
- Подключается к серверу через SSH
- После подключения вы получаете полный доступ к командной строке сервера

---

### 2. `check_server.ps1` - Базовая диагностика сервера

Выполняет базовую проверку всех компонентов системы.

```powershell
.\check_server.ps1
```

**Что проверяет:**
1. SSH соединение
2. Информация о системе (OS, диск, память)
3. PostgreSQL статус и база данных
4. Redis статус и подключение
5. Backend сервис и процессы
6. Backend порт (8000)
7. Frontend сервис и процессы
8. Frontend порт (3000/80/443)
9. Web сервер (Nginx/Apache)
10. Логи приложения
11. API endpoints (health check, docs)

**Время выполнения:** ~30-60 секунд

---

### 3. `check_modules.ps1` - Детальная проверка модулей

Выполняет детальную проверку каждого модуля согласно спецификации MiniTMS.

```powershell
.\check_modules.ps1
```

**Проверяемые модули:**

#### MODULE 1: Authentication & Authorization
- Health Check
- API Documentation
- Login Endpoint

#### MODULE 2: Fleet Management
- Get Vehicles
- Vehicle Statistics

#### MODULE 3: Trans.eu Web Scraping
- Get Cargos
- Search Cargos
- Scraping Status

#### MODULE 4: Profitability Calculation
- Filter by Vehicle
- Calculate Route

#### MODULE 5: Route Planning
- Route Planning Endpoint

#### MODULE 6: GPS Integration
- GPS Vehicles
- GPS Status

#### MODULE 7: Email Communication
- Email Templates
- Email History

#### MODULE 8: Financial Planning
- Financial Plans
- Dashboard Stats

#### MODULE 9: Google Sheets Integration
- Google Sheets Status
- Sync Status

#### MODULE 10: Settings & Configuration
- System Settings
- User Settings

**Дополнительные проверки:**
- Database tables and size
- Redis info and keys
- Frontend availability
- Environment configuration
- Recent errors in logs

**Время выполнения:** ~1-2 минуты

---

### 4. `fix_server.ps1` - Интерактивное управление и исправление

Интерактивное меню для управления сервером и исправления проблем.

```powershell
.\fix_server.ps1
```

**Доступные действия:**

#### Управление сервисами:
1. **Restart Backend Service** - Перезапуск backend сервиса
2. **Restart Frontend Service** - Перезапуск frontend сервиса
3. **Restart PostgreSQL** - Перезапуск базы данных
4. **Restart Redis** - Перезапуск кэша
5. **Restart All Services** - Перезапуск всех сервисов

#### Логи и мониторинг:
6. **View Backend Logs (live)** - Просмотр логов backend в реальном времени
7. **View Frontend Logs (live)** - Просмотр логов frontend в реальном времени

#### База данных:
8. **Check Database Migrations** - Проверка текущей версии миграций
9. **Run Database Migrations** - Запуск миграций базы данных
17. **Backup Database** - Создание резервной копии БД

#### Кэш и производительность:
10. **Clear Redis Cache** - Очистка кэша Redis
11. **Check Disk Space** - Проверка свободного места на диске
18. **View System Resources** - Просмотр использования ресурсов (CPU, RAM, Disk)

#### Обновление и развертывание:
12. **Update Backend Code (git pull)** - Обновление кода из репозитория
13. **Install/Update Dependencies** - Установка/обновление зависимостей

#### Диагностика:
14. **Check Service Status** - Проверка статуса всех сервисов
15. **Test Trans.eu Connection** - Тест подключения к Trans.eu
16. **Test GPS Integration** - Тест подключения к GPS системе
19. **Check Network Connectivity** - Проверка сетевого подключения
20. **Full System Diagnostic** - Полная диагностика системы

---

## Типичные сценарии использования

### Сценарий 1: Первичная проверка после развертывания

```powershell
# Шаг 1: Базовая диагностика
.\check_server.ps1

# Шаг 2: Детальная проверка модулей
.\check_modules.ps1

# Шаг 3: Если есть проблемы - используйте fix_server.ps1
.\fix_server.ps1
```

### Сценарий 2: Backend не отвечает

```powershell
# Запустите fix_server.ps1 и выберите:
# 1 - Restart Backend Service
# 6 - View Backend Logs (live) - для просмотра ошибок
# 14 - Check Service Status - для проверки статуса
```

### Сценарий 3: Проблемы с базой данных

```powershell
# Запустите fix_server.ps1 и выберите:
# 8 - Check Database Migrations
# 9 - Run Database Migrations (если нужно)
# 3 - Restart PostgreSQL (если не помогло)
# 17 - Backup Database (перед серьезными изменениями)
```

### Сценарий 4: Обновление приложения

```powershell
# Запустите fix_server.ps1 и выберите:
# 17 - Backup Database (сначала бэкап!)
# 12 - Update Backend Code (git pull)
# 13 - Install/Update Dependencies
# 9 - Run Database Migrations
# 5 - Restart All Services
```

### Сценарий 5: Проблемы с производительностью

```powershell
# Запустите fix_server.ps1 и выберите:
# 18 - View System Resources
# 11 - Check Disk Space
# 10 - Clear Redis Cache
```

### Сценарий 6: Проверка интеграций

```powershell
# Запустите fix_server.ps1 и выберите:
# 15 - Test Trans.eu Connection
# 16 - Test GPS Integration
# 19 - Check Network Connectivity
```

---

## Ручное подключение и команды

Если вам нужно выполнить команды вручную:

```powershell
# Подключение к серверу
.\connect_server.ps1

# Или напрямую:
ssh root@89.167.70.67
```

### Полезные команды на сервере:

#### Управление сервисами:
```bash
# Статус сервисов
systemctl status minitms-backend
systemctl status minitms-frontend
systemctl status postgresql
systemctl status redis

# Перезапуск
systemctl restart minitms-backend
systemctl restart minitms-frontend

# Логи
journalctl -u minitms-backend -f
journalctl -u minitms-frontend -f
```

#### База данных:
```bash
# Подключение к PostgreSQL
sudo -u postgres psql -d minitms

# Список таблиц
sudo -u postgres psql -d minitms -c '\dt'

# Бэкап
sudo -u postgres pg_dump minitms > backup.sql
```

#### Redis:
```bash
# Проверка подключения
redis-cli ping

# Информация
redis-cli info

# Очистка кэша
redis-cli FLUSHDB
```

#### Процессы:
```bash
# Backend процессы
ps aux | grep uvicorn

# Frontend процессы
ps aux | grep node

# Порты
netstat -tlnp | grep -E ':(8000|3000|80|443)'
```

#### Логи:
```bash
# Backend логи
tail -f /var/log/minitms/backend.log

# Системные логи
journalctl -xe
```

---

## Структура проекта на сервере

Предполагаемая структура (может отличаться):

```
/root/MiniTMS/
├── backend/
│   ├── .env                    # Конфигурация
│   ├── main.py                 # Точка входа
│   ├── requirements.txt        # Зависимости
│   ├── alembic/               # Миграции БД
│   └── app/                   # Код приложения
├── frontend/
│   ├── .env                    # Конфигурация frontend
│   ├── package.json           # Зависимости
│   └── src/                   # Код приложения
└── logs/                      # Логи приложения
```

---

## Конфигурация сервисов (systemd)

### Backend Service: `/etc/systemd/system/minitms-backend.service`

```ini
[Unit]
Description=MiniTMS Backend Service
After=network.target postgresql.service redis.service

[Service]
Type=simple
User=root
WorkingDirectory=/root/MiniTMS/backend
Environment="PATH=/root/MiniTMS/backend/venv/bin"
ExecStart=/root/MiniTMS/backend/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

### Frontend Service: `/etc/systemd/system/minitms-frontend.service`

```ini
[Unit]
Description=MiniTMS Frontend Service
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/MiniTMS/frontend
ExecStart=/usr/bin/npm start
Restart=always

[Install]
WantedBy=multi-user.target
```

---

## Мониторинг и алерты

### Проверка доступности API:
```bash
curl http://89.167.70.67:8000/health
```

### Проверка frontend:
```bash
curl http://89.167.70.67:3000
```

### Мониторинг ресурсов:
```bash
# CPU и память
htop

# Диск
df -h

# Сеть
iftop
```

---

## Troubleshooting

### Проблема: Backend не запускается

**Решение:**
1. Проверьте логи: `journalctl -u minitms-backend -n 50`
2. Проверьте .env файл: `cat /root/MiniTMS/backend/.env`
3. Проверьте зависимости: `cd /root/MiniTMS/backend && pip list`
4. Проверьте порт: `netstat -tlnp | grep 8000`

### Проблема: База данных недоступна

**Решение:**
1. Проверьте статус: `systemctl status postgresql`
2. Проверьте подключение: `sudo -u postgres psql -d minitms -c 'SELECT 1;'`
3. Проверьте логи: `tail -f /var/log/postgresql/postgresql-*.log`

### Проблема: Redis недоступен

**Решение:**
1. Проверьте статус: `systemctl status redis`
2. Проверьте подключение: `redis-cli ping`
3. Проверьте конфигурацию: `cat /etc/redis/redis.conf | grep bind`

### Проблема: Высокая нагрузка на CPU/RAM

**Решение:**
1. Проверьте процессы: `top` или `htop`
2. Очистите Redis: `redis-cli FLUSHDB`
3. Перезапустите сервисы: `systemctl restart minitms-backend`
4. Проверьте логи на зацикливание

### Проблема: Нет места на диске

**Решение:**
1. Проверьте использование: `df -h`
2. Найдите большие файлы: `du -h / | sort -rh | head -20`
3. Очистите логи: `journalctl --vacuum-time=7d`
4. Удалите старые бэкапы

---

## Контакты и поддержка

- **Документация проекта:** `d:\MiniTMS\docs\`
- **Основная спецификация:** `MiniTMS_Full_Doc_Structure.md`
- **Новые функции:** `New_Features_Documentation.md`

---

## Чеклист регулярного обслуживания

### Ежедневно:
- [ ] Проверка статуса сервисов (`check_server.ps1`)
- [ ] Проверка логов на ошибки
- [ ] Мониторинг использования ресурсов

### Еженедельно:
- [ ] Полная диагностика модулей (`check_modules.ps1`)
- [ ] Очистка старых логов
- [ ] Проверка свободного места на диске
- [ ] Резервное копирование базы данных

### Ежемесячно:
- [ ] Обновление зависимостей
- [ ] Проверка безопасности (обновления ОС)
- [ ] Анализ производительности
- [ ] Оптимизация базы данных

---

**Последнее обновление:** 2026-02-20  
**Версия:** 1.0
