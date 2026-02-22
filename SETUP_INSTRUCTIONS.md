# 🔧 MiniTMS Server - Setup Instructions

## ⚠️ Важная информация

При запуске скриптов из Cursor IDE могут возникать ограничения сетевого доступа. Рекомендуется запускать скрипты напрямую из **Windows PowerShell** или **Windows Terminal**.

---

## 🚀 Быстрый старт (3 шага)

### Шаг 1: Откройте PowerShell

**Вариант A: Windows PowerShell**
1. Нажмите `Win + X`
2. Выберите "Windows PowerShell" или "Windows Terminal"

**Вариант B: Через проводник**
1. Откройте папку `d:\MiniTMS` в проводнике
2. В адресной строке введите `powershell` и нажмите Enter

### Шаг 2: Перейдите в папку проекта

```powershell
cd d:\MiniTMS
```

### Шаг 3: Запустите скрипт

**Рекомендуется начать с:**

```powershell
.\launcher.ps1
```

Или для быстрой проверки:

```powershell
.\check_server.ps1
```

---

## 🔐 Проверка SSH подключения

Перед запуском скриптов убедитесь, что SSH подключение работает:

```powershell
ssh root@89.167.70.67
```

**Ожидаемый результат:**
- Успешное подключение к серверу
- Появление командной строки сервера

**Если не работает:**
1. Проверьте SSH ключ: `ls ~/.ssh/`
2. Проверьте доступность сервера: `ping 89.167.70.67`
3. Проверьте конфигурацию SSH: `cat ~/.ssh/config`

---

## 📋 Доступные команды

### Интерактивное меню (рекомендуется)
```powershell
.\launcher.ps1
```

### Диагностика

**Быстрая проверка (30 сек):**
```powershell
.\check_server.ps1
```

**Детальная проверка модулей (1-2 мин):**
```powershell
.\check_modules.ps1
```

**Проверка бизнес-требований (2-3 мин):**
```powershell
.\test_business_requirements.ps1
```

**Тестирование функций (1-2 мин):**
```powershell
.\test_features.ps1
```

**Полная диагностика с отчетом (5-7 мин):**
```powershell
.\run_full_diagnostic.ps1
```

### Управление

**Интерактивное меню исправлений:**
```powershell
.\fix_server.ps1
```

**Прямое SSH подключение:**
```powershell
.\connect_server.ps1
```

---

## 🛡️ Политика выполнения PowerShell

Если при запуске скриптов появляется ошибка о политике выполнения:

```
.\launcher.ps1 : File cannot be loaded because running scripts is disabled on this system.
```

**Решение:**

```powershell
# Проверить текущую политику
Get-ExecutionPolicy

# Установить политику для текущего пользователя
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Подтвердить изменение (Y)
```

После этого скрипты должны запускаться без проблем.

---

## 🔍 Проверка работы скриптов

### Тест 1: Проверка файлов
```powershell
Get-ChildItem -Path "d:\MiniTMS" -Filter "*.ps1" | Select-Object Name
```

**Ожидаемый результат:** Список всех .ps1 файлов

### Тест 2: Проверка SSH
```powershell
ssh root@89.167.70.67 "echo 'Test successful'"
```

**Ожидаемый результат:** `Test successful`

### Тест 3: Запуск скрипта
```powershell
.\check_server.ps1
```

**Ожидаемый результат:** Вывод диагностической информации

---

## 🐛 Troubleshooting

### Проблема: "ssh: command not found"

**Причина:** SSH клиент не установлен

**Решение:**
1. Откройте "Settings" → "Apps" → "Optional Features"
2. Найдите "OpenSSH Client"
3. Если не установлен - нажмите "Add a feature" и установите

Или через PowerShell:
```powershell
Add-WindowsCapability -Online -Name OpenSSH.Client~~~~0.0.1.0
```

### Проблема: "Connection timed out"

**Причина:** Сервер недоступен или файрвол блокирует

**Решение:**
1. Проверьте доступность: `ping 89.167.70.67`
2. Проверьте порт SSH: `Test-NetConnection -ComputerName 89.167.70.67 -Port 22`
3. Проверьте файрвол Windows
4. Проверьте VPN/прокси настройки

### Проблема: "Permission denied (publickey)"

**Причина:** SSH ключ не найден или неправильный

