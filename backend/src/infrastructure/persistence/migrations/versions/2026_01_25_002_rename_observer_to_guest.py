"""Rename Observer to Guest

Revision ID: 002
Revises: 001
Create Date: 2026-01-25 00:15:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '002'
down_revision: Union[str, None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Drop old constraint
    op.drop_constraint('check_user_role', 'users', type_='check')
    
    # 2. Update existing data
    op.execute("UPDATE users SET role = 'guest' WHERE role = 'observer'")
    
    # 3. Create new constraint
    op.create_check_constraint(
        'check_user_role',
        'users',
        "role IN ('administrator', 'director', 'dispatcher', 'guest')"
    )
    
    # 4. Update server default
    op.alter_column('users', 'role', server_default='guest')


def downgrade() -> None:
    # 1. Drop new constraint
    op.drop_constraint('check_user_role', 'users', type_='check')
    
    # 2. Revert data
    op.execute("UPDATE users SET role = 'observer' WHERE role = 'guest'")
    
    # 3. Restore old constraint
    op.create_check_constraint(
        'check_user_role',
        'users',
        "role IN ('administrator', 'director', 'dispatcher', 'observer')"
    )
    
    # 4. Restore server default
    op.alter_column('users', 'role', server_default='observer')
