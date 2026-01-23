# Спецификация API (REST / Infrastructure Layer)

**Версия:** 1.0
**Статус:** Draft
**Базовый URL:** `/api/v1`

## 1. Общие принципы
Данный документ описывает REST API интерфейс, предоставляемый слоем инфраструктуры для Frontend-приложения и внешних интеграций.

* **Протокол:** HTTP/1.1 (HTTPS в продакшене).
* **Формат данных:** JSON (`application/json`).
* **Кодировка:** UTF-8.
* **Стандарты:** RESTful, соблюдение HTTP кодов ответов.
* **Даты:** ISO 8601 (`YYYY-MM-DDThh:mm:ssZ`).

## 2. Аутентификация и Авторизация
Используется JWT (JSON Web Token). Токен должен передаваться в заголовке `Authorization: Bearer <token>`.

### Эндпоинты
| Метод | URL | Описание | Доступ |
| :--- | :--- | :--- | :--- |
| `POST` | `/auth/login` | Вход в систему (email/pass). Возвращает `access_token` и `refresh_token`. | Public |
| `POST` | `/auth/refresh` | Обновление токена доступа. | Public |
| `POST` | `/auth/logout` | Инвалидация сессии. | Authorized |
| `GET` | `/auth/me` | Получение профиля текущего пользователя и прав доступа. | Authorized |

## 3. Модуль: Автопарк (Fleet Management)
Управление транспортными средствами (ТС) и их геопозицией.

| Метод | URL | Описание | Параметры / Body |
| :--- | :--- | :--- | :--- |
| `GET` | `/vehicles` | Список всех ТС с текущими координатами и статусами. | `?status=FREE,BUSY` |
| `POST` | `/vehicles` | Добавление нового ТС. | `{ reg_number, type, dimensions: {l,w,h}, payload }` |
| `GET` | `/vehicles/{id}` | Детальная информация о ТС. | - |
| `PUT` | `/vehicles/{id}` | Обновление данных ТС. | - |
| `PATCH` | `/vehicles/{id}/status` | Смена статуса (Свободен/В рейсе/На ТО). | `{ status: string }` |
| `POST` | `/vehicles/{id}/location/sync` | **Trigger:** Принудительное обновление GPS. Запрашивает API провайдера -> Сохраняет -> Геокодирует. | - |

## 4. Модуль: Грузы и Trans.eu (Cargo & Scraping)
Работа с предложениями грузов, полученными через парсинг.

| Метод | URL | Описание | Параметры / Body |
| :--- | :--- | :--- | :--- |
| `GET` | `/cargos` | Получение списка грузов с пагинацией и фильтрами. | `?vehicle_id=1&min_price=0.8&country_from=DE` |
| `POST` | `/cargos/search` | Запуск процесса парсинга (Scraping Task). | `{ vehicle_id: string, radius: number }` |
| `GET` | `/cargos/{id}/route` | Получение геометрии маршрута (OSM/OSRM Polyline) для карты. | - |
| `POST` | `/cargos/{id}/hide` | Скрыть груз (добавить в Blacklist). | `{ reason: string }` |
| `POST` | `/cargos/{id}/calculate` | Пересчитать рентабельность для конкретного ТС. | `{ vehicle_id: string }` |

**Специфика ответа `/cargos`:**
Каждый объект груза включает расчетные поля:
* `distance_empty`: Расстояние подачи (ТС -> Загрузка).
* `distance_full`: Расстояние перевозки (Загрузка -> Выгрузка).
* `rate_per_km`: Расчетная ставка €/км.
* `profitability_color`: Индикатор (red/gray/yellow/green).

## 5. Модуль: Финансы и Планирование (Planning)

| Метод | URL | Описание |
| :--- | :--- | :--- |
| `GET` | `/planning/dashboard` | Сводные данные план/факт (Выручка, Маржа, Пробег) за период. |
| `POST` | `/planning/targets` | Установка плановых показателей для ТС на месяц. |
| `GET` | `/planning/report` | Генерация отчета (PDF/Excel). |

## 6. Модуль: Интеграции (External Services)

| Метод | URL | Описание |
| :--- | :--- | :--- |
| `GET` | `/integrations/google/auth-url` | Получение ссылки для OAuth 2.0 авторизации Google (Sheets). |
| `POST` | `/integrations/google/callback` | Обработка callback от Google, сохранение токенов. |
| `POST` | `/orders/{id}/export-sheets` | Ручной триггер экспорта заказа в Google Sheets. |
| `POST` | `/email/send-offer` | Отправка коммерческого предложения. Проверяет лимиты (50/час). |

## 7. Обработка ошибок
API возвращает ошибки в стандартизированном формате `Problem Details` (RFC 7807).

```json
{
  "type": "about:blank",
  "title": "Rate Limit Exceeded",
  "status": 429,
  "detail": "Email limit reached. Try again in 12 minutes.",
  "instance": "/api/v1/email/send-offer"
}