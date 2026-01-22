import os

# Список директорий
dirs = [
    # backend
    "backend/src/domain/entities",
    "backend/src/domain/value_objects",
    "backend/src/domain/repositories",
    "backend/src/domain/services",
    "backend/src/domain/events",
    "backend/src/application/use_cases/auth",
    "backend/src/application/use_cases/fleet",
    "backend/src/application/use_cases/cargo",
    "backend/src/application/use_cases/orders",
    "backend/src/application/use_cases/planning",
    "backend/src/application/use_cases/notifications",
    "backend/src/application/dto",
    "backend/src/application/ports",
    "backend/src/infrastructure/persistence/sqlalchemy/models",
    "backend/src/infrastructure/persistence/sqlalchemy/repositories",
    "backend/src/infrastructure/persistence/sqlalchemy",
    "backend/src/infrastructure/persistence/migrations",
    "backend/src/infrastructure/external_services/trans_eu",
    "backend/src/infrastructure/external_services/google_maps",
    "backend/src/infrastructure/external_services/google_sheets",
    "backend/src/infrastructure/external_services/gps",
    "backend/src/infrastructure/external_services/telegram",
    "backend/src/infrastructure/external_services/smtp",
    "backend/src/infrastructure/api/v1/endpoints",
    "backend/src/infrastructure/api/v1/schemas",
    "backend/src/infrastructure/security",
    "backend/src/infrastructure/config",
    "backend/src/infrastructure/messaging",
    "backend/tests/unit/domain",
    "backend/tests/unit/application",
    "backend/tests/unit/infrastructure",
    "backend/tests/integration",
    "backend/tests/e2e",

    # frontend
    "frontend/src/core/config",
    "frontend/src/core/router",
    "frontend/src/core/store",
    "frontend/src/features/auth/components",
    "frontend/src/features/auth/hooks",
    "frontend/src/features/auth/services",
    "frontend/src/features/auth/types",
    "frontend/src/features/dashboard",
    "frontend/src/features/loads",
    "frontend/src/features/fleet",
    "frontend/src/features/finance",
    "frontend/src/features/reports",
    "frontend/src/features/settings",
    "frontend/src/shared/components/ui",
    "frontend/src/shared/components/layout",
    "frontend/src/shared/components/map",
    "frontend/src/shared/components/charts",
    "frontend/src/shared/hooks",
    "frontend/src/shared/utils",
    "frontend/src/shared/types",
    "frontend/src/infrastructure/api/endpoints",
    "frontend/src/infrastructure/i18n/locales",
    "frontend/src/infrastructure/theme",
    "frontend/tests/unit",
    "frontend/tests/integration",
    "frontend/tests/e2e",
    "frontend/public",

    # docs
    "docs/01_introduction",
    "docs/02_functional_requirements/modules",
    "docs/03_non_functional_requirements",
    "docs/04_architecture/diagrams",
    "docs/05_ui_design",
    "docs/06_data_model",
    "docs/07_integrations",
    "docs/08_security",
    "docs/09_testing",
    "docs/10_deployment",
    "docs/11_maintenance",

    # infrastructure
    "infrastructure/docker",
    "infrastructure/kubernetes/deployments",
    "infrastructure/kubernetes/services",
    "infrastructure/kubernetes/ingress",
    "infrastructure/terraform",
    "infrastructure/scripts",

    # tools & archive
    "tools/.agent",
    "tools/.gemini",
    "tools/.specify",
    "tools/chrome_profile",
    "tools/mcp-db-server",
    "archive/backup",
    "archive/backup1712",
    "archive/backend_backup_20251209",

    # .github
    ".github/workflows",

    # .vscode
    ".vscode",
]

