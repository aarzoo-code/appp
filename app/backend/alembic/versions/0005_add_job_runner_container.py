"""add runner_container_id to jobs

Revision ID: 0005_add_job_runner_container
Revises: 0004_add_is_admin
Create Date: 2025-10-30 15:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0005_add_job_runner_container'
down_revision = '0004_add_is_admin'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('jobs', sa.Column('runner_container_id', sa.String(length=200), nullable=True))


def downgrade():
    op.drop_column('jobs', 'runner_container_id')
