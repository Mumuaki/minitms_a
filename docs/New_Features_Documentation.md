# Документация по новым возможностям системы MiniTMS

## Содержание
1. [Расширенный поиск грузов](#расширенный-поиск-грузов)
2. [Расчет рентабельности](#расчет-рентабельности)
3. [Фильтрация по транспортным средствам](#фильтрация-по-транспортным-средствам)
4. [Планирование маршрутов](#планирование-маршрутов)
5. [Архитектурные решения](#архитектурные-решения)
6. [Рекомендации по интеграции](#рекомендации-по-интеграции)
7. [Примеры использования](#примеры-использования)

## Расширенный поиск грузов

### Описание
Эндпоинт `/cargos/search` позволяет выполнять расширенный поиск грузов с фильтрацией по различным параметрам, включая даты, вес, цену, расстояние, тип кузова и другие характеристики.

### API Endpoint
```
GET /api/v1/cargos/search
```

### Параметры запроса

#### Фильтры
- `loading_date_from`: Начальная дата загрузки (YYYY-MM-DD)
- `loading_date_to`: Конечная дата загрузки (YYYY-MM-DD)
- `unloading_date_from`: Начальная дата выгрузки (YYYY-MM-DD)
- `unloading_date_to`: Конечная дата выгрузки (YYYY-MM-DD)
- `weight_min`: Минимальный вес (т)
- `weight_max`: Максимальный вес (т)
- `body_type`: Тип кузова
- `price_min`: Минимальная цена (€)
- `price_max`: Максимальная цена (€)
- `distance_min`: Минимальное расстояние (км)
- `distance_max`: Максимальное расстояние (км)
- `distance_type`: Тип расстояния: `trans_eu` или `osm` (по умолчанию `trans_eu`)
- `status_colors`: Статусы цвета рентабельности (RED, GRAY, YELLOW, GREEN)
- `source`: Источник данных
- `is_hidden`: Показывать скрытые грузы (true/false)

#### Параметры расчета рентабельности
- `fuel_consumption`: Расход топлива (л/100км)
- `fuel_price`: Стоимость топлива (€/л)
- `depreciation_per_km`: Амортизация (€/км)
- `driver_salary_per_km`: Зарплата водителя (€/км)
- `other_costs_per_km`: Прочие расходы (€/км)
- `empty_run_distance`: Расстояние порожнего пробега (км)

#### Параметры сортировки
- `order_by`: Поле сортировки (по умолчанию `created_at`)
- `order_direction`: Направление сортировки: `asc` или `desc` (по умолчанию `desc`)

#### Пагинация
- `page`: Номер страницы (по умолчанию 1)
- `limit`: Количество элементов на странице (по умолчанию 20, максимум 100)

#### Параметры фильтрации по транспортному средству
- `vehicle_body_type`: Тип кузова транспортного средства
- `vehicle_max_weight`: Максимальный вес груза для ТС (т)
- `vehicle_capacity`: Вместимость ТС (м³)
- `vehicle_length`: Длина ТС (м)
- `vehicle_width`: Ширина ТС (м)
- `vehicle_height`: Высота ТС (м)

### Пример запроса
```
GET /api/v1/cargos/search?weight_min=5&price_min=1000&body_type=Refrigerator&fuel_consumption=30&fuel_price=1.5&page=1&limit=10
```

### Ответ
```json
{
  "items": [
    {
      "id": "cargo-id-1",
      "external_id": "ext-12345",
      "source": "trans-eu",
      "loading_place": {
        "address": "Berlin, Germany",
        "country_code": "DE",
        "lat": 52.52,
        "lon": 13.405
      },
      "unloading_place": {
        "address": "Paris, France",
        "country_code": "FR",
        "lat": 48.8566,
        "lon": 2.3522
      },
      "loading_date": "2024-01-15",
      "unloading_date": "2024-01-17",
      "weight": 12.5,
      "body_type": "Refrigerator",
      "price": 2450.0,
      "distance_trans_eu": 1050,
      "distance_osm": 1075,
      "profitability": {
        "rate_per_km": 0.85,
        "total_cost": 450.5,
        "empty_run_km": 50,
        "total_distance": 1125,
        "status_color": "GREEN"
      },
      "is_hidden": false,
      "created_at": "2024-01-10T10:30:00"
    }
  ],
  "total": 150,
  "page": 1,
  "limit": 10,
  "total_pages": 15
}
```

## Расчет рентабельности

### Описание
Система MiniTMS включает в себя продвинутый механизм расчета рентабельности перевозок, который учитывает различные факторы затрат и доходов.

### Формула расчета
Рентабельность рассчитывается по следующей формуле:
```
rate_per_km = (cargo_price - total_cost) / total_distance
```

Где:
- `cargo_price` - цена груза (€)
- `total_cost` - общие затраты на перевозку (€)
- `total_distance` - общее расстояние (груженый + порожний пробег) (км)

### Компоненты затрат
Общие затраты состоят из:
- Затраты на топливо: `(fuel_consumption / 100) * total_distance * fuel_price`
- Амортизация: `depreciation_per_km * total_distance`
- Зарплата водителя: `driver_salary_per_km * total_distance`
- Прочие расходы: `other_costs_per_km * total_distance`

### Цветовая кодировка статусов
- GREEN: ≥ 0.80 €/км
- YELLOW: 0.60 - 0.79 €/км
- GRAY: 0.54 - 0.59 €/км
- RED: < 0.54 €/км

### Значения по умолчанию
Если какие-либо параметры затрат не указаны, они принимаются как 0:
- fuel_consumption: None
- fuel_price: None
- depreciation_per_km: None
- driver_salary_per_km: None
- other_costs_per_km: None

## Фильтрация по транспортным средствам

### Описание
Эндпоинт `/cargos/filter-by-vehicle` позволяет фильтровать грузы на основе характеристик транспортного средства, таких как тип кузова, грузоподъемность, габариты и другие параметры.

### API Endpoint
```
GET /api/v1/cargos/filter-by-vehicle
```

### Параметры запроса
Все параметры такие же, как в обычном поиске, но с акцентом на параметры транспортного средства:
- `vehicle_body_type`: Тип кузова транспортного средства
- `vehicle_max_weight`: Максимальный вес груза для ТС (т)
- `vehicle_capacity`: Вместимость ТС (м³)
- `vehicle_length`: Длина ТС (м)
- `vehicle_width`: Ширина ТС (м)
- `vehicle_height`: Высота ТС (м)

А также параметры расчета рентабельности:
- `fuel_consumption`, `fuel_price`, `depreciation_per_km`, `driver_salary_per_km`, `other_costs_per_km`, `empty_run_distance`

### Пример запроса
```
GET /api/v1/cargos/filter-by-vehicle?vehicle_body_type=Box&vehicle_max_weight=20&fuel_consumption=25&fuel_price=1.4&page=1&limit=5
```

## Планирование маршрутов

### Описание
Система планирования маршрутов позволяет автоматически назначать грузы транспортным средствам и оптимизировать маршруты для максимальной прибыли.

### API Endpoints

#### Планирование маршрутов
```
POST /api/v1/route-planning/
```

#### Оптимизация маршрутов
```
POST /api/v1/route-planning/optimize
```

### Запрос на планирование (RoutePlanningRequest)

#### Поля
- `cargo_ids`: Список ID грузов для планирования
- `vehicle_ids`: Список ID доступных транспортных средств
- `planning_date`: Дата планирования
- `max_routes_per_vehicle`: Максимальное количество маршрутов на ТС (по умолчанию 1)
- `max_cargos_per_route`: Максимальное количество грузов на маршрут (по умолчанию 3)

### Ответ на планирование (RoutePlanningResponse)

#### Поля
- `planned_routes`: Список запланированных маршрутов
- `unassigned_cargos`: Список ID грузов, которые не удалось назначить
- `total_profit`: Общая прибыль от всех маршрутов
- `message`: Сообщение о результате

### Структура PlannedRouteDTO

#### Поля
- `vehicle_id`: ID транспортного средства
- `route`: Маршрут (объект с точками, расстоянием и временем)
- `assigned_cargos`: Назначенные грузы (список ID)
- `total_profit`: Общая прибыль от маршрута
- `start_time`: Время начала маршрута
- `end_time`: Время окончания маршрута

### Пример запроса на планирование
```json
{
  "cargo_ids": ["cargo-1", "cargo-2", "cargo-3"],
  "vehicle_ids": ["vehicle-1", "vehicle-2"],
  "planning_date": "2024-01-15T09:00:00",
  "max_routes_per_vehicle": 1,
  "max_cargos_per_route": 3
}
```

### Пример ответа
```json
{
  "planned_routes": [
    {
      "vehicle_id": "vehicle-1",
      "route": {
        "points": [
          {
            "coordinates": {
              "latitude": 52.52,
              "longitude": 13.405
            },
            "address": "Berlin, Germany",
            "operation": "loading",
            "planned_time": "2024-01-15T09:00:00"
          },
          {
            "coordinates": {
              "latitude": 48.8566,
              "longitude": 2.3522
            },
            "address": "Paris, France",
            "operation": "unloading",
            "planned_time": "2024-01-15T15:00:00"
          }
        ],
        "total_distance": 1075,
        "estimated_duration": "PT6H30M",
        "empty_run_distance": 50
      },
      "assigned_cargos": ["cargo-1"],
      "total_profit": 1850.5,
      "start_time": "2024-01-15T08:00:00",
      "end_time": "2024-01-15T16:30:00"
    }
  ],
  "unassigned_cargos": ["cargo-2", "cargo-3"],
  "total_profit": 1850.5,
  "message": "Запланировано 1 маршрутов. Назначено 1 грузов. Не назначено 2 грузов. Ожидаемая прибыль: €1850.50"
}
```

### Алгоритм планирования
1. Сопоставление грузов с транспортными средствами по совместимости (вес, тип кузова)
2. Сортировка грузов по рентабельности (от большего к меньшему)
3. Назначение наиболее рентабельных грузов доступным транспортным средствам
4. Оптимизация маршрутов с использованием алгоритма оптимизации
5. Расчет общей прибыли для каждого маршрута

## Архитектурные решения

### Общая архитектура
Система MiniTMS построена по принципам Clean Architecture с разделением на три основных слоя:

#### Domain Layer
- Сущности (Entities): Cargo, Vehicle, User, Order
- Value Objects: Profitability, Coordinates, Route, Dimensions
- Domain Services: ProfitabilityCalculator, RoutePlanner, RouteOptimizer
- Repository Protocols: Интерфейсы репозиториев

#### Application Layer
- Use Cases: SearchCargosUseCase, PlanRoutesUseCase, FilterByVehicleUseCase
- DTOs: Data Transfer Objects для передачи данных между слоями
- Ports: Интерфейсы для взаимодействия с внешними системами

#### Infrastructure Layer
- API: FastAPI эндпоинты и схемы
- Persistence: SQLAlchemy модели и репозитории
- External Services: Google Maps, Trans.eu, SMTP, Telegram

### Паттерны проектирования
- Use Case Pattern: Бизнес-логика изолирована в use cases
- Repository Pattern: Абстракция доступа к данным
- Dependency Injection: Через FastAPI зависимости
- Value Objects: Для представления бизнес-значений с логикой
- Strategy Pattern: Для различных стратегий расчета и оптимизации

### Масштабируемость
- Модульная архитектура позволяет легко добавлять новые функции
- Четкое разделение ответственности между слоями
- Возможность замены реализаций без изменения интерфейсов

## Рекомендации по интеграции

### Установка и настройка
1. Клонируйте репозиторий
2. Установите зависимости: `pip install -r requirements.txt`
3. Настройте переменные окружения в `.env` файле
4. Запустите миграции базы данных
5. Запустите сервер: `uvicorn main:app --reload`

### Пример клиентского кода (Python)

#### Поиск грузов
```python
import requests

def search_cargos():
    url = "http://localhost:8000/api/v1/cargos/search"
    params = {
        "weight_min": 5,
        "price_min": 1000,
        "body_type": "Box",
        "fuel_consumption": 25,
        "fuel_price": 1.4,
        "page": 1,
        "limit": 10
    }
    
    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = response.json()
        print(f"Найдено {data['total']} грузов")
        for cargo in data['items']:
            print(f"ID: {cargo['id']}, Цена: {cargo['price']}, Рентабельность: {cargo['profitability']['status_color']}")
    else:
        print(f"Ошибка: {response.status_code}")

search_cargos()
```

#### Планирование маршрутов
```python
import requests

def plan_routes():
    url = "http://localhost:8000/api/v1/route-planning/"
    payload = {
        "cargo_ids": ["cargo-1", "cargo-2"],
        "vehicle_ids": ["vehicle-1"],
        "planning_date": "2024-01-15T09:00:00"
    }
    
    response = requests.post(url, json=payload)
    if response.status_code == 200:
        data = response.json()
        print(data['message'])
        for route in data['planned_routes']:
            print(f"ТС {route['vehicle_id']}: {len(route['assigned_cargos'])} грузов, прибыль €{route['total_profit']}")
    else:
        print(f"Ошибка: {response.status_code}")

plan_routes()
```

### Обработка ошибок
- 400 Bad Request: Неверные параметры запроса
- 422 Unprocessable Entity: Неверный формат данных
- 500 Internal Server Error: Внутренняя ошибка сервера

### Лучшие практики
1. Всегда указывайте параметры пагинации для больших наборов данных
2. Используйте параметры фильтрации для уменьшения объема данных
3. Рассчитывайте рентабельность с реалистичными значениями затрат
4. Используйте HTTPS в production окружении
5. Реализуйте повторные попытки при временных ошибках

## Примеры использования

### Сценарий 1: Поиск прибыльных грузов для конкретного ТС

#### Задача
Найти прибыльные грузы, подходящие для транспортного средства с холодильником, грузоподъемностью 20 тонн.

#### Решение
```bash
GET /api/v1/cargos/filter-by-vehicle?vehicle_body_type=Refrigerator&vehicle_max_weight=20&status_colors=GREEN,YELLOW&fuel_consumption=28&fuel_price=1.45&page=1&limit=20
```

#### Объяснение
- `vehicle_body_type=Refrigerator`: Только грузы, подходящие для холодильника
- `vehicle_max_weight=20`: Только грузы, которые может перевезти ТС
- `status_colors=GREEN,YELLOW`: Только прибыльные грузы (GREEN: ≥0.80 €/км, YELLOW: 0.60-0.79 €/км)
- `fuel_consumption=28`: Расход топлива для расчета рентабельности
- `fuel_price=1.45`: Стоимость топлива для расчета рентабельности

### Сценарий 2: Планирование маршрутов на неделю вперед

#### Задача
Спланировать маршруты для парка из 5 транспортных средств на предстоящую неделю, максимально увеличив общую прибыль.

#### Решение
1. Сначала получить список доступных грузов на следующую неделю:
```bash
GET /api/v1/cargos/search?loading_date_from=2024-01-15&loading_date_to=2024-01-21&status_colors=GREEN,YELLOW,GRAY&price_min=500&page=1&limit=100
```

2. Затем использовать полученные ID грузов для планирования маршрутов:
```json
{
  "cargo_ids": ["cargo-1", "cargo-2", "..."],
  "vehicle_ids": ["truck-1", "truck-2", "truck-3", "truck-4", "truck-5"],
  "planning_date": "2024-01-15T00:00:00"
}
```

#### Объяснение
- Алгоритм планирования автоматически сопоставит грузы с подходящими ТС
- Рассчитает оптимальные маршруты для максимальной прибыли
- Учтет совместимость грузов с ТС по весу и типу кузова

### Сценарий 3: Мониторинг рентабельности перевозок

#### Задача
Анализировать рентабельность перевозок с учетом текущих рыночных условий (цены на топливо, затраты на эксплуатацию).

#### Решение
```bash
GET /api/v1/cargos/search?loading_date_from=2024-01-01&loading_date_to=2024-01-31&fuel_consumption=30&fuel_price=1.6&depreciation_per_km=0.8&driver_salary_per_km=0.5&other_costs_per_km=0.3&page=1&limit=50
```

#### Объяснение
- `fuel_price=1.6`: Актуальная стоимость топлива
- `depreciation_per_km=0.8`: Затраты на амортизацию на км
- `driver_salary_per_km=0.5`: Затраты на зарплату водителя на км
- `other_costs_per_km=0.3`: Другие операционные расходы на км
- Система пересчитает рентабельность с этими параметрами и вернет актуальный статус

### Полезные рецепты

#### 1. Поиск грузов с минимальной маржой прибыли
Чтобы найти грузы с минимальной прибылью, можно использовать фильтрацию по цветовому статусу:
```bash
GET /api/v1/cargos/search?status_colors=RED,GRAY&price_min=500&distance_max=1500
```

#### 2. Оптимизация использования парка
Для проверки, какие ТС простаивают, можно использовать планирование маршрутов с фильтрацией по типу кузова:
```bash
GET /api/v1/cargos/filter-by-vehicle?vehicle_body_type=Box&vehicle_max_weight=24&loading_date_from=2024-01-15&loading_date_to=2024-01-22
```

#### 3. Сравнение рентабельности разных маршрутов
Для сравнения разных сценариев можно выполнить несколько запросов с разными параметрами затрат:
```bash
# Сценарий 1: Высокие затраты
GET /api/v1/cargos/search?fuel_price=1.8&depreciation_per_km=1.0&price_min=1000

# Сценарий 2: Низкие затраты
GET /api/v1/cargos/search?fuel_price=1.2&depreciation_per_km=0.5&price_min=1000
```

#### 4. Экспорт данных для анализа
Для дальнейшего анализа можно экспортировать данные в Excel или CSV:
```bash
GET /api/v1/cargos/search?loading_date_from=2024-01-01&loading_date_to=2024-01-31&limit=1000
```
Затем использовать полученные JSON данные для импорта в аналитические инструменты.