# Список файлов
files = [
    # backend domain entities
    "backend/src/domain/entities/user.py",
    "backend/src/domain/entities/vehicle.py",
    "backend/src/domain/entities/cargo.py",
    "backend/src/domain/entities/order.py",
    "backend/src/domain/entities/plan.py",
    "backend/src/domain/entities/email_history.py",
    "backend/src/domain/entities/gps_data.py",

    # value_objects
    "backend/src/domain/value_objects/coordinates.py",
    "backend/src/domain/value_objects/route.py",
    "backend/src/domain/value_objects/profitability.py",
    "backend/src/domain/value_objects/dimensions.py",

    # repositories interfaces
    "backend/src/domain/repositories/user_repository.py",
    "backend/src/domain/repositories/vehicle_repository.py",
    "backend/src/domain/repositories/cargo_repository.py",
    "backend/src/domain/repositories/order_repository.py",
    "backend/src/domain/repositories/plan_repository.py",

    # domain services
    "backend/src/domain/services/profitability_calculator.py",
    "backend/src/domain/services/route_optimizer.py",
    "backend/src/domain/services/plan_validator.py",

    # domain events
    "backend/src/domain/events/cargo_found.py",
    "backend/src/domain/events/order_created.py",
    "backend/src/domain/events/plan_exceeded.py",

    # application use_cases/auth
    "backend/src/application/use_cases/auth/login_user.py",
    "backend/src/application/use_cases/auth/register_user.py",
    "backend/src/application/use_cases/auth/refresh_token.py",

    # application use_cases/fleet
    "backend/src/application/use_cases/fleet/add_vehicle.py",
    "backend/src/application/use_cases/fleet/update_vehicle_status.py",
    "backend/src/application/use_cases/fleet/get_vehicle_location.py",

    # application use_cases/cargo
    "backend/src/application/use_cases/cargo/search_cargos.py",
    "backend/src/application/use_cases/cargo/calculate_profitability.py",
    "backend/src/application/use_cases/cargo/filter_by_vehicle.py",

    # application use_cases/orders
    "backend/src/application/use_cases/orders/create_order.py",
    "backend/src/application/use_cases/orders/sync_to_google_sheets.py",
    "backend/src/application/use_cases/orders/send_commercial_offer.py",

    # application use_cases/planning
    "backend/src/application/use_cases/planning/set_monthly_plan.py",
    "backend/src/application/use_cases/planning/track_plan_execution.py",
    "backend/src/application/use_cases/planning/calculate_average_rate.py",

    # application use_cases/notifications
    "backend/src/application/use_cases/notifications/send_push_notification.py",
    "backend/src/application/use_cases/notifications/send_telegram_alert.py",

    # application dto
    "backend/src/application/dto/auth_dto.py",
    "backend/src/application/dto/vehicle_dto.py",
    "backend/src/application/dto/cargo_dto.py",
    "backend/src/application/dto/order_dto.py",

    # application ports
    "backend/src/application/ports/scraping_port.py",
    "backend/src/application/ports/maps_port.py",
    "backend/src/application/ports/sheets_port.py",
    "backend/src/application/ports/gps_port.py",
    "backend/src/application/ports/email_port.py",
    "backend/src/application/ports/notification_port.py",

    # infrastructure persistence sqlalchemy models
    "backend/src/infrastructure/persistence/sqlalchemy/models/user_model.py",
    "backend/src/infrastructure/persistence/sqlalchemy/models/vehicle_model.py",
    "backend/src/infrastructure/persistence/sqlalchemy/models/cargo_model.py",
    "backend/src/infrastructure/persistence/sqlalchemy/models/order_model.py",
    "backend/src/infrastructure/persistence/sqlalchemy/models/plan_model.py",

    # infrastructure persistence sqlalchemy repositories impl
    "backend/src/infrastructure/persistence/sqlalchemy/repositories/user_repository_impl.py",
    "backend/src/infrastructure/persistence/sqlalchemy/repositories/vehicle_repository_impl.py",
    "backend/src/infrastructure/persistence/sqlalchemy/repositories/cargo_repository_impl.py",

    # database
    "backend/src/infrastructure/persistence/sqlalchemy/database.py",

    # infrastructure external_services
    "backend/src/infrastructure/external_services/trans_eu/client.py",
    "backend/src/infrastructure/external_services/trans_eu/parser.py",
    "backend/src/infrastructure/external_services/trans_eu/mapper.py",
    "backend/src/infrastructure/external_services/google_maps/client.py",
    "backend/src/infrastructure/external_services/google_maps/distance_calculator.py",
    "backend/src/infrastructure/external_services/google_sheets/client.py",
    "backend/src/infrastructure/external_services/google_sheets/oauth_handler.py",
    "backend/src/infrastructure/external_services/google_sheets/sync_service.py",
    "backend/src/infrastructure/external_services/gps/wialon_adapter.py",
    "backend/src/infrastructure/external_services/gps/navixy_adapter.py",
    "backend/src/infrastructure/external_services/gps/gps_trace_adapter.py",
    "backend/src/infrastructure/external_services/telegram/bot_client.py",
    "backend/src/infrastructure/external_services/smtp/email_client.py",
    "backend/src/infrastructure/external_services/smtp/template_engine.py",

    # infrastructure api
    "backend/src/infrastructure/api/v1/endpoints/auth.py",
    "backend/src/infrastructure/api/v1/endpoints/fleet.py",
    "backend/src/infrastructure/api/v1/endpoints/cargos.py",
    "backend/src/infrastructure/api/v1/endpoints/orders.py",
    "backend/src/infrastructure/api/v1/endpoints/planning.py",
    "backend/src/infrastructure/api/v1/endpoints/reports.py",
    "backend/src/infrastructure/api/v1/endpoints/settings.py",
    "backend/src/infrastructure/api/v1/dependencies.py",
    "backend/src/infrastructure/api/v1/middleware.py",
    "backend/src/infrastructure/api/v1/schemas/auth_schema.py",
    "backend/src/infrastructure/api/v1/schemas/vehicle_schema.py",
    "backend/src/infrastructure/api/v1/schemas/cargo_schema.py",

    # infrastructure security
    "backend/src/infrastructure/security/jwt_handler.py",
    "backend/src/infrastructure/security/password_hasher.py",
    "backend/src/infrastructure/security/rbac.py",

    # infrastructure config
    "backend/src/infrastructure/config/settings.py",
    "backend/src/infrastructure/config/logging.py",

    # infrastructure messaging
    "backend/src/infrastructure/messaging/event_bus.py",
    "backend/src/infrastructure/messaging/task_queue.py",

    # backend root files
    "backend/main.py",
    "backend/requirements.txt",
    "backend/Dockerfile",
    "backend/.env.example",

    # frontend core
    "frontend/src/App.tsx",
    "frontend/src/main.tsx",
    "frontend/src/infrastructure/api/client.ts",
    "frontend/src/infrastructure/api/interceptors.ts",
    "frontend/src/infrastructure/i18n/config.ts",
    "frontend/src/infrastructure/i18n/locales/ru.json",
    "frontend/src/infrastructure/i18n/locales/en.json",
    "frontend/src/infrastructure/i18n/locales/sk.json",
    "frontend/src/infrastructure/i18n/locales/pl.json",

    # frontend root files
    "frontend/package.json",
    "frontend/vite.config.ts",
    "frontend/tsconfig.json",
    "frontend/Dockerfile",

    # docs main files (пустые; вы потом наполните контентом или переместите существующие)
    "docs/01_introduction/vision.md",
    "docs/01_introduction/business_requirements.md",
    "docs/02_functional_requirements/use_cases.md",
    "docs/02_functional_requirements/business_rules.md",
    "docs/02_functional_requirements/modules/auth.md",
    "docs/02_functional_requirements/modules/fleet.md",
    "docs/02_functional_requirements/modules/cargo.md",
    "docs/02_functional_requirements/modules/planning.md",
    "docs/02_functional_requirements/modules/integrations.md",
    "docs/04_architecture/overview.md",
    "docs/04_architecture/components.md",
    "docs/06_data_model/entities.md",
    "docs/06_data_model/er_diagram.png",
    "docs/07_integrations/trans_eu.md",
    "docs/07_integrations/google_maps.md",
    "docs/07_integrations/google_sheets.md",
    "docs/07_integrations/gps.md",
    "docs/07_integrations/telegram.md",
    "docs/09_testing/TESTING_GUIDE.md",
    "docs/10_deployment/DEPLOYMENT.md",
    "docs/11_maintenance/USER_GUIDE.md",
    "docs/MiniTMS_Full_Doc_Structure.md",
    "docs/PROJECT_PLAN.md",
    "docs/ANALYSIS.md",
    "docs/CHECKLIST.md",

    # infrastructure
    "infrastructure/docker/backend.Dockerfile",
    "infrastructure/docker/frontend.Dockerfile",
    "infrastructure/docker/nginx.conf",
    "infrastructure/scripts/setup.sh",
    "infrastructure/scripts/migrate.sh",

    # .github workflows
    ".github/workflows/ci.yml",
    ".github/workflows/cd.yml",
    ".github/workflows/tests.yml",

    # root files
    "docker-compose.yml",
    "docker-compose.prod.yml",
    "README.md",
    "CONTRIBUTING.md",
    "LICENSE",
    ".gitignore",
]

def touch(path: str):
    """Создать пустой файл, если его нет."""
    if not os.path.exists(path):
        with open(path, "w", encoding="utf-8") as f:
            f.write("")

def main():
    # Создаём директории
    for d in dirs:
        os.makedirs(d, exist_ok=True)

    # Создаём файлы
    for f in files:
        # убеждаемся, что директория существует
        dir_name = os.path.dirname(f)
        if dir_name and not os.path.exists(dir_name):
            os.makedirs(dir_name, exist_ok=True)
        touch(f)

    print("Структура проекта развёрнута (директории и пустые файлы созданы).")

if __name__ == "__main__":
    main()