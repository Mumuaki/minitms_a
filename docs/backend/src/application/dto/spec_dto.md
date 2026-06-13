> [!NOTE]
> **Внимание:** Базовые архитектурные решения (включая выбор БД, шины сообщений, GPS-провайдера и единиц измерения) зафиксированы в PROJECT-CONFIG.md. Любые расхождения в данной спецификации следует трактовать в пользу центрального конфига.

# Specification: Data Transfer Objects (DTO)

Р­С‚РѕС‚ РґРѕРєСѓРјРµРЅС‚ РѕРїРёСЃС‹РІР°РµС‚ СЃС‚СЂСѓРєС‚СѓСЂС‹ РґР°РЅРЅС‹С… (DTO), РёСЃРїРѕР»СЊР·СѓРµРјС‹Рµ РґР»СЏ РїРµСЂРµРґР°С‡Рё РёРЅС„РѕСЂРјР°С†РёРё РјРµР¶РґСѓ СЃР»РѕСЏРјРё РїСЂРёР»РѕР¶РµРЅРёСЏ. DTO РЅРµ СЃРѕРґРµСЂР¶Р°С‚ Р±РёР·РЅРµСЃ-Р»РѕРіРёРєРё.

## 1. Fleet & Vehicle DTOs
РСЃРїРѕР»СЊР·СѓСЋС‚СЃСЏ РІ РјРѕРґСѓР»Рµ СѓРїСЂР°РІР»РµРЅРёСЏ Р°РІС‚РѕРїР°СЂРєРѕРј.

### `VehicleDto`
РћСЃРЅРѕРІРЅРѕР№ РѕР±СЉРµРєС‚ РїРµСЂРµРґР°С‡Рё РґР°РЅРЅС‹С… Рѕ С‚СЂР°РЅСЃРїРѕСЂС‚РЅРѕРј СЃСЂРµРґСЃС‚РІРµ.
* **id**: UUID (String) вЂ” РЈРЅРёРєР°Р»СЊРЅС‹Р№ РёРґРµРЅС‚РёС„РёРєР°С‚РѕСЂ
* **plate_number**: String вЂ” Р“РѕСЃРЅРѕРјРµСЂ
* **type**: Enum (TENT, FRIDGE, VAN) вЂ” РўРёРї РєСѓР·РѕРІР°
* **dimensions**: `VehicleDimensionsDto` вЂ” Р“Р°Р±Р°СЂРёС‚С‹
* **max_weight**: Float вЂ” Р“СЂСѓР·РѕРїРѕРґСЉРµРјРЅРѕСЃС‚СЊ (РєРі)
* **status**: Enum (FREE, BUSY, MAINTENANCE, N/A) вЂ” РўРµРєСѓС‰РёР№ СЃС‚Р°С‚СѓСЃ
* **gps_device_id**: String? вЂ” ID РїСЂРёРІСЏР·Р°РЅРЅРѕРіРѕ С‚СЂРµРєРµСЂР°

### `VehicleDimensionsDto`
Р’Р»РѕР¶РµРЅРЅС‹Р№ РѕР±СЉРµРєС‚ РґР»СЏ СЂР°Р·РјРµСЂРѕРІ РєСѓР·РѕРІР°.
* **length**: Float вЂ” Р”Р»РёРЅР° (Рј)
* **width**: Float вЂ” РЁРёСЂРёРЅР° (Рј)
* **height**: Float вЂ” Р’С‹СЃРѕС‚Р° (Рј)

### `CreateVehicleRequest`
Р—Р°РїСЂРѕСЃ РЅР° СЃРѕР·РґР°РЅРёРµ РЅРѕРІРѕРіРѕ РўРЎ (UC-002).
* **plate_number**: String (Required)
* **type**: String (Required)
* **dimensions**: `VehicleDimensionsDto` (Required)
* **max_weight**: Float (Required)

## 2. Cargo & Scraping DTOs
РСЃРїРѕР»СЊР·СѓСЋС‚СЃСЏ РґР»СЏ СЂР°Р±РѕС‚С‹ СЃ РґР°РЅРЅС‹РјРё, РїРѕР»СѓС‡РµРЅРЅС‹РјРё РѕС‚ РїР°СЂСЃРµСЂР° Trans.eu.

