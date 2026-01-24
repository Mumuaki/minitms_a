"""Create users table

Revision ID: 001
Revises: 
Create Date: 2026-01-23
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Создание таблицы users."""
    # Создаём таблицу users
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('username', sa.String(length=100), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('role', sa.String(length=50), nullable=False, server_default='observer'),
        sa.Column('language', sa.String(length=2), nullable=False, server_default='ru'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('failed_login_attempts', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('locked_until', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email'),
        sa.CheckConstraint(
            "role IN ('administrator', 'director', 'dispatcher', 'observer')",
            name='check_user_role'
        )
    )
    
    # Создаём индекс на email для быстрого поиска
    op.create_index('ix_users_email', 'users', ['email'], unique=True)


def downgrade() -> None:
    """Удаление таблицы users."""
    op.drop_index('ix_users_email', table_name='users')
    op.drop_table('users')

