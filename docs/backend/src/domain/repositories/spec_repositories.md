# Domain Repositories Specification

Спецификация интерфейсов репозиториев для доступа к персистентным данным. Реализация этих интерфейсов находится в слое Infrastructure.

## 1. Cargo Repository (`ICargoRepository`)
Отвечает за хранение и поиск распарсенных грузов.

### Методы
* `save(cargo: Cargo): Promise<void>`
    * Сохраняет или обновляет информацию о грузе (upsert по `transEuId`).
* `findById(id: CargoId): Promise<Cargo | null>`
* `findMatching(filter: CargoFilterSpecification, currentVehiclePos: GeoLocation): Promise<Cargo[]>`
    * **Описание:** Основной метод поиска.
    * **Аргументы:**
        * `filter`: Включает радиус поиска (по умолчанию +75км), даты, тип кузова, вес.
        * `currentVehiclePos`: Координаты для сортировки по удаленности.
    * **Поведение:** Возвращает грузы, соответствующие фильтрам, с учетом исключенных (Blacklisted).
* `findProfitable(minRate: Money): Promise<Cargo[]>`
    * Возвращает грузы с рентабельностью выше указанной.

## 2. Vehicle Repository (`IVehicleRepository`)
Управление данными транспортных средств и их локацией.

### Методы
* `save(vehicle: Vehicle): Promise<void>`
* `findAll(): Promise<Vehicle[]>`
* `updateLocation(vehicleId: VehicleId, location: GeoLocation, address: string): Promise<void>`
    * **Описание:** Обновляет текущие координаты и сохраняет запись в историю перемещений (`VehiclePosition` entity).
* `findByGpsTrackerId(trackerId: string): Promise<Vehicle | null>`

## 3. Order Repository (`IOrderRepository`)
Хранение подтвержденных сделок.

### Методы
* `save(order: Order): Promise<void>`
    * Сохраняет заказ со статусом `CREATED`.
* `findByDateRange(startDate: Date, endDate: Date): Promise<Order[]>`
    * Используется для генерации отчетов.
* `getFinancialStats(vehicleId: VehicleId, month: int, year: int): Promise<FinancialStatsDTO>`
    * Агрегирует данные для расчета план/факт (выручка, маржа).

## 4. Email Log Repository (`IEmailLogRepository`)
Служебный репозиторий для контроля лимитов отправки.

### Методы
* `logSentEmail(emailMeta: EmailMetadata): Promise<void>`
* `countSentLastHour(userId: UserId): Promise<int>`
    * **Описание:** Критически важный метод для реализации BR-015 (Лимит 50 писем/час).
    * **Query:** `SELECT COUNT(*) FROM email_logs WHERE user_id = :id AND sent_at > NOW() - INTERVAL '1 hour'`.

## 5. User Settings Repository (`ISettingsRepository`)
Хранение настроек пользователя и черных списков.

### Методы
* `getBlacklistedCargoIds(userId: UserId): Promise<string[]>`
    * Возвращает список ID грузов, помеченных на удаление.
* `saveBlacklistedCargo(userId: UserId, cargoExternalId: string): Promise<void>`
* `getUserPreferences(userId: UserId): Promise<UserPreferences>`
    * Возвращает настройки: мин. ставка, шаблон email, API ключи.