# 📁 MiniTMS Server Management - Files Overview

## Созданные файлы и их назначение

Всего создано: **13 файлов** для полного управления сервером MiniTMS

---

## 🚀 Главные файлы (начните здесь)

### 1. `START_HERE.md` ⭐⭐⭐
**Назначение:** Точка входа для новых пользователей  
**Размер:** Краткий (2 минуты чтения)  
**Содержит:**
- Самый быстрый старт
- Основные команды
- Чеклист первого запуска

### 2. `launcher.ps1` ⭐⭐⭐
**Назначение:** Интерактивное меню для всех операций  
**Тип:** PowerShell скрипт  
**Функции:**
- Графическое меню
- Запуск всех диагностических скриптов
- Доступ к документации
- SSH подключение

### 3. `INDEX.md` ⭐⭐⭐
**Назначение:** Навигация по всем файлам  
**Размер:** Средний (5 минут чтения)  
**Содержит:**
- Карта всех файлов
- Быстрые ссылки
- Типичные сценарии
- Чеклисты

---

## 📊 Скрипты диагностики

### 4. `check_server.ps1` ⭐⭐⭐
**Назначение:** Базовая проверка всех компонентов  
**Время выполнения:** 30-60 секунд  
**Проверяет:**
- SSH соединение
- Системная информация
- PostgreSQL
- Redis
- Backend сервис
- Frontend сервис
- Web сервер
- API endpoints

**Использование:**
```powershell
.\check_server.ps1
```

### 5. `check_modules.ps1` ⭐⭐⭐
**Назначение:** Детальная проверка всех 10 модулей  
**Время выполнения:** 1-2 минуты  
**Проверяет:**
- MODULE 1: Authentication & Authorization
- MODULE 2: Fleet Management
- MODULE 3: Trans.eu Web Scraping
- MODULE 4: Profitability Calculation
- MODULE 5: Route Planning
- MODULE 6: GPS Integration
- MODULE 7: Email Communication
- MODULE 8: Financial Planning
- MODULE 9: Google Sheets Integration
- MODULE 10: Settings & Configuration
- Database performance
- Redis cache
- Frontend availability

**Использование:**
```powershell
.\check_modules.ps1
```

### 6. `test_business_requirements.ps1` ⭐⭐
**Назначение:** Проверка бизнес-требований из спецификации  
**Время выполнения:** 2-3 минуты  
**Проверяет:**
- Критические требования (BR-001, BR-002, FR-FLEET-001, и т.д.)
- Высокоприоритетные требования
- Средние требования
- Performance requirements
- Security requirements

**Использование:**
```powershell
.\test_business_requirements.ps1
```

### 7. `test_features.ps1` ⭐⭐
**Назначение:** Тестирование 20 специфических функций  
**Время выполнения:** 1-2 минуты  
**Проверяет:**
- Authentication System
- Fleet Management CRUD
- Trans.eu Scraping
- Profitability Calculation
- Route Visualization
- GPS Integration
- Email Communication
- Financial Planning
- Google Sheets Integration
- Notification System
- Localization
- System Settings
- Database Performance
- Redis Performance
- API Response Time
- Security Headers
- CORS Configuration
- WebSocket Support
- File Upload
- Export Functionality

**Использование:**
```powershell
.\test_features.ps1
```

### 8. `run_full_diagnostic.ps1` ⭐⭐
**Назначение:** Полная диагностика с генерацией отчета  
**Время выполнения:** 5-7 минут  
**Делает:**
- Запускает все проверки (check_server, check_modules, test_business_requirements, test_features)
- Проверяет системные ресурсы
- Генерирует детальный отчет в файл
- Анализирует результаты
- Выводит общий статус здоровья системы

**Результат:** Файл `diagnostic_report_YYYYMMDD_HHMMSS.txt`

**Использование:**
```powershell
.\run_full_diagnostic.ps1
```

---

## 🛠️ Скрипты управления

### 9. `fix_server.ps1` ⭐⭐⭐
**Назначение:** Интерактивное меню для исправления проблем  
**Тип:** Интерактивный скрипт  
**Функции:** 20 опций для управления:
1. Restart Backend Service
2. Restart Frontend Service
3. Restart PostgreSQL
4. Restart Redis
5. Restart All Services
6. View Backend Logs (live)
7. View Frontend Logs (live)
8. Check Database Migrations
9. Run Database Migrations
10. Clear Redis Cache
11. Check Disk Space
12. Update Backend Code (git pull)
13. Install/Update Dependencies
14. Check Service Status
15. Test Trans.eu Connection
16. Test GPS Integration
17. Backup Database
18. View System Resources
19. Check Network Connectivity
20. Full System Diagnostic

**Использование:**
```powershell
.\fix_server.ps1
# Выберите нужную опцию из меню
```

### 10. `connect_server.ps1` ⭐⭐⭐
**Назначение:** Быстрое SSH подключение к серверу  
**Тип:** PowerShell скрипт  
**Делает:**
- Подключается к серверу через SSH
- Предоставляет полный доступ к командной строке

**Использование:**
```powershell
.\connect_server.ps1
```

---

## 📚 Документация

