"""
Password Hasher - утилита для хеширования паролей.

Использует bcrypt с настраиваемым количеством раундов.
Согласно спецификации: salt rounds >= 10.
"""

import bcrypt


# Количество раундов для bcrypt (12 - хороший баланс безопасности и скорости)
BCRYPT_ROUNDS = 12


def hash_password(plain_password: str) -> str:
    """
    Хеширует пароль с использованием bcrypt.
    
    Args:
        plain_password: Пароль в открытом виде.
        
    Returns:
        Хешированный пароль (строка).
        
    Example:
        >>> hashed = hash_password("mysecretpassword")
        >>> hashed.startswith("$2b$")
        True
    """
    # Конвертируем строку в байты
    password_bytes = plain_password.encode('utf-8')
    
    # Генерируем соль и хешируем
    salt = bcrypt.gensalt(rounds=BCRYPT_ROUNDS)
    hashed = bcrypt.hashpw(password_bytes, salt)
    
    # Возвращаем как строку
    return hashed.decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Проверяет соответствие пароля хешу.
    
    Args:
        plain_password: Пароль в открытом виде для проверки.
        hashed_password: Хеш пароля из базы данных.
        
    Returns:
        True если пароль верный, False если нет.
        
    Example:
        >>> hashed = hash_password("mysecretpassword")
        >>> verify_password("mysecretpassword", hashed)
        True
        >>> verify_password("wrongpassword", hashed)
        False
    """
    # Конвертируем строки в байты
    password_bytes = plain_password.encode('utf-8')
    hashed_bytes = hashed_password.encode('utf-8')
    
    # Проверяем совпадение
    return bcrypt.checkpw(password_bytes, hashed_bytes)
