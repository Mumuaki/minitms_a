# 🚀 MiniTMS Server Management Scripts

Полный набор скриптов для управления, диагностики и тестирования развернутого приложения MiniTMS на удаленном сервере **89.167.70.67**.

---

## 📋 Содержание

1. [Быстрый старт](#быстрый-старт)
2. [Список скриптов](#список-скриптов)
3. [Детальное описание](#детальное-описание)
4. [Сценарии использования](#сценарии-использования)
5. [Troubleshooting](#troubleshooting)

---

## 🎯 Быстрый старт

### Первичная проверка системы (рекомендуется начать с этого)

```powershell
cd d:\MiniTMS
.\check_server.ps1
```

Если все OK, переходите к детальной проверке:

```powershell
.\check_modules.ps1
```

Для тестирования бизнес-требований:

```powershell
.\test_business_requirements.ps1
```

---

## 📂 Список скриптов

| Скрипт | Назначение | Время выполнения | Приоритет |
|--------|-----------|------------------|-----------|
| `QUICK_START.md` | Краткая инструкция по быстрому старту | - | ⭐⭐⭐ |
| `connect_server.ps1` | Быстрое SSH подключение | Мгновенно | ⭐⭐⭐ |
| `check_server.ps1` | Базовая диагностика всех компонентов | 30-60 сек | ⭐⭐⭐ |
| `check_modules.ps1` | Детальная проверка всех 10 модулей | 1-2 мин | ⭐⭐⭐ |
| `test_business_requirements.ps1` | Тестирование бизнес-требований | 2-3 мин | ⭐⭐ |
| `test_features.ps1` | Тестирование специфических функций | 1-2 мин | ⭐⭐ |
| `fix_server.ps1` | Интерактивное меню для исправлений | Интерактивно | ⭐⭐⭐ |
| `SERVER_MANAGEMENT.md` | Полная документация по управлению | - | ⭐⭐⭐ |

---

## 📖 Детальное описание

### 1️⃣ `connect_server.ps1` - Прямое подключение

**Назначение:** Быстрое SSH подключение к серверу

**Использование:**
```powershell
.\connect_server.ps1
```

**Что делает:**
- Подключается к серверу через SSH
- Предоставляет полный доступ к командной строке

---

### 2️⃣ `check_server.ps1` - Базовая диагностика

**Назначение:** Быстрая проверка здоровья системы

**Использование:**
```powershell
.\check_server.ps1
```

**Что проверяет:**
- ✅ SSH соединение
- ✅ Системная информация (OS, диск, память)
- ✅ PostgreSQL (статус, база minitms)
- ✅ Redis (статус, ping)
- ✅ Backend сервис (процессы, порт 8000)
- ✅ Frontend сервис (процессы, порт 3000/80)
- ✅ Web сервер (Nginx/Apache)
- ✅ Логи приложения
- ✅ API endpoints (/health, /docs)

**Результат:**
- Зеленые галочки ✓ - все работает
- Красные крестики ✗ - есть проблемы

---

### 3️⃣ `check_modules.ps1` - Детальная проверка модулей

**Назначение:** Проверка всех 10 модулей согласно спецификации

**Использование:**
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

**Дополнительно:**
- Database tables and size
- Redis info and keys
- Frontend availability
- Environment configuration
- Recent errors in logs

---

### 4️⃣ `test_business_requirements.ps1` - Тестирование бизнес-требований

**Назначение:** Проверка соответствия бизнес-требованиям из документации

**Использование:**
```powershell
.\test_business_requirements.ps1
```

**Тестируемые требования:**

#### Критические (КРИТИЧЕСКИЙ):
- **BR-001:** Trans.eu Integration
- **BR-002:** Profitability Calculation
- **FR-FLEET-001:** Fleet Management
- **FR-CALC-001:** Vehicle Filtering
- **FR-UI-002:** Color Coding (🔴⚪🟡🟢)
- **FR-EMAIL-006:** Email Limits (50/hour, 30sec)
- **FR-PLAN-001:** Financial Planning
- **FR-GSHEET-002:** Google Sheets Structure (24 columns)

#### Высокий приоритет (ВЫСОКИЙ):
- **BR-003:** GPS Location Tracking
- **BR-004:** Multi-user Support (4 roles)
- **BR-007:** Google Sheets Integration
- **FR-LOC-001:** Localization (RU, EN, SK, PL)
- **FR-SETTINGS-003:** Rate Settings (0.15-3.5 EUR/km)

#### Средний приоритет (СРЕДНИЙ):
- **BR-005:** GPS Trackers
- **BR-006:** Email Communication

**Также проверяет:**
- Performance (< 3 sec load, < 5 sec calc)
- Security (TLS, bcrypt, headers)
- Database integrity
- Redis cache status

---

### 5️⃣ `test_features.ps1` - Тестирование функций

**Назначение:** Детальное тестирование специфических функций

**Использование:**
```powershell
.\test_features.ps1
```

**Тестируемые функции:**
1. Authentication System
2. Fleet Management CRUD
3. Trans.eu Scraping
4. Profitability Calculation
5. Route Visualization (OSM)
6. GPS Integration (GPS Dozor)
7. Email Communication
8. Financial Planning
9. Google Sheets Integration
10. Notification System
11. Localization (4 languages)
12. System Settings
13. Database Performance
14. Redis Cache Performance
15. API Response Time
16. Security Headers
17. CORS Configuration
18. WebSocket Support
19. File Upload
20. Export Functionality

---

### 6️⃣ `fix_server.ps1` - Интерактивное управление

**Назначение:** Интерактивное меню для управления и исправления проблем

**Использование:**
```powershell
.\fix_server.ps1
```

**Доступные действия (20 опций):**

#### Управление сервисами (1-5):
1. Restart Backend Service
2. Restart Frontend Service
3. Restart PostgreSQL
4. Restart Redis
5. Restart All Services

#### Логи (6-7):
6. View Backend Logs (live)
7. View Frontend Logs (live)

#### База данных (8-9, 17):
8. Check Database Migrations
9. Run Database Migrations
17. Backup Database

#### Кэш и ресурсы (10-11, 18):
10. Clear Redis Cache
11. Check Disk Space
18. View System Resources

#### Обновление (12-13):
12. Update Backend Code (git pull)
13. Install/Update Dependencies

#### Диагностика (14-16, 19-20):
14. Check Service Status
15. Test Trans.eu Connection
16. Test GPS Integration
19. Check Network Connectivity
20. Full System Diagnostic

---

## 🎬 Сценарии использования

### Сценарий 1: Первичная настройка и проверка

```powershell
# Шаг 1: Базовая проверка
.\check_server.ps1

# Шаг 2: Детальная проверка модулей
.\check_modules.ps1

# Шаг 3: Проверка бизнес-требований
.\test_business_requirements.ps1

# Шаг 4: Если есть проблемы
.\fix_server.ps1
```

### Сценарий 2: Ежедневная проверка

```powershell
# Быстрая проверка здоровья системы
.\check_server.ps1

# Если все OK - готово!
# Если есть проблемы - используйте fix_server.ps1
```

### Сценарий 3: Backend не отвечает

```powershell
# Запустите интерактивное меню
.\fix_server.ps1

# Выберите:
# 1 - Restart Backend Service
# Подождите 5 секунд
# 6 - View Backend Logs (live) - для просмотра ошибок
# Ctrl+C для выхода из логов
# 14 - Check Service Status
```

### Сценарий 4: Проблемы с базой данных

```powershell
.\fix_server.ps1

# Выберите:
# 8 - Check Database Migrations
# 9 - Run Database Migrations (если нужно)
# 3 - Restart PostgreSQL (если не помогло)
```

### Сценарий 5: Обновление приложения

```powershell
.\fix_server.ps1

# Выберите в следующем порядке:
# 17 - Backup Database (ОБЯЗАТЕЛЬНО!)
# 12 - Update Backend Code (git pull)
# 13 - Install/Update Dependencies
# 9 - Run Database Migrations
# 5 - Restart All Services
# Подождите 10 секунд
# 14 - Check Service Status
```

### Сценарий 6: Проверка интеграций

```powershell
.\fix_server.ps1

# Выберите:
# 15 - Test Trans.eu Connection
# 16 - Test GPS Integration
# 19 - Check Network Connectivity
```

### Сценарий 7: Проблемы с производительностью

```powershell
.\fix_server.ps1

# Выберите:
# 18 - View System Resources
# 11 - Check Disk Space
# 10 - Clear Redis Cache
# 5 - Restart All Services
```

---

## 🔧 Troubleshooting

### Проблема: "SSH connection failed"

**Решение:**
1. Проверьте SSH ключ: `ls ~/.ssh/`
2. Проверьте доступность сервера: `ping 89.167.70.67`
3. Попробуйте подключиться вручную: `ssh root@89.167.70.67`

### Проблема: "Backend не отвечает (HTTP 500)"

**Решение:**
```powershell
.\fix_server.ps1
# 6 - View Backend Logs
# Найдите ошибку в логах
# 1 - Restart Backend Service
```

### Проблема: "Database connection failed"

**Решение:**
```powershell
.\fix_server.ps1
# 3 - Restart PostgreSQL
# 8 - Check Database Migrations
# 9 - Run Database Migrations (если нужно)
```

### Проблема: "Redis не отвечает"

**Решение:**
```powershell
.\fix_server.ps1
# 4 - Restart Redis
# 10 - Clear Redis Cache
```

### Проблема: "Высокая нагрузка на CPU/RAM"

**Решение:**
```powershell
.\fix_server.ps1
# 18 - View System Resources
# Найдите процесс с высокой нагрузкой
# 10 - Clear Redis Cache
# 5 - Restart All Services
```

### Проблема: "Нет места на диске"

**Решение:**
```powershell
.\fix_server.ps1
# 11 - Check Disk Space
# Затем вручную:
.\connect_server.ps1
# На сервере:
journalctl --vacuum-time=7d  # Очистка старых логов
```

### Проблема: "Trans.eu не работает"

**Решение:**
```powershell
.\fix_server.ps1
# 15 - Test Trans.eu Connection
# Проверьте credentials в .env:
.\connect_server.ps1
cat /root/MiniTMS/backend/.env | grep TRANS_EU
```

### Проблема: "GPS интеграция не работает"

**Решение:**
```powershell
.\fix_server.ps1
# 16 - Test GPS Integration
# Проверьте credentials:
.\connect_server.ps1
cat /root/MiniTMS/backend/.env | grep GPS_DOZOR
```

---

## 📊 Интерпретация результатов

### HTTP Status Codes:

| Code | Значение | Действие |
|------|----------|----------|
| 200 | ✅ OK | Все работает |
| 401 | ⚠️ Unauthorized | Требуется аутентификация (нормально для защищенных endpoints) |
| 404 | ❌ Not Found | Endpoint не найден (проверьте URL) |
| 500 | ❌ Server Error | Внутренняя ошибка (смотрите логи) |
| 502/503 | ❌ Bad Gateway/Unavailable | Сервис недоступен (перезапустите) |

### Service Status:

| Status | Значение | Действие |
|--------|----------|----------|
| `active (running)` | ✅ Работает | OK |
| `inactive (dead)` | ❌ Остановлен | Запустите сервис |
| `failed` | ❌ Ошибка | Смотрите логи |

---

## 🔗 Полезные ссылки

После успешного запуска доступны:

- **Backend API:** http://89.167.70.67:8000
- **API Documentation:** http://89.167.70.67:8000/docs
- **Frontend:** http://89.167.70.67:3000 (или :80)

---

## 📚 Дополнительная документация

- **Полное руководство:** `SERVER_MANAGEMENT.md`
- **Быстрый старт:** `QUICK_START.md`
- **Спецификация проекта:** `docs/MiniTMS_Full_Doc_Structure.md`
- **Новые функции:** `docs/New_Features_Documentation.md`

---

## 🎯 Чеклист регулярного обслуживания

### ✅ Ежедневно:
- [ ] Запустить `check_server.ps1`
- [ ] Проверить логи на ошибки
- [ ] Мониторинг использования ресурсов

### ✅ Еженедельно:
- [ ] Запустить `check_modules.ps1`
- [ ] Запустить `test_business_requirements.ps1`
- [ ] Очистка старых логов
- [ ] Проверка свободного места на диске
- [ ] Резервное копирование базы данных

### ✅ Ежемесячно:
- [ ] Обновление зависимостей
- [ ] Проверка безопасности (обновления ОС)
- [ ] Анализ производительности
- [ ] Оптимизация базы данных

---

## 🆘 Экстренная помощь

### Быстрые команды:

```powershell
# Перезагрузка всех сервисов
ssh root@89.167.70.67 "systemctl restart postgresql redis minitms-backend minitms-frontend"

# Проверка статуса
ssh root@89.167.70.67 "systemctl status minitms-backend minitms-frontend"

# Просмотр ошибок
ssh root@89.167.70.67 "journalctl -u minitms-backend -n 50 --no-pager"

# Очистка Redis
ssh root@89.167.70.67 "redis-cli FLUSHDB"

# Бэкап БД
ssh root@89.167.70.67 "sudo -u postgres pg_dump minitms > /root/backup_$(date +%Y%m%d_%H%M%S).sql"
```

---

## 📞 Контакты

- **Сервер:** 89.167.70.67
- **Пользователь:** root
- **Аутентификация:** SSH ключ
- **Git:** D:\Git

---

**Версия:** 1.0  
**Дата:** 2026-02-20  
**Статус:** Production Ready ✅
