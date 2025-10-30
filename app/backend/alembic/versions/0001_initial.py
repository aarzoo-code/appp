"""create initial tables

Revision ID: 0001_initial
Revises: 
Create Date: 2025-10-30 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0001_initial'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'users',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('display_name', sa.String(120), nullable=False),
        sa.Column('email', sa.String(200), nullable=True),
        sa.Column('xp_total', sa.Integer, nullable=False, server_default='0'),
        sa.Column('level', sa.Integer, nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.text('(CURRENT_TIMESTAMP)')),
    )

    op.create_table(
        'xp_events',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('user_id', sa.Integer, sa.ForeignKey('users.id'), nullable=False),
        sa.Column('amount', sa.Integer, nullable=False),
        sa.Column('source', sa.String(50), nullable=True),
        sa.Column('source_id', sa.String(200), nullable=True),
        sa.Column('meta', sa.JSON, nullable=True),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.text('(CURRENT_TIMESTAMP)')),
    )

    op.create_table(
        'badges',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('code', sa.String(100), nullable=False, unique=True),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('description', sa.String(500), nullable=True),
        sa.Column('icon', sa.String(500), nullable=True),
    )

    op.create_table(
        'user_badges',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('user_id', sa.Integer, sa.ForeignKey('users.id'), nullable=False),
        sa.Column('badge_id', sa.Integer, sa.ForeignKey('badges.id'), nullable=False),
        sa.Column('earned_at', sa.DateTime, nullable=False, server_default=sa.text('(CURRENT_TIMESTAMP)')),
    )

    op.create_table(
        'streaks',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('user_id', sa.Integer, sa.ForeignKey('users.id'), nullable=False),
        sa.Column('current_streak', sa.Integer, nullable=False, server_default='0'),
        sa.Column('last_checkin_date', sa.Date, nullable=True),
    )


def downgrade():
    op.drop_table('streaks')
    op.drop_table('user_badges')
    op.drop_table('badges')
    op.drop_table('xp_events')
    op.drop_table('users')
