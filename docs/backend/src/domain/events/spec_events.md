# Domain Events Specification

В этом документе описаны доменные события (Domain Events), возникающие в системе MiniTMS. События служат для обеспечения слабой связности между компонентами (например, расчет прибыльности после скрапинга или синхронизация с Google Sheets после создания заказа).

## 1. Общие принципы
Все события наследуются от базового класса `DomainEvent` и содержат:
- `eventId`: UUID события.
- `occurredOn`: Дата и время возникновения (UTC).
- `aggregateId`: ID сущности, породившей событие.

## 2. События домена Cargo (Грузы)

### `CargoScraped`
Возникает, когда сервис скрапинга успешно получает и нормализует новый груз с Trans.eu.
* **Контекст:** Модуль скрапинга, обновление базы предложений.
* **Payload:**
    * `cargoId`: UUID
    * `transEuId`: String (внешний ID)
    * `route`: { loadingPoint: GeoLocation, unloadingPoint: GeoLocation }
    * `offerDetails`: { price: Money, weight: Weight }
* **Обработчики (Listeners):**
    * `ProfitabilityCalculator`: Запускает расчет рентабельности (€/км).
    * `FilterMatcher`: Проверяет соответствие автопарку.

### `HighProfitabilityCargoFound`
Возникает, когда рассчитанная ставка €/км превышает порог "Зеленой зоны" (≥ 0.80 €/км) или пользовательский лимит.
* **Контекст:** Модуль уведомлений.
* **Payload:**
    * `cargoId`: UUID
    * `ratePerKm`: float (0.85)
    * `loadingLocation`: String ("Berlin, DE")
* **Обработчики:**
    * `NotificationService`: Отправляет Push/Telegram уведомление диспетчеру.

## 3. События домена Order (Заказы)

### `OrderCreated`
Возникает, когда диспетчер нажимает "Заключить сделку" и сохраняет данные заказа в системе.
* **Контекст:** Фиксация сделки.
* **Payload:**
    * `orderId`: UUID
    * `customerName`: String
    * `agreedPrice`: Money
    * `routeDetails`: { distanceOsm: float, distanceTrans: float }
    * `dates`: { loading: Date, unloading: Date }
* **Обработчики:**
    * `GoogleSheetsSyncService`: Создает новую строку в таблице "Заказы" (заполняет 16 автоматических полей).
    * `FinancialService`: Обновляет фактическую выручку в финансовом плане.

### `OrderStatusChanged`
Возникает при смене статуса (например, "В работе" -> "Выгружен").
* **Payload:**
    * `orderId`: UUID
    * `oldStatus`: OrderStatus
    * `newStatus`: OrderStatus
* **Обработчики:**
    * `GoogleSheetsSyncService`: Обновляет соответствующую ячейку в таблице.

## 4. События домена Fleet & GPS (Автопарк)

### `VehicleLocationUpdated`
Возникает, когда система получает новые координаты от GPS-провайдера или по ручному обновлению.
* **Контекст:** Обновление позиции для поиска грузов.
* **Payload:**
    * `vehicleId`: UUID
    * `location`: GeoLocation (lat, lon)
    * `address`: String (Reverse Geocoding result: "Paris, FR")
    * `timestamp`: DateTime
* **Обработчики:**
    * `CargoSearchService`: Пересчитывает расстояние "порожнего пробега" (Deadhead) до ближайших грузов.

### `PlanDeviationDetected`
Возникает, когда фактические показатели ТС (выручка/пробег) отклоняются от плана более чем на 10% или 20%.
* **Контекст:** Финансовое планирование (BR-020, BR-021).
* **Payload:**
    * `vehicleId`: UUID
    * `metric`: String ("Revenue", "Margin")
    * `deviationPercent`: float (e.g., -15.0)
    * `severity`: Enum (WARNING, CRITICAL)
* **Обработчики:**
    * `DashboardService`: Меняет цвет индикатора (Желтый/Красный).
    * `NotificationService`: Отправляет алерт директору (при Critical).

## 5. События домена Communication (Email)

### `EmailLimitWarning`
Возникает, когда количество отправленных писем за последний час достигает 80% (40 писем).
* **Контекст:** FR-EMAIL-010.
* **Payload:**
    * `userId`: UUID
    * `currentCount`: int (40)
* **Обработчики:**
    * `UserInterface`: Показывает предупреждение диспетчеру.

### `EmailLimitExceeded`
Возникает при попытке отправить письмо сверх лимита (50/час).
* **Контекст:** FR-EMAIL-009.
* **Payload:**
    * `userId`: UUID
    * `attemptedAt`: DateTime
* **Обработчики:**
    * `EmailService`: Блокирует отправку.
    * `SecurityLog`: Записывает инцидент.