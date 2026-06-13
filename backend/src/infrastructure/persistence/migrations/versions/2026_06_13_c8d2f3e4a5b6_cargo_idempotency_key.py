"""cargo_idempotency_key

Revision ID: c8d2f3e4a5b6
Revises: b7c1e2d3f4a5
Create Date: 2026-06-13 20:38:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c8d2f3e4a5b6'
down_revision: Union[str, None] = 'b7c1e2d3f4a5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Drop unique index on external_id and recreate as non-unique
    op.drop_index('ix_cargos_external_id', table_name='cargos')
    op.create_index('ix_cargos_external_id', 'cargos', ['external_id'], unique=False)

    # 2. Add snapshot_time_bucket column (nullable for now to allow backfill)
    op.add_column('cargos', sa.Column('snapshot_time_bucket', sa.DateTime(timezone=True), nullable=True))

    # 3. Backfill data
    op.execute("UPDATE cargos SET source = 'trans.eu' WHERE source IS NULL")
    op.execute("UPDATE cargos SET snapshot_time_bucket = date_trunc('hour', created_at)")

    # 4. Make snapshot_time_bucket NOT NULL
    op.alter_column('cargos', 'snapshot_time_bucket', existing_type=sa.DateTime(timezone=True), nullable=False)

    # 5. Create composite unique constraint
    op.create_unique_constraint('uix_cargo_source_ext_bucket', 'cargos', ['source', 'external_id', 'snapshot_time_bucket'])


def downgrade() -> None:
    op.drop_constraint('uix_cargo_source_ext_bucket', 'cargos', type_='unique')
    op.drop_column('cargos', 'snapshot_time_bucket')
    op.drop_index('ix_cargos_external_id', table_name='cargos')
    op.create_index('ix_cargos_external_id', 'cargos', ['external_id'], unique=True)
