"""add username, password_hash, github_id to users

Revision ID: 0003_add_user_fields
Revises: 0002_add_idempotency
Create Date: 2025-10-30 12:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0003_add_user_fields'
down_revision = '0002_add_idempotency'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('users', sa.Column('username', sa.String(length=80), nullable=True))
    op.add_column('users', sa.Column('password_hash', sa.String(length=300), nullable=True))
    op.add_column('users', sa.Column('github_id', sa.String(length=200), nullable=True))
    # add unique constraints where appropriate
    op.create_unique_constraint('uq_users_username', 'users', ['username'])
    op.create_unique_constraint('uq_users_github_id', 'users', ['github_id'])


def downgrade():
    op.drop_constraint('uq_users_github_id', 'users', type_='unique')
    op.drop_constraint('uq_users_username', 'users', type_='unique')
    op.drop_column('users', 'github_id')
    op.drop_column('users', 'password_hash')
    op.drop_column('users', 'username')
