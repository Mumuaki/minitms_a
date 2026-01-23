# Спецификация слоя хранения данных (Persistence Layer)

**СУБД:** PostgreSQL 15+
**ORM/Query Builder:** TypeORM / Prisma (в зависимости от выбора стека Node.js)
**Кэширование:** Redis (для сессий и результатов парсинга)

## 1. ER-диаграмма и Схема БД
Описание основных сущностей системы и их отображение в реляционную структуру.

### 1.1 Users (Пользователи)
Таблица `users`
* `id`: UUID (PK)
* `email`: VARCHAR(255) (Unique)
* `password_hash`: VARCHAR (bcrypt)
* `role`: ENUM ('Administrator', 'Director', 'Dispatcher', 'Observer')
* `settings`: JSONB (Настройки интерфейса, фильтры по умолчанию, язык)
* `trans_eu_credentials`: JSONB (Encrypted) - Логин/пароль для парсера.

### 1.2 Vehicles (Транспортные средства)
Таблица `vehicles`
* `id`: UUID (PK)
* `reg_number`: VARCHAR(20)
* `type`: VARCHAR(50) (Тент, Рэф, и т.д.)
* `dims_l`: DECIMAL (Длина, м)
* `dims_w`: DECIMAL (Ширина, м)
* `dims_h`: DECIMAL (Высота, м)
* `payload_kg`: INTEGER
* `gps_tracker_id`: VARCHAR (ID в системе Wialon/Navixy).

### 1.3 VehiclePositions (История GPS)
Таблица `vehicle_positions`
* `id`: BIGINT (PK)
* `vehicle_id`: UUID (FK -> vehicles.id)
* `latitude`: DECIMAL(10, 8)
* `longitude`: DECIMAL(11, 8)
* `place_name`: VARCHAR (Результат обратного геокодирования: Город)
* `country_code`: VARCHAR(2)
* `measured_at`: TIMESTAMP (Время на устройстве)
* `created_at`: TIMESTAMP (Время записи в БД)

### 1.4 OffersNormalized (Спарсенные грузы)
Таблица `offers`
* `id`: UUID (PK)
* `external_id`: VARCHAR (ID с Trans.eu)
* `vehicle_id`: UUID (Для какого ТС искали)
* `loading_place`: VARCHAR
* `loading_lat`: DECIMAL
* `loading_lon`: DECIMAL
* `unloading_place`: VARCHAR
* `unloading_lat`: DECIMAL
* `unloading_lon`: DECIMAL
* `price`: DECIMAL (NULLable)
* `distance_osm`: INTEGER (Рассчитанное расстояние в км)
* `profitability_eur_km`: DECIMAL (Рассчитанная ставка)
* `raw_data`: JSONB (Полный слепок данных с парсера)
* `is_hidden`: BOOLEAN (Default: false)

### 1.5 FinancialPlans (Планирование)
Таблица `financial_plans`
* `id`: UUID (PK)
* `vehicle_id`: UUID (FK)
* `month`: DATE (Начало месяца)
* `target_revenue`: DECIMAL
* `target_margin`: DECIMAL
* `target_mileage`: INTEGER
* `fact_revenue`: DECIMAL (Обновляется триггером или сервисом)
* `fact_mileage`: INTEGER (Агрегация из GPS)

## 2. Репозитории (Repositories Implementation)
Реализация паттерна Repository для абстракции доступа к данным.

* **`PostgresVehicleRepository`**: Реализует `IVehicleRepository`. Методы: `save`, `findById`, `updateStatus`.
* **`PostgresOfferRepository`**: Реализует `IOfferRepository`. Методы: `saveBatch` (для массовой вставки после парсинга), `findActiveByVehicle` (с фильтрацией по Blacklist).
* **`GPSLogRepository`**: Оптимизирован для записи time-series данных (или использование TimescaleDB расширения при необходимости).

## 3. Миграции
Управление схемой базы данных осуществляется через миграции.
* Путь: `src/infrastructure/persistence/migrations`
* Команды: `run`, `revert`, `create`.
* Версионирование обязательно при изменении структуры `users` или `offers`.

## 4. Резервное копирование
* **Тип:** `pg_dump`
* **Расписание:** Ежедневно в 03:00 UTC.
* **Хранение:** S3-совместимое хранилище (хранить последние 30 дней).