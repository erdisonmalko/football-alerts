"""add google_tokens table

Revision ID: 3c9a311067f3
Revises: 48b930667d4d
Create Date: 2026-03-17 20:54:40.119688

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3c9a311067f3'
down_revision: Union[str, None] = '48b930667d4d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('google_tokens',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('access_token', sa.Text(), nullable=False),
        sa.Column('refresh_token', sa.Text(), nullable=False),
        sa.Column('token_expiry', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id')
    )
    op.create_index(op.f('ix_google_tokens_user_id'), 'google_tokens', ['user_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_google_tokens_user_id'), table_name='google_tokens')
    op.drop_table('google_tokens')
