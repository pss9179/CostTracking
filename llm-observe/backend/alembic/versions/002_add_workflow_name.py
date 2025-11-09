"""Add workflow_name to traces table

Revision ID: 002
Revises: 001
Create Date: 2024-01-01 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '002'
down_revision: Union[str, None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add workflow_name column to traces table
    op.add_column('traces', sa.Column('workflow_name', sa.String(length=255), nullable=True))
    # Create index on workflow_name for faster queries
    op.create_index(op.f('ix_traces_workflow_name'), 'traces', ['workflow_name'], unique=False)


def downgrade() -> None:
    # Drop index
    op.drop_index(op.f('ix_traces_workflow_name'), table_name='traces')
    # Drop column
    op.drop_column('traces', 'workflow_name')

