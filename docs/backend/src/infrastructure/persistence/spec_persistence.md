> [!NOTE]
> **Внимание:** Базовые архитектурные решения (включая выбор БД, шины сообщений, GPS-провайдера и единиц измерения) зафиксированы в PROJECT-CONFIG.md. Любые расхождения в данной спецификации следует трактовать в пользу центрального конфига.

# РЎРїРµС†РёС„РёРєР°С†РёСЏ СЃР»РѕСЏ С…СЂР°РЅРµРЅРёСЏ РґР°РЅРЅС‹С… (Persistence Layer)

**РЎРЈР‘Р”:** PostgreSQL 15+
**ORM/Query Builder:** SQLAlchemy + Alembic (Python)
**РљСЌС€РёСЂРѕРІР°РЅРёРµ:** Redis (РґР»СЏ СЃРµСЃСЃРёР№ Рё СЂРµР·СѓР»СЊС‚Р°С‚РѕРІ РїР°СЂСЃРёРЅРіР°)

## 1. ER-РґРёР°РіСЂР°РјРјР° Рё РЎС…РµРјР° Р‘Р”
РћРїРёСЃР°РЅРёРµ РѕСЃРЅРѕРІРЅС‹С… СЃСѓС‰РЅРѕСЃС‚РµР№ СЃРёСЃС‚РµРјС‹ Рё РёС… РѕС‚РѕР±СЂР°Р¶РµРЅРёРµ РІ СЂРµР»СЏС†РёРѕРЅРЅСѓСЋ СЃС‚СЂСѓРєС‚СѓСЂСѓ.

### 1.1 Users (РџРѕР»СЊР·РѕРІР°С‚РµР»Рё)
РўР°Р±Р»РёС†Р° `users`
* `id`: UUID (PK)
* `email`: VARCHAR(255) (Unique)
* `password_hash`: VARCHAR (bcrypt)
* `role`: ENUM ('Administrator', 'Director', 'Dispatcher', 'Guest')
* `settings`: JSONB (РќР°СЃС‚СЂРѕР№РєРё РёРЅС‚РµСЂС„РµР№СЃР°, С„РёР»СЊС‚СЂС‹ РїРѕ СѓРјРѕР»С‡Р°РЅРёСЋ, СЏР·С‹Рє)
* `trans_eu_credentials`: JSONB (Encrypted) - Р›РѕРіРёРЅ/РїР°СЂРѕР»СЊ РґР»СЏ РїР°СЂСЃРµСЂР°.

### 1.2 Vehicles (РўСЂР°РЅСЃРїРѕСЂС‚РЅС‹Рµ СЃСЂРµРґСЃС‚РІР°)
РўР°Р±Р»РёС†Р° `vehicles`
* `id`: UUID (PK)
* `reg_number`: VARCHAR(20)
* `type`: VARCHAR(50) (РўРµРЅС‚, Р СЌС„, Рё С‚.Рґ.)
* `dims_l`: DECIMAL (Р”Р»РёРЅР°, Рј)
* `dims_w`: DECIMAL (РЁРёСЂРёРЅР°, Рј)
* `dims_h`: DECIMAL (Р’С‹СЃРѕС‚Р°, Рј)
* `payload_kg`: INTEGER
* `gps_tracker_id`: VARCHAR (ID РІ СЃРёСЃС‚РµРјРµ GPS Guard).

### 1.3 VehiclePositions (РСЃС‚РѕСЂРёСЏ GPS)
РўР°Р±Р»РёС†Р° `vehicle_positions`
* `id`: BIGINT (PK)
* `vehicle_id`: UUID (FK -> vehicles.id)
* `latitude`: DECIMAL(10, 8)
* `longitude`: DECIMAL(11, 8)
* `place_name`: VARCHAR (Р РµР·СѓР»СЊС‚Р°С‚ РѕР±СЂР°С‚РЅРѕРіРѕ РіРµРѕРєРѕРґРёСЂРѕРІР°РЅРёСЏ: Р“РѕСЂРѕРґ)
* `country_code`: VARCHAR(2)
* `measured_at`: TIMESTAMP (Р’СЂРµРјСЏ РЅР° СѓСЃС‚СЂРѕР№СЃС‚РІРµ)
* `created_at`: TIMESTAMP (Р’СЂРµРјСЏ Р·Р°РїРёСЃРё РІ Р‘Р”)

