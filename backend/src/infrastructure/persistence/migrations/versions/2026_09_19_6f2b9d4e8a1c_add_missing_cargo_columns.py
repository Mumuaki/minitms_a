"""add missing cargo columns (route_polyline, company_rating, published_at)

Revision ID: 6f2b9d4e8a1c
Revises: 5e6f7a8b9c0d
Create Date: 2026-09-19 20:35:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6f2b9d4e8a1c'
down_revision: Union[str, None] = '5e6f7a8b9c0d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('cargos', sa.Column('route_polyline', sa.String(), nullable=True))
    op.add_column('cargos', sa.Column('company_rating', sa.String(length=50), nullable=True))
    op.add_column('cargos', sa.Column('published_at', sa.String(length=100), nullable=True))


def downgrade() -> None:
    op.drop_column('cargos', 'published_at')
    op.drop_column('cargos', 'company_rating')
    op.drop_column('cargos', 'route_polyline')
