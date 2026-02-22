"""
Создание первого администратора в системе.
Запуск: python create_admin.py (или docker compose exec backend python create_admin.py)
"""
import sys
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# Загружаем .env
env_path = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(env_path)

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    print("DATABASE_URL not found in .env")
    sys.exit(1)

# Путь к src для импорта hash_password
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))
from infrastructure.security.password_hasher import hash_password

print("=" * 60)
print("Creating administrator...")
print("=" * 60)

try:
    engine = create_engine(DATABASE_URL)

    with engine.connect() as conn:
        result = conn.execute(text("SELECT COUNT(*) FROM users"))
        count = result.scalar()

        if count > 0:
            print(f"Users already exist ({count}). Skipping.")
            sys.exit(0)

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

        print("Administrator created!")
        print("  Email: admin@minitms.local")
        print("  Password: admin123")
        print("  Change password after first login!")

except Exception as e:
    print(f"Error: {type(e).__name__}: {e}")
    sys.exit(1)
