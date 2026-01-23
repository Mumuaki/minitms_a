# Specification: Application Ports

Порты определяют границы приложения. Use Cases реализуют Input Ports, а Infrastructure реализует Output Ports.

## 1. Input Ports (Primary / Driver)
Интерфейсы, через которые внешние акторы (API Controller, CLI) взаимодействуют с приложением.

### `SearchCargoUseCase`
Интерфейс для сценария поиска грузов (UC-001).
* `execute(vehicleId: UUID, filters: FilterCriteria): List<CargoOfferDto>` — Запускает поиск грузов для конкретного ТС, учитывая его GPS-позицию и характеристики.

### `CreateVehicleUseCase`
Интерфейс для добавления ТС (UC-002).
* `execute(request: CreateVehicleRequest): VehicleDto`

### `SyncOrderToSheetUseCase`
Интерфейс для синхронизации заказа (UC-005).
* `execute(orderId: UUID): void` — Триггерит отправку данных заказа в Google Sheets.

### `UpdatePlanUseCase`
Интерфейс для установки фин. плана (UC-004).
* `execute(plan: PlanDto): void`

### `GeneratePlanFactReportUseCase`
Интерфейс для генерации отчетов (UC-008).
* `execute(month: String): List<PlanFactReportDto>`

## 2. Output Ports (Secondary / Driven)
Интерфейсы, которые приложение использует для доступа к данным и внешним сервисам.

### 2.1 Repositories (Persistence)
* `VehicleRepository`: методы `save`, `findById`, `findAll`, `updateStatus`.
* `OrderRepository`: методы `save`, `findByDateRange`, `sumRevenueByVehicle`.
* `PlanRepository`: методы `save`, `findByVehicleAndMonth`.
* `GpsHistoryRepository`: сохранение истории перемещений для расчета пробега.

### 2.2 External Services

#### `TransEuScraperPort`
Абстракция над модулем парсинга Trans.eu.
* `login(credentials: AuthData): SessionToken`
* `fetchOffers(criteria: SearchCriteria, token: SessionToken): List<RawOfferData>` — Получение сырых данных предложений.
* *Note:* Реализация должна обрабатывать отсутствие API и использовать парсинг DOM.

#### `GeoServicePort` (OSM / Nominatim)
Абстракция над картографическими сервисами (OpenStreetMap).
* `calculateDistance(origin: Location, destination: Location): DistanceResult` — Расчет точного пробега (OSRM).
* `geocode(address: String): Location` — Получение координат по адресу (Nominatim).
* `reverseGeocode(lat: Float, lon: Float): Location` — Получение адреса по координатам (для GPS).

#### `GpsServicePort`
Интеграция с Wialon/Navixy.
* `getCurrentCoordinates(vehicleId: String): LocationDto` — Получение текущей точки (lat/lon).
* `getDailyMileage(vehicleId: String, date: Date): Float` — Расчет пробега за сутки (одометр 23:59 - 00:00).

#### `GoogleSheetsPort`
Интеграция с таблицами.
* `appendRow(spreadsheetId: String, row: OrderSheetRowDto): void` — Добавление новой строки заказа.
* `updateRow(spreadsheetId: String, rowNumber: Int, data: Partial<OrderSheetRowDto>): void`
* `ensureHeaderStructure(spreadsheetId: String): void` — Проверка наличия 24 столбцов.

#### `NotificationPort`
Отправка уведомлений.
* `sendPush(userId: UUID, message: String)`
* `sendTelegram(chatId: String, message: String)`
* `sendEmail(to: String, subject: String, body: String, attachments: List<File>)` — С учетом лимитов (50/час).