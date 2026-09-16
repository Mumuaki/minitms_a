"""
API Endpoints для управления пользователями.
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status

from backend.src.infrastructure.api.v1.schemas.user_schema import UserCreate, UserUpdate, UserResponse
from backend.src.infrastructure.api.v1.dependencies import get_user_repository, require_role, CurrentUser, get_current_user
from backend.src.domain.repositories.user_repository import UserRepository
from backend.src.domain.entities.user import User, UserRole
from backend.src.infrastructure.security.password_hasher import hash_password

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/", response_model=List[UserResponse], summary="Список всех пользователей")
async def get_users(
    skip: int = 0,
    limit: int = 100,
    user_repo: UserRepository = Depends(get_user_repository),
    current_user: CurrentUser = Depends(require_role(["administrator"]))
):
    """
    Получение списка всех пользователей.
    Доступно только Администраторам.
    """
    users = user_repo.get_all(skip, limit)
    
    # Явная конвертация для надежности
    results = []
    for u in users:
        role_val = u.role.value if hasattr(u.role, 'value') else u.role
        results.append(
            UserResponse(
                id=u.id,
                email=u.email,
                username=u.username,
                role=role_val,
                language=u.language,
                is_active=u.is_active
            )
        )
    return results


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED, summary="Создать пользователя")
async def create_user(
    user_in: UserCreate,
    user_repo: UserRepository = Depends(get_user_repository),
    current_user: CurrentUser = Depends(require_role(["administrator"]))
):
    """
    Создание нового пользователя.
    Доступно только Администраторам.
    """
    # Проверка email
    if user_repo.get_by_email(user_in.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists"
        )
    
    # Валидация роли
    try:
        role_enum = UserRole(user_in.role.lower())
    except ValueError:
        allowed = [e.value for e in UserRole]
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid role. Allowed roles: {allowed}"
        )

    # Хеширование пароля
    hashed_password = hash_password(user_in.password)

    new_user = User(
        email=user_in.email,
        username=user_in.username,
        password_hash=hashed_password,
        role=role_enum,
        language=user_in.language,
        is_active=True
    )
    
    created_user = user_repo.create(new_user)
    
    return UserResponse(
        id=created_user.id,
        email=created_user.email,
        username=created_user.username,
        role=created_user.role.value,
        language=created_user.language,
        is_active=created_user.is_active
    )


@router.put("/{user_id}", response_model=UserResponse, summary="Обновить пользователя")
async def update_user(
    user_id: int,
    user_in: UserUpdate,
    user_repo: UserRepository = Depends(get_user_repository),
    current_user: CurrentUser = Depends(require_role(["administrator"]))
):
    """
    Обновление данных пользователя.
    Доступно только Администраторам.
    """
    user = user_repo.get_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Email меняем только если он реально изменился, и следим за уникальностью
    if user_in.email is not None and user_in.email.lower() != user.email.lower():
        existing = user_repo.get_by_email(user_in.email)
        if existing and existing.id != user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this email already exists"
            )
        user.email = user_in.email.lower()

    if user_in.username is not None:
        user.username = user_in.username

    if user_in.role is not None:
        try:
            user.role = UserRole(user_in.role.lower())
        except ValueError:
            allowed = [e.value for e in UserRole]
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid role. Allowed roles: {allowed}"
            )

    if user_in.language is not None:
        user.language = user_in.language

    if user_in.is_active is not None:
        # Не позволяем администратору заблокировать самого себя
        if user.id == current_user.id and user_in.is_active is False:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot deactivate yourself"
            )
        user.is_active = user_in.is_active

    if user_in.password:
        user.password_hash = hash_password(user_in.password)

    updated = user_repo.save(user)

    return UserResponse(
        id=updated.id,
        email=updated.email,
        username=updated.username,
        role=updated.role.value if hasattr(updated.role, 'value') else updated.role,
        language=updated.language,
        is_active=updated.is_active
    )


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Удалить пользователя")
async def delete_user(
    user_id: int,
    user_repo: UserRepository = Depends(get_user_repository),
    current_user: CurrentUser = Depends(require_role(["administrator"]))
):
    """
    Удаление пользователя.
    Доступно только Администраторам.
    Нельзя удалить самого себя.
    """
    user = user_repo.get_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete yourself"
        )
        
    user_repo.delete(user)
    return None
