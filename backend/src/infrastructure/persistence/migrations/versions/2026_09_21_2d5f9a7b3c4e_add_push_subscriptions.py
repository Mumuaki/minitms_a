"""add push_subscriptions table

Revision ID: 2d5f9a7b3c4e
Revises: 1c4e8f2a5b6d
Create Date: 2026-09-21 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


revision: str = '2d5f9a7b3c4e'
down_revision: Union[str, None] = '1c4e8f2a5b6d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'push_subscriptions',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('endpoint', sa.String(length=1024), nullable=False),
        sa.Column('subscription', JSONB(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('endpoint'),
    )
    op.create_index('ix_push_subscriptions_user_id', 'push_subscriptions', ['user_id'])
    op.create_foreign_key(
        'fk_push_subscriptions_user_id',
        'push_subscriptions',
        'users',
        ['user_id'],
        ['id'],
    )


def downgrade() -> None:
    op.drop_constraint('fk_push_subscriptions_user_id', 'push_subscriptions', type_='foreignkey')
    op.drop_index('ix_push_subscriptions_user_id', table_name='push_subscriptions')
    op.drop_table('push_subscriptions')
