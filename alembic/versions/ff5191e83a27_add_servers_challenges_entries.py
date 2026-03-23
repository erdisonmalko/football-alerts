"""add servers challenges entries

Revision ID: ff5191e83a27
Revises: 3c9a311067f3
Create Date: 2026-03-23 20:37:42.712658

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ff5191e83a27'
down_revision: Union[str, None] = '3c9a311067f3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE TYPE serverrole AS ENUM ('owner', 'member')")
    op.execute("CREATE TYPE challengestatus AS ENUM ('open', 'locked', 'settled', 'void')")
    op.execute("CREATE TYPE challengeentrystatus AS ENUM ('pending', 'accepted', 'declined', 'void')")
    op.execute("CREATE TYPE challengeentryresult AS ENUM ('win', 'loss', 'draw', 'void')")

    op.create_table('servers',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('invite_code', sa.String(length=16), nullable=False),
        sa.Column('created_by_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['created_by_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_servers_id'), 'servers', ['id'], unique=False)
    op.create_index(op.f('ix_servers_invite_code'), 'servers', ['invite_code'], unique=True)

    op.create_table('challenges',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('server_id', sa.Integer(), nullable=False),
        sa.Column('match_id', sa.Integer(), nullable=False),
        sa.Column('created_by_id', sa.Integer(), nullable=False),
        sa.Column('stake', sa.String(length=255), nullable=False),
        sa.Column('status', sa.Enum('open', 'locked', 'settled', 'void', name='challengestatus', create_type=False), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('settled_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['created_by_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['match_id'], ['matches.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['server_id'], ['servers.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_challenges_created_by_id'), 'challenges', ['created_by_id'], unique=False)
    op.create_index(op.f('ix_challenges_id'), 'challenges', ['id'], unique=False)
    op.create_index(op.f('ix_challenges_match_id'), 'challenges', ['match_id'], unique=False)
    op.create_index(op.f('ix_challenges_server_id'), 'challenges', ['server_id'], unique=False)

    op.create_table('server_members',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('server_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('role', sa.Enum('owner', 'member', name='serverrole', create_type=False), nullable=False),
        sa.Column('joined_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('total_points', sa.Integer(), nullable=False),
        sa.Column('total_wins', sa.Integer(), nullable=False),
        sa.Column('total_losses', sa.Integer(), nullable=False),
        sa.Column('total_draws', sa.Integer(), nullable=False),
        sa.Column('challenge_count', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['server_id'], ['servers.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('server_id', 'user_id', name='uq_server_member')
    )
    op.create_index(op.f('ix_server_members_id'), 'server_members', ['id'], unique=False)
    op.create_index(op.f('ix_server_members_server_id'), 'server_members', ['server_id'], unique=False)
    op.create_index(op.f('ix_server_members_user_id'), 'server_members', ['user_id'], unique=False)

    op.create_table('challenge_entries',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('challenge_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('prediction', sa.String(length=100), nullable=True),
        sa.Column('status', sa.Enum('pending', 'accepted', 'declined', 'void', name='challengeentrystatus', create_type=False), nullable=False),
        sa.Column('points_earned', sa.Integer(), nullable=False),
        sa.Column('result', sa.Enum('win', 'loss', 'draw', 'void', name='challengeentryresult', create_type=False), nullable=True),
        sa.Column('responded_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['challenge_id'], ['challenges.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('challenge_id', 'user_id', name='uq_challenge_entry')
    )
    op.create_index(op.f('ix_challenge_entries_challenge_id'), 'challenge_entries', ['challenge_id'], unique=False)
    op.create_index(op.f('ix_challenge_entries_id'), 'challenge_entries', ['id'], unique=False)
    op.create_index(op.f('ix_challenge_entries_user_id'), 'challenge_entries', ['user_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_challenge_entries_user_id'), table_name='challenge_entries')
    op.drop_index(op.f('ix_challenge_entries_id'), table_name='challenge_entries')
    op.drop_index(op.f('ix_challenge_entries_challenge_id'), table_name='challenge_entries')
    op.drop_table('challenge_entries')
    op.drop_index(op.f('ix_server_members_user_id'), table_name='server_members')
    op.drop_index(op.f('ix_server_members_server_id'), table_name='server_members')
    op.drop_index(op.f('ix_server_members_id'), table_name='server_members')
    op.drop_table('server_members')
    op.drop_index(op.f('ix_challenges_server_id'), table_name='challenges')
    op.drop_index(op.f('ix_challenges_match_id'), table_name='challenges')
    op.drop_index(op.f('ix_challenges_id'), table_name='challenges')
    op.drop_index(op.f('ix_challenges_created_by_id'), table_name='challenges')
    op.drop_table('challenges')
    op.drop_index(op.f('ix_servers_invite_code'), table_name='servers')
    op.drop_index(op.f('ix_servers_id'), table_name='servers')
    op.drop_table('servers')
    op.execute("DROP TYPE IF EXISTS challengeentryresult")
    op.execute("DROP TYPE IF EXISTS challengeentrystatus")
    op.execute("DROP TYPE IF EXISTS challengestatus")
    op.execute("DROP TYPE IF EXISTS serverrole")