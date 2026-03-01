"""
Создание первого администратора в системе.
Запуск: python create_admin.py (или docker compose exec backend python create_admin.py)
"""
import sys
import os
import logging
from dotenv import load_dotenv
from sqlalchemy import create_engine, text, inspect

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# Загружаем .env
env_path = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(env_path)

DATABASE_URL = os.getenv("DATABASE_URL")
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@minitms.local")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")

if not DATABASE_URL:
    logger.error("DATABASE_URL not found in .env")
    sys.exit(1)

# Путь к src для импорта hash_password
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))
try:
    from infrastructure.security.password_hasher import hash_password
except ImportError:
    # Попытка импорта если запуск из корня backend
    sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
    from src.infrastructure.security.password_hasher import hash_password

logger.info("=" * 60)
logger.info("Checking/Creating administrator...")
logger.info("=" * 60)

try:
    engine = create_engine(DATABASE_URL)

    with engine.connect() as conn:
        # Проверяем, существует ли таблица users (важно при первом запуске до миграций)
        inspector = inspect(engine)
        if 'users' not in inspector.get_table_names():
            logger.warning("Table 'users' does not exist yet. Please run migrations first.")
            sys.exit(0)  # Выходим без ошибки, чтобы не ломать entrypoint

        # Проверяем наличие пользователей
        result = conn.execute(text("SELECT COUNT(*) FROM users"))
        count = result.scalar()

        if count > 0:
            # Проверяем, есть ли именно этот админ
            admin_check = conn.execute(
                text("SELECT id FROM users WHERE email = :email"),
                {"email": ADMIN_EMAIL}
            ).fetchone()
            
            if admin_check:
                logger.info(f"Admin '{ADMIN_EMAIL}' already exists. Skipping.")
                sys.exit(0)
            else:
                logger.info(f"Users exist ({count}), but admin '{ADMIN_EMAIL}' is missing.")

        password_hash = hash_password(ADMIN_PASSWORD)
        conn.execute(text("""
            INSERT INTO users (
                email, username, password_hash, role, language, is_active
            ) VALUES (
                :email, :username, :password_hash, :role, :language, :is_active
            )
        """), {
            "email": ADMIN_EMAIL,
            "username": "Administrator",
            "password_hash": password_hash,
            "role": "administrator",
            "language": "ru",
            "is_active": True
        })
        conn.commit()

        logger.info("Administrator created successfully!")
        logger.info(f"  Email: {ADMIN_EMAIL}")
        logger.info("  Password: (from environment or default)")
        logger.info("  Please change password after first login if using defaults.")

except Exception as e:
    logger.error(f"Error: {type(e).__name__}: {e}")
    sys.exit(1)
