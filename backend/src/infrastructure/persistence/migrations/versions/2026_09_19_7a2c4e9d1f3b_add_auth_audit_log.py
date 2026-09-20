"""add auth audit log table

Revision ID: 7a2c4e9d1f3b
Revises: 6f2b9d4e8a1c
Create Date: 2026-09-19 22:10:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '7a2c4e9d1f3b'
down_revision: Union[str, None] = '6f2b9d4e8a1c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'auth_audit_log',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('ip', sa.String(length=45), nullable=True),
        sa.Column('user_agent', sa.String(length=512), nullable=True),
        sa.Column('success', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_auth_audit_log_email', 'auth_audit_log', ['email'])


def downgrade() -> None:
    op.drop_index('ix_auth_audit_log_email', table_name='auth_audit_log')
    op.drop_table('auth_audit_log')
