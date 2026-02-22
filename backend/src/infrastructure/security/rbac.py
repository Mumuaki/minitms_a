"""
RBAC (Role-Based Access Control) - управление ролями и правами доступа.

Определяет матрицу ролей и проверяет права доступа пользователей
к различным ресурсам системы.

Согласно спецификации FR-AUTH-002:
- Administrator: Полный доступ
- Director: Управленческий доступ (без администрирования пользователей)
- Dispatcher: Операционный доступ
- Observer: Только чтение
"""

from enum import Enum
from typing import Set


class Permission(Enum):
    """Разрешения в системе."""
    
    # Пользователи
    USER_CREATE = "user:create"
    USER_READ = "user:read"
    USER_UPDATE = "user:update"
    USER_DELETE = "user:delete"
    
    # Настройки системы
    SETTINGS_READ = "settings:read"
    SETTINGS_UPDATE = "settings:update"
    
    # Автопарк
    FLEET_CREATE = "fleet:create"
    FLEET_READ = "fleet:read"
    FLEET_UPDATE = "fleet:update"
    FLEET_DELETE = "fleet:delete"
    
    # Грузы
    CARGO_READ = "cargo:read"
    CARGO_SEARCH = "cargo:search"
    
    # Email
    EMAIL_SEND = "email:send"
    EMAIL_READ = "email:read"
    
    # Отчёты
    REPORT_READ = "report:read"
    REPORT_EXPORT = "report:export"
    
    # Google Sheets
    SHEETS_READ = "sheets:read"
    SHEETS_EDIT = "sheets:edit"
    
    # Финансовое планирование
    FINANCE_READ = "finance:read"
    FINANCE_EDIT = "finance:edit"


# Матрица ролей и разрешений
# Соответствует таблице из MiniTMS_Full_Doc_Structure.md
ROLE_PERMISSIONS: dict[str, Set[Permission]] = {
    "administrator": {
        # Полный доступ
        Permission.USER_CREATE,
        Permission.USER_READ,
        Permission.USER_UPDATE,
        Permission.USER_DELETE,
        Permission.SETTINGS_READ,
        Permission.SETTINGS_UPDATE,
        Permission.FLEET_CREATE,
        Permission.FLEET_READ,
        Permission.FLEET_UPDATE,
        Permission.FLEET_DELETE,
        Permission.CARGO_READ,
        Permission.CARGO_SEARCH,
        Permission.EMAIL_SEND,
        Permission.EMAIL_READ,
        Permission.REPORT_READ,
        Permission.REPORT_EXPORT,
        Permission.SHEETS_READ,
        Permission.SHEETS_EDIT,
        Permission.FINANCE_READ,
        Permission.FINANCE_EDIT,
    },
    
    "director": {
        # Управленческий доступ (без управления пользователями)
        Permission.USER_READ,  # Только просмотр
        Permission.SETTINGS_READ,
        Permission.SETTINGS_UPDATE,
        Permission.FLEET_CREATE,
        Permission.FLEET_READ,
        Permission.FLEET_UPDATE,
        Permission.FLEET_DELETE,
        Permission.CARGO_READ,
        Permission.CARGO_SEARCH,
        Permission.EMAIL_SEND,
        Permission.EMAIL_READ,
        Permission.REPORT_READ,
        Permission.REPORT_EXPORT,
        Permission.SHEETS_READ,
        Permission.SHEETS_EDIT,
        Permission.FINANCE_READ,
        Permission.FINANCE_EDIT,
    },
    
    "dispatcher": {
        # Операционный доступ
        Permission.FLEET_CREATE,
        Permission.FLEET_READ,
        Permission.FLEET_UPDATE,
        Permission.CARGO_READ,
        Permission.CARGO_SEARCH,
        Permission.EMAIL_SEND,
        Permission.EMAIL_READ,
        Permission.REPORT_READ,
        Permission.REPORT_EXPORT,
        Permission.SHEETS_READ,
        Permission.SHEETS_EDIT,
        Permission.FINANCE_READ,  # Только просмотр своих показателей
    },
    
    "observer": {
        # Только чтение
        Permission.FLEET_READ,
        Permission.CARGO_READ,
        Permission.REPORT_READ,
        Permission.SHEETS_READ,
        Permission.FINANCE_READ,
    },
}

def normalize_role(role: str | None) -> str:
    """
    Нормализует входную роль к каноническому значению RBAC.

    Guest считается алиасом Observer для read-only доступа.
    """
    if not isinstance(role, str):
        return ""
    role_lower = role.strip().lower()
    if not role_lower:
        return ""
    if role_lower == "guest":
        return "observer"
    return role_lower


def has_permission(role: str | None, permission: Permission) -> bool:
    """
    Проверяет, имеет ли роль указанное разрешение.
    
    Args:
        role: Название роли (administrator, director, dispatcher, observer).
        permission: Разрешение для проверки.
        
    Returns:
        True если роль имеет разрешение, False если нет.
        
    Example:
        >>> has_permission("administrator", Permission.USER_CREATE)
        True
        >>> has_permission("observer", Permission.USER_CREATE)
        False
    """
    role_lower = normalize_role(role)
    if role_lower not in ROLE_PERMISSIONS:
        return False
    
    return permission in ROLE_PERMISSIONS[role_lower]


def get_role_permissions(role: str | None) -> Set[Permission]:
    """
    Возвращает все разрешения для роли.
    
    Args:
        role: Название роли.
        
    Returns:
        Множество разрешений или пустое множество если роль не найдена.
    """
    role_lower = normalize_role(role)
    return ROLE_PERMISSIONS.get(role_lower, set())


def is_admin(role: str | None) -> bool:
    """Проверяет, является ли роль администратором."""
    return normalize_role(role) == "administrator"


def can_manage_users(role: str | None) -> bool:
    """Проверяет, может ли роль управлять пользователями."""
    return has_permission(role, Permission.USER_CREATE)


def can_edit_settings(role: str | None) -> bool:
    """Проверяет, может ли роль редактировать настройки."""
    return has_permission(role, Permission.SETTINGS_UPDATE)


def can_send_email(role: str | None) -> bool:
    """Проверяет, может ли роль отправлять email."""
    return has_permission(role, Permission.EMAIL_SEND)


def can_edit_finance(role: str | None) -> bool:
    """Проверяет, может ли роль редактировать финансовые планы."""
    return has_permission(role, Permission.FINANCE_EDIT)
