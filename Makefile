# Makefile для упрощения команд разработки и деплоя MiniTMS

.PHONY: help dev dev-up dev-down prod prod-up prod-down vps-deploy logs clean test

help: ## Показать это сообщение помощи
	@echo "Доступные команды:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

# Development
dev: ## Запустить в режиме разработки (с hot-reload)
	docker-compose -f docker-compose.dev.yml up --build

dev-up: ## Запустить dev режим в фоне
	docker-compose -f docker-compose.dev.yml up -d --build

dev-down: ## Остановить dev контейнеры
	docker-compose -f docker-compose.dev.yml down

dev-logs: ## Показать логи dev контейнеров
	docker-compose -f docker-compose.dev.yml logs -f

# Production
prod: ## Запустить production версию
	docker-compose up --build

prod-up: ## Запустить production в фоне
	docker-compose up -d --build

prod-down: ## Остановить production контейнеры
	docker-compose down

prod-logs: ## Показать логи production
	docker-compose logs -f

# VPS Deployment
vps-deploy: ## Задеплоить на VPS (PostgreSQL/Redis уже установлены)
	docker-compose -f docker-compose.vps.yml up -d --build

vps-down: ## Остановить VPS контейнеры
	docker-compose -f docker-compose.vps.yml down

vps-logs: ## Показать логи VPS
	docker-compose -f docker-compose.vps.yml logs -f

vps-server-check-and-start: ## На VPS: проверить и при необходимости запустить backend+frontend (запускать на сервере)
	bash scripts/vps-server-check-and-start.sh

vps-test-remote: ## С вашей машины: проверить доступность приложения на 89.167.70.67
	powershell -ExecutionPolicy Bypass -File scripts/test-remote.ps1

# Database
db-migrate: ## Применить миграции БД
	docker-compose exec backend alembic upgrade head

db-rollback: ## Откатить последнюю миграцию
	docker-compose exec backend alembic downgrade -1

db-create-migration: ## Создать новую миграцию (использовать: make db-create-migration MSG="описание")
	docker-compose exec backend alembic revision --autogenerate -m "$(MSG)"

db-shell: ## Подключиться к PostgreSQL shell
	docker-compose exec postgres psql -U postgres -d mini-tms

db-backup: ## Создать бэкап БД
	docker-compose exec postgres pg_dump -U postgres mini-tms > backup_$$(date +%Y%m%d_%H%M%S).sql

# Logs
logs: ## Показать все логи
	docker-compose logs -f

logs-backend: ## Показать логи backend
	docker-compose logs -f backend

logs-frontend: ## Показать логи frontend
	docker-compose logs -f frontend

logs-postgres: ## Показать логи PostgreSQL
	docker-compose logs -f postgres

# Shell access
shell-backend: ## Войти в backend container shell
	docker-compose exec backend bash

shell-frontend: ## Войти в frontend container shell
	docker-compose exec frontend sh

shell-postgres: ## Войти в PostgreSQL container shell
	docker-compose exec postgres bash

# Testing
test-backend: ## Запустить backend тесты
	docker-compose exec backend pytest

test-frontend: ## Запустить frontend тесты
	cd frontend && npm run test

# Cleanup
clean: ## Остановить и удалить все контейнеры, volumes и образы
	docker-compose down -v --rmi all --remove-orphans
	docker-compose -f docker-compose.dev.yml down -v --rmi all --remove-orphans

clean-volumes: ## Удалить только volumes
	docker-compose down -v

restart: ## Перезапустить все сервисы
	docker-compose restart

restart-backend: ## Перезапустить только backend
	docker-compose restart backend

restart-frontend: ## Перезапустить только frontend
	docker-compose restart frontend

# Build
build: ## Пересобрать все образы
	docker-compose build

build-backend: ## Пересобрать только backend
	docker-compose build backend

build-frontend: ## Пересобрать только frontend
	docker-compose build frontend

# Status
ps: ## Показать статус контейнеров
	docker-compose ps

status: ps ## Алиас для ps

# Install dependencies
install-backend: ## Установить backend зависимости локально
	cd backend && pip install -r requirements.txt

install-frontend: ## Установить frontend зависимости локально
	cd frontend && npm install

# Linting & Formatting
lint-backend: ## Проверить backend код
	cd backend && black . && flake8 .

lint-frontend: ## Проверить frontend код
	cd frontend && npm run lint

# Documentation
docs: ## Открыть API документацию
	@echo "Opening API docs at http://localhost:8000/docs"
	@xdg-open http://localhost:8000/docs 2>/dev/null || open http://localhost:8000/docs 2>/dev/null || start http://localhost:8000/docs
