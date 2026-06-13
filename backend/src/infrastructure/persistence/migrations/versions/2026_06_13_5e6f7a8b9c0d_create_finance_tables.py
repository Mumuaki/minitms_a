"""create finance tables

Revision ID: 5e6f7a8b9c0d
Revises: d8f2b1a3c4e5
Create Date: 2026-06-13 21:40:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers, used by Alembic.
revision: str = '5e6f7a8b9c0d'
down_revision: Union[str, None] = 'd8f2b1a3c4e5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Создание таблицы financial_plans
    op.create_table('financial_plans',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('vehicle_id', sa.Integer(), nullable=False),
        sa.Column('period_start', sa.Date(), nullable=False),
        sa.Column('period_end', sa.Date(), nullable=False),
        sa.Column('revenue_target', sa.Float(), nullable=False),
        sa.Column('margin_target', sa.Float(), nullable=False),
        sa.Column('distance_target', sa.Float(), nullable=False),
        sa.Column('currency', sa.String(length=3), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['vehicle_id'], ['vehicles.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_financial_plans_vehicle_id'), 'financial_plans', ['vehicle_id'], unique=False)

    # Создание таблицы orders
    op.create_table('orders',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('vehicle_id', sa.Integer(), nullable=True),
        sa.Column('cargo_id', UUID(as_uuid=True), nullable=True),
        sa.Column('revenue', sa.Float(), nullable=False),
        sa.Column('margin', sa.Float(), nullable=False),
        sa.Column('distance', sa.Float(), nullable=False),
        sa.Column('start_date', sa.Date(), nullable=False),
        sa.Column('end_date', sa.Date(), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['cargo_id'], ['cargos.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['vehicle_id'], ['vehicles.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_orders_vehicle_id'), 'orders', ['vehicle_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_orders_vehicle_id'), table_name='orders')
    op.drop_table('orders')
    op.drop_index(op.f('ix_financial_plans_vehicle_id'), table_name='financial_plans')
    op.drop_table('financial_plans')
