"""add default users

Revision ID: d8f2b1a3c4e5
Revises: c8d2f3e4a5b6
Create Date: 2026-06-13 21:24:00.000000

"""
import os
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import table, column

# revision identifiers, used by Alembic.
revision: str = 'd8f2b1a3c4e5'
down_revision: Union[str, None] = 'c8d2f3e4a5b6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Динамический импорт хэшера паролей, так как он доступен в контексте выполнения Alembic
    try:
        from backend.src.infrastructure.security.password_hasher import hash_password as get_password_hash
    except ImportError:
        # Fallback, если запускается вне полного контекста приложения
        def get_password_hash(password: str) -> str:
            import bcrypt
            # passlib 1.7.4 is incompatible with bcrypt>=4.1; use bcrypt directly
            pwd_bytes = password.encode("utf-8")[:72]
            return bcrypt.hashpw(pwd_bytes, bcrypt.gensalt(rounds=12)).decode("utf-8")

    users_table = table('users',
        column('email', sa.String),
        column('username', sa.String),
        column('password_hash', sa.String),
        column('role', sa.String),
        column('language', sa.String),
        column('is_active', sa.Boolean),
        column('failed_login_attempts', sa.Integer)
    )

    # Passwords MUST come from the environment. This file is public, so a
    # hardcoded seed password would hand out production admin access.
    seed_specs = [
        ('admin@minitms.com', 'Admin User', 'administrator', 'SEED_ADMIN_PASSWORD'),
        ('director@minitms.com', 'Director User', 'director', 'SEED_DIRECTOR_PASSWORD'),
        ('dispatcher@minitms.com', 'Dispatcher User', 'dispatcher', 'SEED_DISPATCHER_PASSWORD'),
    ]

    rows = []
    missing = []
    for email, username, role, env_key in seed_specs:
        password = (os.getenv(env_key) or '').strip()
        if not password:
            missing.append(env_key)
            continue
        rows.append({
            'email': email,
            'username': username,
            'password_hash': get_password_hash(password),
            'role': role,
            'language': 'ru',
            'is_active': True,
            'failed_login_attempts': 0,
        })

    if missing:
        print('[d8f2b1a3c4e5] no password set for: ' + ', '.join(missing) + ' - those users are skipped')
    if not rows:
        print('[d8f2b1a3c4e5] no SEED_*_PASSWORD variables set - no default users created. '
              'Set them, or use create_admin.py, if initial accounts are needed.')
        return

    op.bulk_insert(users_table, rows)


def downgrade() -> None:
    op.execute("DELETE FROM users WHERE email IN ('admin@minitms.com', 'director@minitms.com', 'dispatcher@minitms.com')")
