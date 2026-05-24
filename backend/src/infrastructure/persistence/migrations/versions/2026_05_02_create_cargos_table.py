"""Create cargos table

Revision ID: b7c1e2d3f4a5
Revises: 430703469f38
Create Date: 2026-05-02 22:10:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision: str = 'b7c1e2d3f4a5'
down_revision: Union[str, None] = '430703469f38'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'cargos',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('external_id', sa.String(100), nullable=False),
        sa.Column('source', sa.String(50), server_default='trans.eu', nullable=True),
        sa.Column('loading_place', sa.JSON(), nullable=False),
        sa.Column('unloading_place', sa.JSON(), nullable=False),
        sa.Column('loading_date', sa.Date(), nullable=True),
        sa.Column('unloading_date', sa.Date(), nullable=True),
        sa.Column('weight', sa.Numeric(10, 2), nullable=True),
        sa.Column('body_type', sa.String(100), nullable=True),
        sa.Column('price', sa.Numeric(10, 2), nullable=True),
        sa.Column('distance_trans_eu', sa.Integer(), nullable=True),
        sa.Column('distance_osm', sa.Integer(), nullable=True),
        sa.Column('rate_per_km', sa.Numeric(10, 2), nullable=True),
        sa.Column('total_cost', sa.Numeric(10, 2), nullable=True),
        sa.Column('status_color', sa.String(20), server_default='GRAY', nullable=False),
        sa.Column('is_hidden', sa.Boolean(), server_default=sa.text('false'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    )
    op.create_index('ix_cargos_external_id', 'cargos', ['external_id'], unique=True)


def downgrade() -> None:
    op.drop_index('ix_cargos_external_id', table_name='cargos')
    op.drop_table('cargos')