### `CargoOfferDto`
РќРѕСЂРјР°Р»РёР·РѕРІР°РЅРЅРѕРµ РїСЂРµРґР»РѕР¶РµРЅРёРµ РіСЂСѓР·Р° СЃ Trans.eu.
* **external_id**: String вЂ” ID РїСЂРµРґР»РѕР¶РµРЅРёСЏ РЅР° Trans.eu
* **source**: String вЂ” РСЃС‚РѕС‡РЅРёРє (РїРѕ СѓРјРѕР»С‡Р°РЅРёСЋ "trans.eu")
* **loading_location**: `LocationDto` вЂ” РњРµСЃС‚Рѕ Р·Р°РіСЂСѓР·РєРё
* **unloading_location**: `LocationDto` вЂ” РњРµСЃС‚Рѕ РІС‹РіСЂСѓР·РєРё
* **loading_date**: Date (ISO8601) вЂ” Р”Р°С‚Р° Р·Р°РіСЂСѓР·РєРё
* **unloading_date**: Date (ISO8601) вЂ” Р”Р°С‚Р° РІС‹РіСЂСѓР·РєРё
* **weight**: Float вЂ” Р’РµСЃ РіСЂСѓР·Р° (РєРі) (РІ UI РјРѕР¶РµС‚ РєРѕРЅРІРµСЂС‚РёСЂРѕРІР°С‚СЊСЃСЏ РІ С‚РѕРЅРЅС‹)
* **price**: MoneyDto? вЂ” Р¦РµРЅР° (РµСЃР»Рё СѓРєР°Р·Р°РЅР°)
* **body_type**: String вЂ” РўСЂРµР±СѓРµРјС‹Р№ С‚РёРї РєСѓР·РѕРІР°
* **distance_route**: Float вЂ” Р Р°СЃСЃС‚РѕСЏРЅРёРµ РїРѕ РґР°РЅРЅС‹Рј Р±РёСЂР¶Рё (РєРј)
* **calculated_distance**: Float вЂ” Р Р°СЃСЃС‚РѕСЏРЅРёРµ С‡РµСЂРµР· OSM (Aв†’B + Bв†’C)
* **profitability**: `ProfitabilityDto` вЂ” Р Р°СЃСЃС‡РёС‚Р°РЅРЅС‹Рµ РїРѕРєР°Р·Р°С‚РµР»Рё

### `LocationDto`
Р“РµРѕРіСЂР°С„РёС‡РµСЃРєР°СЏ С‚РѕС‡РєР° (РґР»СЏ РёСЃРїРѕР»СЊР·РѕРІР°РЅРёСЏ СЃ GPS Рё РєР°СЂС‚Р°РјРё).
* **address**: String вЂ” РўРµРєСЃС‚РѕРІРѕРµ РїСЂРµРґСЃС‚Р°РІР»РµРЅРёРµ (Р“РѕСЂРѕРґ, РЎС‚СЂР°РЅР°, РРЅРґРµРєСЃ)
* **country_code**: String (ISO 2)
* **lat**: Float вЂ” РЁРёСЂРѕС‚Р°
* **lon**: Float вЂ” Р”РѕР»РіРѕС‚Р°

### `ProfitabilityDto`
Р РµР·СѓР»СЊС‚Р°С‚ СЂР°Р±РѕС‚С‹ СЃРµСЂРІРёСЃР° СЂР°СЃС‡РµС‚РѕРІ (Module 4).
* **rate_per_km**: Float вЂ” РЎС‚Р°РІРєР° в‚¬/РєРј
* **empty_run_km**: Float вЂ” РџРѕСЂРѕР¶РЅРёР№ РїСЂРѕР±РµРі РѕС‚ С‚РµРєСѓС‰РµР№ РїРѕР·РёС†РёРё
* **total_distance**: Float вЂ” РџРѕР»РЅС‹Р№ РїСЂРѕР±РµРі
* **color_code**: Enum (RED, GRAY, YELLOW, GREEN) вЂ” РРЅРґРёРєР°С‚РѕСЂ СЂРµРЅС‚Р°Р±РµР»СЊРЅРѕСЃС‚Рё

## 3. Planning & Finance DTOs
РСЃРїРѕР»СЊР·СѓСЋС‚СЃСЏ РІ РјРѕРґСѓР»Рµ С„РёРЅР°РЅСЃРѕРІРѕРіРѕ РїР»Р°РЅРёСЂРѕРІР°РЅРёСЏ (Module 12).

### `PlanDto`
РџР»Р°РЅРѕРІС‹Рµ РїРѕРєР°Р·Р°С‚РµР»Рё РЅР° РјРµСЃСЏС†.
* **vehicle_id**: UUID
* **month**: String (YYYY-MM)
* **target_revenue**: Float вЂ” РџР»Р°РЅРѕРІР°СЏ РІС‹СЂСѓС‡РєР° (в‚¬)
* **target_margin**: Float вЂ” РџР»Р°РЅРѕРІР°СЏ РјР°СЂР¶Р° (в‚¬)
* **target_mileage**: Float вЂ” РџР»Р°РЅРѕРІС‹Р№ РїСЂРѕР±РµРі (РєРј)

### `PlanFactReportDto`
РћС‚С‡РµС‚ РїР»Р°РЅ/С„Р°РєС‚ РґР»СЏ Dashboard (UC-008).
* **revenue**: `MetricComparisonDto`
* **margin**: `MetricComparisonDto`
* **mileage**: `MetricComparisonDto`
* **average_rate_fact**: Float вЂ” Р¤Р°РєС‚РёС‡РµСЃРєР°СЏ СЃСЂРµРґРЅСЏСЏ СЃС‚Р°РІРєР° (в‚¬/РєРј)

### `MetricComparisonDto`
* **planned**: Float
* **actual**: Float
* **percentage**: Float вЂ” % РІС‹РїРѕР»РЅРµРЅРёСЏ

## 4. Google Sheets Integration DTOs
Р”Р»СЏ СЃРёРЅС…СЂРѕРЅРёР·Р°С†РёРё СЃ С‚Р°Р±Р»РёС†Р°РјРё "Р—Р°РєР°Р·С‹" (24 СЃС‚РѕР»Р±С†Р°).

### `OrderSheetRowDto`
РћС‚СЂР°Р¶Р°РµС‚ СЃС‚СЂСѓРєС‚СѓСЂСѓ СЃС‚СЂРѕРєРё РІ Google Sheets.
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

