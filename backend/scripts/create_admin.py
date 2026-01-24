"""
Создание первого администратора в системе.
"""

import sys
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# Загружаем .env
env_path = os.path.join(os.path.dirname(__file__), "../.env")
load_dotenv(env_path)

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    print("❌ DATABASE_URL не найден в .env")
    sys.exit(1)

# Добавляем путь к модулям
backend_src = os.path.abspath(os.path.join(os.path.dirname(__file__), "../src"))
sys.path.insert(0, backend_src)

from infrastructure.security.password_hasher import hash_password

print("=" * 60)
print("СОЗДАНИЕ АДМИНИСТРАТОРА")
print("=" * 60)

try:
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as conn:
        # Проверяем, есть ли уже пользователи
        result = conn.execute(text("SELECT COUNT(*) FROM users"))
        count = result.scalar()
        
        if count > 0:
            print(f"\n⚠️  В базе уже есть {count} пользователей")
            print("Пропускаю создание администратора.")
            sys.exit(0)
        
        # Создаём администратора
        print("\nСоздание пользователя admin@minitms.local...")
        
        password_hash = hash_password("admin123")
        
        conn.execute(text("""
            INSERT INTO users (
                email, username, password_hash, role, language, is_active
            ) VALUES (
                :email, :username, :password_hash, :role, :language, :is_active
            )
        """), {
            "email": "admin@minitms.local",
            "username": "Administrator",
            "password_hash": password_hash,
            "role": "administrator",
            "language": "ru",
            "is_active": True
        })
        
        conn.commit()
        
        print("✅ Администратор создан!")
        print()
        print("Данные для входа:")
        print("  Email: admin@minitms.local")
        print("  Password: admin123")
        print()
        print("⚠️  ВАЖНО: Смените пароль после первого входа!")
        
except Exception as e:
    print(f"\n❌ Ошибка: {type(e).__name__}")
    print(f"   {str(e)[:200]}")
    sys.exit(1)
