# Specification: Data Transfer Objects (DTO)

Этот документ описывает структуры данных (DTO), используемые для передачи информации между слоями приложения. DTO не содержат бизнес-логики.

## 1. Fleet & Vehicle DTOs
Используются в модуле управления автопарком.

### `VehicleDto`
Основной объект передачи данных о транспортном средстве.
* **id**: UUID (String) — Уникальный идентификатор
* **plate_number**: String — Госномер
* **type**: Enum (TENT, FRIDGE, VAN) — Тип кузова
* **dimensions**: `VehicleDimensionsDto` — Габариты
* **max_weight**: Float — Грузоподъемность (кг)
* **status**: Enum (FREE, BUSY, MAINTENANCE, N/A) — Текущий статус
* **gps_device_id**: String? — ID привязанного трекера

### `VehicleDimensionsDto`
Вложенный объект для размеров кузова.
* **length**: Float — Длина (м)
* **width**: Float — Ширина (м)
* **height**: Float — Высота (м)

### `CreateVehicleRequest`
Запрос на создание нового ТС (UC-002).
* **plate_number**: String (Required)
* **type**: String (Required)
* **dimensions**: `VehicleDimensionsDto` (Required)
* **max_weight**: Float (Required)

## 2. Cargo & Scraping DTOs
Используются для работы с данными, полученными от парсера Trans.eu.

### `CargoOfferDto`
Нормализованное предложение груза с Trans.eu.
* **external_id**: String — ID предложения на Trans.eu
* **source**: String — Источник (по умолчанию "trans.eu")
* **loading_location**: `LocationDto` — Место загрузки
* **unloading_location**: `LocationDto` — Место выгрузки
* **loading_date**: Date (ISO8601) — Дата загрузки
* **unloading_date**: Date (ISO8601) — Дата выгрузки
* **weight**: Float — Вес груза (т)
* **price**: MoneyDto? — Цена (если указана)
* **body_type**: String — Требуемый тип кузова
* **distance_route**: Float — Расстояние по данным биржи (км)
* **calculated_distance**: Float — Расстояние через OSM (A→B + B→C)
* **profitability**: `ProfitabilityDto` — Рассчитанные показатели

### `LocationDto`
Географическая точка (для использования с GPS и картами).
* **address**: String — Текстовое представление (Город, Страна, Индекс)
* **country_code**: String (ISO 2)
* **lat**: Float — Широта
* **lon**: Float — Долгота

### `ProfitabilityDto`
Результат работы сервиса расчетов (Module 4).
* **rate_per_km**: Float — Ставка €/км
* **empty_run_km**: Float — Порожний пробег от текущей позиции
* **total_distance**: Float — Полный пробег
* **color_code**: Enum (RED, GRAY, YELLOW, GREEN) — Индикатор рентабельности

## 3. Planning & Finance DTOs
Используются в модуле финансового планирования (Module 12).

### `PlanDto`
Плановые показатели на месяц.
* **vehicle_id**: UUID
* **month**: String (YYYY-MM)
* **target_revenue**: Float — Плановая выручка (€)
* **target_margin**: Float — Плановая маржа (€)
* **target_mileage**: Float — Плановый пробег (км)

### `PlanFactReportDto`
Отчет план/факт для Dashboard (UC-008).
* **revenue**: `MetricComparisonDto`
* **margin**: `MetricComparisonDto`
* **mileage**: `MetricComparisonDto`
* **average_rate_fact**: Float — Фактическая средняя ставка (€/км)

### `MetricComparisonDto`
* **planned**: Float
* **actual**: Float
* **percentage**: Float — % выполнения

## 4. Google Sheets Integration DTOs
Для синхронизации с таблицами "Заказы" (24 столбца).

### `OrderSheetRowDto`
Отражает структуру строки в Google Sheets.
* **loading_date**: String (Col A)
* **source**: String (Col B)
* **customer**: String (Col C)
* **order_ref**: String (Col D)
* **invoice_amount**: Float (Col E)
* **invoice_number**: String (Col F)
* **loading_place**: String (Col G)
* **unloading_place**: String (Col H)
* **trans_distance**: Float (Col I)
* **osm_distance**: Float (Col J)
* **cmr_number**: String (Col K)
* **unloading_actual_date**: String (Col L)
* **weight**: Float (Col M)
* **route_link**: String (Col N)
* **rate_calc**: Float (Col O)
* **contact_info**: String (Col P)