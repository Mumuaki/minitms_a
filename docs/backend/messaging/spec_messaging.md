# Specification: Messaging & Event Bus

## 1. Обзор
Система использует асинхронный обмен сообщениями для выполнения длительных операций (парсинг, отчеты) и обеспечения надежности внешних интеграций (Email, Telegram). Реализуется через Message Broker (RabbitMQ).

## 2. Очереди (Queues)

### 2.1. `scraping.tasks`
Очередь для задач по сбору данных с Trans.eu.
* **Producer:** `ScrapingScheduler` (cron jobs), `UserAction` (ручное обновление).
* **Consumer:** `ScrapingService`.
* **Payload:**
    ```json
    {
      "vehicle_id": "uuid",
      "filters": {
        "loading_location": { "lat": 50.0, "lon": 19.0, "radius": 75 },
        "dates": ["2026-01-22", "2026-01-23"]
      }
    }
    ```
* **Приоритет:** Высокий для ручных запросов, Низкий для фоновых.

### 2.2. `notifications.alerts`
Очередь для отправки уведомлений о выгодных грузах.
* **Producer:** `ProfitabilityService` (после ранжирования грузов).
* **Consumer:** `TelegramBotService`, `PushService`.
* **Rate Limiting:** Группировка уведомлений, не чаще 1 раза в 5 минут для одного пользователя.

### 2.3. `email.sending`
Очередь для отправки коммерческих предложений и документов.
* **Producer:** `OrderService`.
* **Consumer:** `SmtpService`.
* **Throttling:** Строгий лимит отправки.
    * Макс. 50 писем/час.
    * Мин. интервал 30 сек между письмами.

### 2.4. `google.sheets.sync`
Очередь для синхронизации заказов с таблицами.
* **Producer:** `OrderService` (при создании/изменении заказа).
* **Consumer:** `GoogleSheetsAdapter`.
* **Retry Policy:** Экспоненциальная задержка при ошибках API Google (429 Too Many Requests).

## 3. События домена (Domain Events)

| Событие | Описание | Подписчики |
| :--- | :--- | :--- |
| `CargoFound` | Найден новый груз с Trans.eu | `ProfitabilityService` |
| `ProfitabilityCalculated` | Расчитана ставка €/км | `NotificationService` |
| `OrderCreated` | Создан новый заказ | `GoogleSheetsSync`, `EmailService` |
| `VehicleMoved` | Обновлены GPS координаты | `ScrapingService` (триггер пересчета) |