### 1.4 OffersNormalized (РЎРїР°СЂСЃРµРЅРЅС‹Рµ РіСЂСѓР·С‹)
РўР°Р±Р»РёС†Р° `offers`
* `id`: UUID (PK)
* `external_id`: VARCHAR (ID СЃ Trans.eu)
* `vehicle_id`: UUID (Р”Р»СЏ РєР°РєРѕРіРѕ РўРЎ РёСЃРєР°Р»Рё)
* `loading_place`: VARCHAR
* `loading_lat`: DECIMAL
* `loading_lon`: DECIMAL
* `unloading_place`: VARCHAR
* `unloading_lat`: DECIMAL
* `unloading_lon`: DECIMAL
* `price`: DECIMAL (NULLable)
* `distance_osm`: INTEGER (Р Р°СЃСЃС‡РёС‚Р°РЅРЅРѕРµ СЂР°СЃСЃС‚РѕСЏРЅРёРµ РІ РєРј)
* `profitability_eur_km`: DECIMAL (Р Р°СЃСЃС‡РёС‚Р°РЅРЅР°СЏ СЃС‚Р°РІРєР°)
* `raw_data`: JSONB (РџРѕР»РЅС‹Р№ СЃР»РµРїРѕРє РґР°РЅРЅС‹С… СЃ РїР°СЂСЃРµСЂР°)
* `is_hidden`: BOOLEAN (Default: false)

### 1.5 FinancialPlans (РџР»Р°РЅРёСЂРѕРІР°РЅРёРµ)
РўР°Р±Р»РёС†Р° `financial_plans`
* `id`: UUID (PK)
* `vehicle_id`: UUID (FK)
* `month`: DATE (РќР°С‡Р°Р»Рѕ РјРµСЃСЏС†Р°)
* `target_revenue`: DECIMAL
* `target_margin`: DECIMAL
* `target_mileage`: INTEGER
* `fact_revenue`: DECIMAL (РћР±РЅРѕРІР»СЏРµС‚СЃСЏ С‚СЂРёРіРіРµСЂРѕРј РёР»Рё СЃРµСЂРІРёСЃРѕРј)
* `fact_mileage`: INTEGER (РђРіСЂРµРіР°С†РёСЏ РёР· GPS)

## 2. Р РµРїРѕР·РёС‚РѕСЂРёРё (Repositories Implementation)
Р РµР°Р»РёР·Р°С†РёСЏ РїР°С‚С‚РµСЂРЅР° Repository РґР»СЏ Р°Р±СЃС‚СЂР°РєС†РёРё РґРѕСЃС‚СѓРїР° Рє РґР°РЅРЅС‹Рј.

* **`PostgresVehicleRepository`**: Р РµР°Р»РёР·СѓРµС‚ `IVehicleRepository`. РњРµС‚РѕРґС‹: `save`, `findById`, `updateStatus`.
* **`PostgresOfferRepository`**: Р РµР°Р»РёР·СѓРµС‚ `IOfferRepository`. РњРµС‚РѕРґС‹: `saveBatch` (РґР»СЏ РјР°СЃСЃРѕРІРѕР№ РІСЃС‚Р°РІРєРё РїРѕСЃР»Рµ РїР°СЂСЃРёРЅРіР°), `findActiveByVehicle` (СЃ С„РёР»СЊС‚СЂР°С†РёРµР№ РїРѕ Blacklist).
* **`GPSLogRepository`**: РћРїС‚РёРјРёР·РёСЂРѕРІР°РЅ РґР»СЏ Р·Р°РїРёСЃРё time-series РґР°РЅРЅС‹С… (РёР»Рё РёСЃРїРѕР»СЊР·РѕРІР°РЅРёРµ TimescaleDB СЂР°СЃС€РёСЂРµРЅРёСЏ РїСЂРё РЅРµРѕР±С…РѕРґРёРјРѕСЃС‚Рё).

## 3. РњРёРіСЂР°С†РёРё
РЈРїСЂР°РІР»РµРЅРёРµ СЃС…РµРјРѕР№ Р±Р°Р·С‹ РґР°РЅРЅС‹С… РѕСЃСѓС‰РµСЃС‚РІР»СЏРµС‚СЃСЏ С‡РµСЂРµР· РјРёРіСЂР°С†РёРё.
* РџСѓС‚СЊ: `src/infrastructure/persistence/migrations`
* РљРѕРјР°РЅРґС‹: `run`, `revert`, `create`.
* Р’РµСЂСЃРёРѕРЅРёСЂРѕРІР°РЅРёРµ РѕР±СЏР·Р°С‚РµР»СЊРЅРѕ РїСЂРё РёР·РјРµРЅРµРЅРёРё СЃС‚СЂСѓРєС‚СѓСЂС‹ `users` РёР»Рё `offers`.

## 4. Р РµР·РµСЂРІРЅРѕРµ РєРѕРїРёСЂРѕРІР°РЅРёРµ
* **РўРёРї:** `pg_dump`
* **Р Р°СЃРїРёСЃР°РЅРёРµ:** Р•Р¶РµРґРЅРµРІРЅРѕ РІ 03:00 UTC.
* **РҐСЂР°РЅРµРЅРёРµ:** S3-СЃРѕРІРјРµСЃС‚РёРјРѕРµ С…СЂР°РЅРёР»РёС‰Рµ (С…СЂР°РЅРёС‚СЊ РїРѕСЃР»РµРґРЅРёРµ 30 РґРЅРµР№).
