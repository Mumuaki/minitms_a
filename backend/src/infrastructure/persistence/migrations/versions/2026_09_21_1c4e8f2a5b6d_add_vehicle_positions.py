"""add vehicle_positions table

Revision ID: 1c4e8f2a5b6d
Revises: 9b3d5f7a1e2c
Create Date: 2026-09-21 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '1c4e8f2a5b6d'
down_revision: Union[str, None] = '9b3d5f7a1e2c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'vehicle_positions',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('vehicle_id', sa.Integer(), nullable=False),
        sa.Column('latitude', sa.Float(), nullable=True),
        sa.Column('longitude', sa.Float(), nullable=True),
        sa.Column('place_name', sa.String(length=255), nullable=True),
        sa.Column('country_code', sa.String(length=2), nullable=True),
        sa.Column('measured_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_vehicle_positions_vehicle_id', 'vehicle_positions', ['vehicle_id'])
    op.create_foreign_key(
        'fk_vehicle_positions_vehicle_id',
        'vehicle_positions',
        'vehicles',
        ['vehicle_id'],
        ['id'],
    )


def downgrade() -> None:
    op.drop_constraint('fk_vehicle_positions_vehicle_id', 'vehicle_positions', type_='foreignkey')
    op.drop_index('ix_vehicle_positions_vehicle_id', table_name='vehicle_positions')
    op.drop_table('vehicle_positions')
