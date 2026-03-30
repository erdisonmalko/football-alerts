"""add is_public to servers

Revision ID: 4d8a5c9e2f1b
Revises: 34c627bb77e0
Create Date: 2026-03-30 23:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = '4d8a5c9e2f1b'
down_revision: Union[str, None] = '34c627bb77e0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('servers', sa.Column('is_public', sa.Boolean(), nullable=False, server_default='true'))


def downgrade() -> None:
    op.drop_column('servers', 'is_public')
