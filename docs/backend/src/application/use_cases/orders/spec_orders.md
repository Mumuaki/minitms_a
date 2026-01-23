# Use Case Specification: Orders & Deals

## 1. Введение
Процесс превращения найденного "Груза" в "Заказ", фиксация договоренностей и синхронизация с отчетностью.

## 2. Use Cases

### UC-ORDER-01: Create Order (Заключение сделки)
* **Actor:** Dispatcher.
* **Input:** Выбранный груз (ID), Контрагент, Финальная цена (Rate).
* **Flow:**
    1. Диспетчер нажимает "Заключить сделку" в карточке груза.
    2. Открывается форма предзаполненная данными из парсера (Маршрут, Вес, Даты).
    3. Диспетчер вводит: Название клиента, Контактное лицо, Согласованную ставку.
    4. Система сохраняет `Order` в БД.
    5. Система инициирует событие `OrderCreated`.

### UC-ORDER-02: Sync to Google Sheets (Экспорт в Google Таблицу)
* **Actor:** System (Triggered by UC-ORDER-01).
* **Requirements:**
    * Использование Google Sheets API v4.
    * Аутентификация через OAuth 2.0 / Service Account.
* **Mapping Rules (24 колонки):**
    * **Auto-fill:** Дата загрузки (A), Источник (B="trans.eu"), Заказчик (C), Номер заявки (D), Сумма (E), Места (G, H), Дистанция Trans (I), OSM Dist (J), Даты (L, X, Y), Вес (M), Маршрут URL (N), Контакт (P).
    * **Calculated Fields:**
        * `€/km` (O) = `Column E` / `Column J`.
        * `Days` (S) = `Date Unload` - `Date Load`.
* **Logic:** Добавить новую строку, применить форматирование, сохранить ID строки в БД для возможности обновления (Two-way sync requirement FR-GSHEET-006).

### UC-ORDER-03: Send Proposal (Отправка КП)
* **Actor:** Dispatcher.
* **Flow:**
    1. Генерация PDF или тела письма на основе шаблона.
    2. Подстановка переменных: `{company_name}`, `{route}`, `{price}`.
    3. Постановка в очередь отправки `email.sending` с проверкой квот.