### 11. `QUICK_START.md` ⭐⭐⭐
**Назначение:** Краткое руководство по быстрому старту  
**Размер:** Краткий (5 минут чтения)  
**Содержит:**
- Быстрый старт (3 шага)
- Интерпретация результатов
- Типичные проблемы и решения
- Прямое подключение к серверу
- Экстренная помощь
- Полезные ссылки

**Для кого:** Начинающие пользователи

### 12. `README_SERVER_SCRIPTS.md` ⭐⭐⭐
**Назначение:** Полное описание всех скриптов  
**Размер:** Большой (20-30 минут чтения)  
**Содержит:**
- Обзор всех скриптов
- Детальное описание каждого
- Сценарии использования
- Troubleshooting
- Интерпретация результатов
- Чеклисты обслуживания

**Для кого:** Все пользователи

### 13. `SERVER_MANAGEMENT.md` ⭐⭐
**Назначение:** Детальное руководство по управлению сервером  
**Размер:** Очень большой (30-40 минут чтения)  
**Содержит:**
- Полное руководство по управлению
- Структура проекта на сервере
- Конфигурация сервисов (systemd)
- Мониторинг и алерты
- Детальный troubleshooting
- Ручные команды
- Чеклисты регулярного обслуживания

**Для кого:** Продвинутые пользователи и администраторы

---

## 📋 Вспомогательные файлы

### `FILES_OVERVIEW.md` (этот файл)
**Назначение:** Обзор всех созданных файлов  
**Содержит:** Описание каждого файла и его назначение

---

## 🗂️ Структура файлов по категориям

### Категория 1: Точки входа (начните здесь)
- `START_HERE.md` - Для новичков
- `launcher.ps1` - Интерактивное меню
- `INDEX.md` - Навигация

### Категория 2: Быстрая диагностика (ежедневно)
- `check_server.ps1` - Базовая проверка (30 сек)

### Категория 3: Детальная диагностика (еженедельно)
- `check_modules.ps1` - Проверка модулей (1-2 мин)
- `test_business_requirements.ps1` - Бизнес-требования (2-3 мин)
- `test_features.ps1` - Функции (1-2 мин)

### Категория 4: Полная диагностика (ежемесячно)
- `run_full_diagnostic.ps1` - Полный отчет (5-7 мин)

### Категория 5: Управление (при проблемах)
- `fix_server.ps1` - Интерактивное меню
- `connect_server.ps1` - SSH доступ

### Категория 6: Документация (для изучения)
- `QUICK_START.md` - Быстрый старт
- `README_SERVER_SCRIPTS.md` - Полное описание
- `SERVER_MANAGEMENT.md` - Детальное руководство

---

## 🎯 Рекомендуемый порядок использования

### День 1: Знакомство
1. Прочитайте `START_HERE.md` (2 мин)
2. Запустите `launcher.ps1` (изучите меню)
3. Запустите `check_server.ps1` (первая проверка)

### День 2: Детальное изучение
1. Прочитайте `QUICK_START.md` (5 мин)
2. Запустите `check_modules.ps1` (детальная проверка)
3. Изучите `INDEX.md` (навигация)

### День 3: Практика
1. Используйте `fix_server.ps1` (изучите опции)
2. Попробуйте `connect_server.ps1` (SSH доступ)
3. Прочитайте `README_SERVER_SCRIPTS.md` (полное описание)

### День 4: Продвинутые функции
1. Запустите `test_business_requirements.ps1`
2. Запустите `test_features.ps1`
3. Изучите `SERVER_MANAGEMENT.md`

### День 5: Полная диагностика
1. Запустите `run_full_diagnostic.ps1`
2. Изучите сгенерированный отчет
3. Настройте регулярные проверки

---

## 📊 Статистика файлов

| Категория | Количество файлов |
|-----------|-------------------|
| Скрипты диагностики | 5 |
| Скрипты управления | 2 |
| Документация | 5 |
| Вспомогательные | 1 |
| **ВСЕГО** | **13** |

---

## 🔄 Обновления

Все файлы созданы: **2026-02-20**  
Версия: **1.0**  
Статус: **Production Ready** ✅

---

## 💡 Советы по использованию

1. **Начните с `START_HERE.md`** - это займет 2 минуты
2. **Используйте `launcher.ps1`** для ежедневной работы
3. **Добавьте в закладки `INDEX.md`** для быстрой навигации
4. **Запускайте `check_server.ps1`** каждый день
5. **Используйте `fix_server.ps1`** при проблемах
6. **Читайте документацию постепенно** - не обязательно все сразу

---

## 🎓 Уровни сложности файлов

### 🟢 Начинающий уровень
- `START_HERE.md`
- `QUICK_START.md`
- `launcher.ps1`
- `check_server.ps1`
- `fix_server.ps1`

### 🟡 Средний уровень
- `INDEX.md`
- `README_SERVER_SCRIPTS.md`
- `check_modules.ps1`
- `test_business_requirements.ps1`
- `connect_server.ps1`

### 🔴 Продвинутый уровень
- `SERVER_MANAGEMENT.md`
- `test_features.ps1`
- `run_full_diagnostic.ps1`

---

**Готово! Теперь вы знаете все файлы и их назначение.** 🚀

**Начните с:** `START_HERE.md` или `launcher.ps1`