**Решение:**
1. Проверьте наличие ключа: `ls ~/.ssh/`
2. Проверьте права на ключ: `icacls ~/.ssh/id_rsa`
3. Попробуйте указать ключ явно:
```powershell
ssh -i ~/.ssh/id_rsa root@89.167.70.67
```

### Проблема: Скрипт запускается, но ничего не происходит

**Причина:** Скрипт ожидает ввода или завис

**Решение:**
1. Нажмите Ctrl+C для прерывания
2. Проверьте SSH подключение отдельно
3. Запустите скрипт с параметром verbose:
```powershell
.\check_server.ps1 -Verbose
```

---

## 📊 Интерпретация результатов

### Успешная проверка
```
✓ SSH connection successful
✓ PostgreSQL - OK
✓ Redis - OK
✓ Backend - OK
✓ Frontend - OK
```

### Предупреждения
```
⚠ HTTP Status: 401 - Authentication required (это нормально для защищенных endpoints)
⚠ Service not found - сервис может быть запущен вручную
```

### Ошибки
```
✗ Connection refused - сервис не запущен
✗ HTTP Status: 500 - внутренняя ошибка сервера
✗ Database connection failed - проблемы с БД
```

---

## 🎯 Рекомендуемый порядок действий

### Первый запуск:

1. **Откройте PowerShell** (не из Cursor, а нативный Windows PowerShell)
2. **Перейдите в папку:**
   ```powershell
   cd d:\MiniTMS
   ```
3. **Проверьте SSH:**
   ```powershell
   ssh root@89.167.70.67 "echo 'OK'"
   ```
4. **Запустите launcher:**
   ```powershell
   .\launcher.ps1
   ```
5. **Выберите опцию 1** (Quick Server Check)
6. **Изучите результаты**

### Если SSH не работает:

1. **Проверьте доступность сервера:**
   ```powershell
   ping 89.167.70.67
   Test-NetConnection -ComputerName 89.167.70.67 -Port 22
   ```

2. **Проверьте SSH ключ:**
   ```powershell
   ls ~/.ssh/
   ```

3. **Попробуйте подключиться вручную:**
   ```powershell
   ssh -v root@89.167.70.67
   ```

4. **Если нужен пароль вместо ключа:**
   - Отредактируйте скрипты, заменив `ssh root@89.167.70.67` на `ssh -o PreferredAuthentications=password root@89.167.70.67`

---

## 📞 Дополнительная помощь

### Полезные команды для диагностики:

```powershell
# Проверка версии PowerShell
$PSVersionTable

# Проверка политики выполнения
Get-ExecutionPolicy -List

# Проверка SSH клиента
ssh -V

# Проверка сетевого подключения
Test-NetConnection -ComputerName 89.167.70.67 -Port 22

# Проверка DNS
nslookup 89.167.70.67

# Трассировка маршрута
tracert 89.167.70.67
```

---

## 🔗 Быстрые ссылки

После успешного запуска сервера:

- **Backend API:** http://89.167.70.67:8000
- **API Docs:** http://89.167.70.67:8000/docs
- **Frontend:** http://89.167.70.67:3000

---

## ✅ Чеклист готовности

Перед запуском скриптов убедитесь:

- [ ] PowerShell установлен (версия 5.1+)
- [ ] SSH клиент установлен
- [ ] SSH ключ настроен
- [ ] Сервер доступен (ping работает)
- [ ] Порт 22 открыт (Test-NetConnection)
- [ ] Политика выполнения разрешает скрипты
- [ ] Вы находитесь в папке d:\MiniTMS

---

## 🎓 Альтернативный метод (без скриптов)

Если скрипты не работают, вы можете выполнять команды вручную:

```powershell
# Подключение к серверу
ssh root@89.167.70.67

# На сервере выполните:
systemctl status minitms-backend
systemctl status minitms-frontend
systemctl status postgresql
systemctl status redis

# Проверка API
curl http://localhost:8000/health

# Проверка процессов
ps aux | grep uvicorn
ps aux | grep node

# Просмотр логов
journalctl -u minitms-backend -n 50
```

---

**Готово! Теперь вы готовы к работе с сервером MiniTMS.**

**Начните с:** Открытие PowerShell → `cd d:\MiniTMS` → `.\launcher.ps1`
