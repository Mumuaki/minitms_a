# Use Case Specification: Fleet Management

## 1. Введение
Управление транспортными средствами (ТС) и их геопозицией.

## 2. Use Cases

### UC-FLEET-01: Manage Vehicle Profile (Управление профилем ТС)
* **Actor:** Administrator, Director, Dispatcher.
* **Data Structure:**
    * `RegNumber`: Госномер.
    * `BodyType`: Тип кузова (Тент, Фургон).
    * `Dimensions`: L x W x H (например, 4.8 x 2.4 x 2.2 м).
    * `Capacity`: Грузоподъемность (например, 900 кг).
* **Validation:** Размеры в метрах, вес в кг.

### UC-FLEET-02: Update Location (Обновление геопозиции)
* **Actor:** Dispatcher (Manual) или System (GPS API Integration).
* **Scenario A: Manual/Force Update**
    1. Пользователь нажимает "Обновить местоположение".
    2. Система запрашивает API GPS-провайдера (Wialon/Navixy).
    3. Получает координаты (`lat`, `lon`).
    4. Выполняет Reverse Geocoding (через OSM/Nominatim) -> `Place Name`, `Country`.
    5. Сохраняет в `VehiclePosition` с `timestamp`.
    6. UI обновляет строку статуса ТС.

### UC-FLEET-03: Set Status (Установка статуса)
* **Actor:** Dispatcher.
* **Values:** `Свободен` (Ready), `В рейсе` (Busy), `На ТО` (Maintenance), `Недоступен`.
* **Logic:** Только ТС со статусом `Свободен` участвуют в алгоритме автоматического поиска грузов.