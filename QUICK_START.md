# MiniTMS Server - Quick Start Guide

## 🚀 Быстрый старт

### Шаг 1: Базовая проверка системы

Откройте PowerShell в директории `d:\MiniTMS\` и выполните:

```powershell
.\check_server.ps1
```

Это займет ~30 секунд и покажет статус всех компонентов.

---

### Шаг 2: Детальная проверка модулей

Если базовая проверка прошла успешно, выполните детальную проверку:

```powershell
.\check_modules.ps1
```

Это займет ~1-2 минуты и проверит все 10 модулей системы.

---

### Шаг 3: Исправление проблем (если есть)

Если обнаружены проблемы, запустите интерактивное меню:

```powershell
.\fix_server.ps1
```

Выберите нужное действие из меню.

---

## 📊 Интерпретация результатов

### ✅ Успешная проверка

Вы увидите:
- `✓` зеленые галочки для работающих компонентов
- `HTTP Status: 200` для доступных API endpoints
- `Active: active (running)` для сервисов

### ⚠️ Предупреждения

Желтые предупреждения могут означать:
- `HTTP Status: 401` - требуется аутентификация (это нормально для защищенных endpoints)
- `Service not found` - сервис может быть запущен вручную, а не через systemd

### ❌ Ошибки

Красные ошибки требуют внимания:
- `Connection refused` - сервис не запущен
- `HTTP Status: 500` - внутренняя ошибка сервера
- `Database connection failed` - проблемы с БД

---

## 🔧 Типичные проблемы и решения

### Backend не отвечает

```powershell
.\fix_server.ps1
# Выберите: 1 (Restart Backend Service)
# Затем: 6 (View Backend Logs) для просмотра ошибок
```

### Frontend не отвечает

```powershell
.\fix_server.ps1
# Выберите: 2 (Restart Frontend Service)
# Затем: 7 (View Frontend Logs)
```

### База данных недоступна

```powershell
.\fix_server.ps1
# Выберите: 3 (Restart PostgreSQL)
# Затем: 8 (Check Database Migrations)
```

### Все сломалось

```powershell
.\fix_server.ps1
# Выберите: 5 (Restart All Services)
# Подождите 10 секунд
# Затем: 14 (Check Service Status)
```

---

## 🔗 Прямое подключение к серверу

Если нужно выполнить команды вручную:

```powershell
.\connect_server.ps1
```

Или напрямую:

```powershell
ssh root@89.167.70.67
```

---

## 📚 Дополнительная документация

Подробная информация в файле `SERVER_MANAGEMENT.md`

---

## 🆘 Экстренная помощь

### Быстрая перезагрузка всего

```powershell
ssh root@89.167.70.67 "systemctl restart postgresql redis minitms-backend minitms-frontend"
```

### Проверка что работает

```powershell
ssh root@89.167.70.67 "systemctl status minitms-backend minitms-frontend postgresql redis"
```

### Просмотр ошибок

```powershell
ssh root@89.167.70.67 "journalctl -u minitms-backend -n 50 --no-pager"
```

---

## ✨ Полезные ссылки

После успешного запуска доступны:

- **Backend API:** http://89.167.70.67:8000
- **API Docs:** http://89.167.70.67:8000/docs
- **Frontend:** http://89.167.70.67:3000 (или :80)

---

**Готово! Теперь вы можете управлять сервером MiniTMS.**
