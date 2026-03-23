"""placeholder for deleted migration

Revision ID: 3b31a4298e82
Revises: ff5191e83a27
Create Date: 2026-03-23 21:11:24.448131

"""
from typing import Sequence, Union

revision: str = '3b31a4298e82'
down_revision: Union[str, None] = 'ff5191e83a27'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass