"""add servers and related tables

Revision ID: 34c627bb77e0
Revises: 3b31a4298e82
Create Date: 2026-03-28 23:31:52.683918

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = '34c627bb77e0'
down_revision: Union[str, None] = '3b31a4298e82'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('calendar_events',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('match_id', sa.Integer(), nullable=False),
        sa.Column('google_event_id', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['match_id'], ['matches.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'match_id', name='uq_user_match_calendar')
    )
    op.create_index(op.f('ix_calendar_events_user_id'), 'calendar_events', ['user_id'], unique=False)
    op.create_index(op.f('ix_calendar_events_match_id'), 'calendar_events', ['match_id'], unique=False)

    op.create_table('server_join_requests',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('server_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('status', sa.Enum('pending', 'accepted', 'declined', name='joinrequeststatus'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['server_id'], ['servers.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('server_id', 'user_id', name='uq_server_join_request')
    )
    op.create_index(op.f('ix_server_join_requests_server_id'), 'server_join_requests', ['server_id'], unique=False)
    op.create_index(op.f('ix_server_join_requests_user_id'), 'server_join_requests', ['user_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_server_join_requests_user_id'), table_name='server_join_requests')
    op.drop_index(op.f('ix_server_join_requests_server_id'), table_name='server_join_requests')
    op.drop_table('server_join_requests')
    op.execute("DROP TYPE IF EXISTS joinrequeststatus")

    op.drop_index(op.f('ix_calendar_events_match_id'), table_name='calendar_events')
    op.drop_index(op.f('ix_calendar_events_user_id'), table_name='calendar_events')
    op.drop_table('calendar_events')