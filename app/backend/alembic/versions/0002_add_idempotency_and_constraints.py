"""add idempotency_key and unique constraints to xp_events

Revision ID: 0002_add_idempotency
Revises: 0001_initial
Create Date: 2025-10-30 00:10:00.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0002_add_idempotency'
down_revision = '0001_initial'
branch_labels = None
depends_on = None


def upgrade():
    # add idempotency_key column
    op.add_column('xp_events', sa.Column('idempotency_key', sa.String(length=200), nullable=True))
    # create unique constraint on user_id,idempotency_key
    op.create_unique_constraint('uq_user_idempotency_key', 'xp_events', ['user_id', 'idempotency_key'])
    # create unique constraint on user_id,source,source_id
    op.create_unique_constraint('uq_user_source_sourceid', 'xp_events', ['user_id', 'source', 'source_id'])


def downgrade():
    op.drop_constraint('uq_user_source_sourceid', 'xp_events', type_='unique')
    op.drop_constraint('uq_user_idempotency_key', 'xp_events', type_='unique')
    op.drop_column('xp_events', 'idempotency_key')
