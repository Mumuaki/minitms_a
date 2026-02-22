# ?? MiniTMS Server Management

> Полный набор инструментов для управления сервером MiniTMS на **89.167.70.67**

---

## ? Быстрый старт (30 секунд)

```powershell
# 1. Откройте Windows PowerShell (Win + X)
# 2. Перейдите в папку:
cd d:\MiniTMS

# 3. Запустите:
.\launcher.ps1
```

**Или для быстрой проверки:**

```powershell
.\check_server.ps1
```

---

## ?? Документация

| Файл | Для кого | Время чтения |
|------|----------|--------------|
| **START_HERE.md** | Новички | 2 мин |
| **SETUP_INSTRUCTIONS.md** | Все | 5 мин |
| **QUICK_START.md** | Все | 5 мин |
| **INDEX.md** | Все | 5 мин |
| **VISUAL_GUIDE.txt** | Визуалы | 10 мин |
| **README_SERVER_SCRIPTS.md** | Детали | 20 мин |
| **SERVER_MANAGEMENT.md** | Админы | 30 мин |
| **SUMMARY.md** | Обзор | 10 мин |

---

## ?? Основные скрипты

### Интерактивное меню
```powershell
.\launcher.ps1          # Главное меню со всеми функциями
```

### Диагностика
```powershell
.\check_server.ps1                    # Быстрая проверка (30 сек)
.\check_modules.ps1                   # 10 модулей (1-2 мин)
.\test_business_requirements.ps1      # Бизнес-требования (2-3 мин)
.\test_features.ps1                   # 20 функций (1-2 мин)
.\run_full_diagnostic.ps1             # Полный отчет (5-7 мин)
```

### Управление
```powershell
.\fix_server.ps1        # 20 опций для исправления проблем
.\connect_server.ps1    # Прямое SSH подключение
```

---

## ?? Что проверяется

? **10 модулей MiniTMS**
? **PostgreSQL, Redis, Backend, Frontend**
? **Trans.eu, GPS Dozor, Google Sheets**
? **Email, Financial Planning, Settings**

---

## ?? Рекомендации

### Ежедневно (5 мин)
```powershell
.\check_server.ps1
```

### Еженедельно (15 мин)
```powershell
.\check_modules.ps1
```

### Ежемесячно (30 мин)
```powershell
.\run_full_diagnostic.ps1
```

### При проблемах
```powershell
.\fix_server.ps1
```

---

## ?? Ссылки

- **Backend:** http://89.167.70.67:8000
- **API Docs:** http://89.167.70.67:8000/docs
- **Frontend:** http://89.167.70.67

---

## ?? Важно

**Запускайте из нативного PowerShell**, а не из Cursor IDE!

1. Нажмите `Win + X`
2. Выберите "Windows PowerShell"
3. `cd d:\MiniTMS`
4. `.\launcher.ps1`

---

## ?? Помощь

**Проблемы с запуском?** > Читайте `SETUP_INSTRUCTIONS.md`  
**Не знаете с чего начать?** > Читайте `START_HERE.md`  
**Нужна навигация?** > Читайте `INDEX.md`  
**Backend не работает?** > Запустите `.\fix_server.ps1`

---

**Версия:** 1.0 | **Дата:** 2026-02-20 | **Статус:** ? Ready
