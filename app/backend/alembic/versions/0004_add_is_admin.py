"""add is_admin to users

Revision ID: 0004_add_is_admin
Revises: 0003_add_user_fields
Create Date: 2025-10-30 12:30:00.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0004_add_is_admin'
down_revision = '0003_add_user_fields'
branch_labels = None
depends_on = None


def upgrade():
    # add is_admin column with default false
    op.add_column('users', sa.Column('is_admin', sa.Boolean(), nullable=False, server_default=sa.text('0')))


def downgrade():
    op.drop_column('users', 'is_admin')
