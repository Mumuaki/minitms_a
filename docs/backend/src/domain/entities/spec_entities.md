# Спецификация: Domain Entities (spec_entities.md)

## 1. Введение
Данный документ описывает основные доменные сущности системы MiniTMS. Сущности являются ядром бизнес-логики и не должны зависеть от фреймворков или деталей реализации базы данных (Persistence Ignorance).

---

## 2. Сущности (Entities)

### 2.1. User (Пользователь)
Представляет пользователя системы с определенными правами доступа.

**Атрибуты:**
    * `id`: UUID (Primary Key)
    * `login`: String (Unique)
    * `password_hash`: String (Bcrypt)
    * `role`: Enum (`ADMINISTRATOR`, `DIRECTOR`, `DISPATCHER`, `OBSERVER`)
    * `language`: Enum (`RU`, `EN`, `SK`, `PL`) — дефолтное предпочтение интерфейса
    * `last_login`: Timestamp
    * `failed_login_attempts`: Integer (для блокировки после 5 попыток)
    * `is_blocked`: Boolean
    * `notification_settings`: JSON (Telegram ID, Email preferences)

### 2.2. Vehicle (Транспортное средство)
Представляет физический грузовик или фургон из автопарка компании.

**Атрибуты:**
    * `id`: UUID (Primary Key)
    * `registration_number`: String (Госномер)
    * `type`: String (Тип кузова: Тент, Фургон, Реф и т.д.)
    * `dimensions`: Object (Value Object)
        * `length`: Float (м)
        * `width`: Float (м)
        * `height`: Float (м)
    * `capacity_weight`: Integer (кг)
    * `status`: Enum (`AVAILABLE`, `IN_TRANSIT`, `MAINTENANCE`, `UNAVAILABLE`) 
    * `gps_tracker_id`: String (ID внешнего трекера Wialon/Navixy)
    * `current_position_id`: Link -> `VehiclePosition` (последняя известная позиция)

### 2.3. VehiclePosition (GPS Позиция)
Хранит историю и текущее состояние местоположения ТС. Используется как точка "А" для поиска грузов.

**Атрибуты:**
    * `id`: UUID
    * `vehicle_id`: UUID (Foreign Key)
    * `latitude`: Float
    * `longitude`: Float
    * `place_name`: String (Населенный пункт после обратного геокодирования)
    * `country`: String (ISO код страны)
    * `measured_at`: Timestamp (Время получения координат с GPS)
    * `updated_at`: Timestamp (Время сохранения в системе)

### 2.4. Cargo (Найденный груз / OffersNormalized)
Представляет "сырое" или обработанное предложение груза, полученное через парсинг Trans.eu.

**Атрибуты:** 
    * `id`: UUID
    * `external_id`: String (ID предложения на Trans.eu)
    * `source`: String (Default: "trans.eu")
    * `loading_place`: Object
        * `city`: String
        * `zip`: String
        * `country`: String
        * `coordinates`: Point (Lat, Lon)
    * `unloading_place`: Object
        * `city`: String
        * `zip`: String
        * `country`: String
        * `coordinates`: Point (Lat, Lon)
    * `loading_date`: Date
    * `unloading_date`: Date
    * `weight`: Float (кг)
    * `body_type`: String
    * `price`: Decimal (€)
    * `distance_trans_eu`: Integer (км)
    * `distance_google`: Integer (км) (Рассчитанное через Google Maps API)
    * `profitability`: Object (Value Object)
    * `rate_per_km`: Decimal (€/км) 
    * `total_cost`: Decimal (Себестоимость)
    * `status_color`: Enum (`RED`, `GRAY`, `YELLOW`, `GREEN`)
    *`is_hidden`: Boolean (Флаг "Удалено пользователем") 

### 2.5. Order (Заказ / Сделка)
Представляет подтвержденную перевозку. Эта сущность синхронизируется с Google Sheets.

**Атрибуты:**
    * `id`: UUID
    * `cargo_id`: UUID (Ссылка на исходное предложение)
    * `vehicle_id`: UUID (Исполнитель)
    * `status`: Enum (`CREATED`, `IN_PROGRESS`, `DELIVERED`, `PAID`, `CANCELLED`)
    * `customer_name`: String 
    * `contact_person`: String 
    * `invoice_amount`: Decimal (€) (Сумма в инвойс) 
    * `invoice_number`: String (Номер инвойса - заполняется вручную)
    * `cmr_number`: String (Номер СМР - заполняется вручную)
    * `documents`: Object
        * `scan_url`: String (Ссылка на сканы)
        * `originals_received`: Boolean
        * `originals_sent_to_client`: Boolean
        * `sent_via_email`: Boolean
    * `dates_actual`: Object
        * `etr`: Date (Estimated Time of Pickup)
        * `atr`: Date (Actual Time of Pickup)

### 2.6. Plan (Финансовый план)
Плановые показатели на месяц для конкретного транспортного средства.

**Атрибуты:**
    * `id`: UUID
    * `vehicle_id`: UUID
    * `month`: Date (Месяц/Год)
    * `target_revenue`: Decimal (€) (Плановая выручка)
    * `target_margin`: Decimal (€) (Плановая маржа)
    * `target_mileage`: Integer (км) (Плановый пробег)
    * `fact_revenue`: Decimal (€) (Фактическая выручка - агрегат по Orders)
    * `fact_mileage`: Integer (км) (Фактический пробег - агрегат по GPS Odometer)


## 3. Value Objects (Объекты-значения)

### 3.1. Coordinates
* `latitude`: Float
* `longitude`: Float

### 3.2. Dimensions
* `length`: Float
* `width`: Float
* `height`: Float

### 3.3. Money
* `amount`: Decimal
* `currency`: String (Всегда 'EUR')