# Frontend Infrastructure Specification

## 1. Обзор
Данный документ описывает инфраструктурные решения, процессы сборки, развертывания и обеспечения качества кода для Frontend-приложения MiniTMS.

## 2. Технологический стек
Согласно техническим рекомендациям, приложение разрабатывается как SPA (Single Page Application).

* **Фреймворк:** React (с использованием TypeScript для строгой типизации).
* **Сборщик:** Vite (для обеспечения быстрой сборки и HMR).
* **Стилизация:** TailwindCSS (для быстрой верстки и адаптивности) + UI Kit (Ant Design или Material UI).
* **State Management:** Redux Toolkit или Zustand (глобальное состояние приложения).
* **Маршрутизация:** React Router v6.
* **HTTP Клиент:** Axios (с настройкой интерцепторов для JWT).
* **Карты:** react-leaflet (Интеграция с OpenStreetMap / Leaflet).

## 3. Архитектура приложения
Используется **Feature-Sliced Design (FSD)** (адаптированный) для обеспечения масштабируемости, что отражено в структуре папок `src/features`, `src/shared`, `src/entities`.

### 3.1 Структура Docker
Для контейнеризации используется многоэтапная сборка (Multi-stage build).

**Dockerfile Stages:**
1.  **Build Stage:** Node.js образ. Установка зависимостей (`npm ci`), сборка проекта (`npm run build`).
2.  **Production Stage:** Nginx (Alpine). Копирование собранных статических файлов из `build stage` в папку `/usr/share/nginx/html`.
3.  **Config:** Кастомный `nginx.conf` для обработки SPA-роутинга (try_files $uri /index.html) и Gzip-сжатия.

## 4. CI/CD Pipeline
Процесс непрерывной интеграции и доставки настроен для автоматизации проверок и деплоя.

* **Trigger:** Push в ветки `develop` (dev env) или `main` (prod env).
* **Steps:**
    1.  **Linting:** Проверка кода через ESLint и Prettier.
    2.  **Unit Tests:** Запуск тестов (Vitest/Jest). Критерий покрытия кода > 80%.
    3.  **Build:** Тестовая сборка для проверки отсутствия ошибок компиляции.
    4.  **Docker Build & Push:** Создание образа и отправка в Registry.
    5.  **Deploy:** Обновление контейнеров на целевом сервере (SSH/Kubernetes).

## 5. Окружение и Конфигурация
Конфигурация управляется через переменные окружения (`.env`).

| Переменная | Описание |
| :--- | :--- |
| `VITE_API_BASE_URL` | Базовый URL бэкенда. |
| `VITE_OSM_TILE_SERVER` | URL тайл-сервера (например, OpenStreetMap или собственный OSRM). |
| `VITE_TRANS_EU_CLIENT_ID` | ID приложения для интеграции (если применимо). |

## 6. Требования к производительности и совместимости
* **Browser Support:** Chrome, Firefox, Edge, Safari (последние 2 версии).
* **Load Time:** Время первой отрисовки (FCP) < 1.5 сек.
* **Optimization:** Использование Code Splitting (lazy loading) для разделения бандлов по роутам.