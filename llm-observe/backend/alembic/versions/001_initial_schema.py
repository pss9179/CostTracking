"""Initial schema

Revision ID: 001
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create span_summaries table
    op.create_table(
        'span_summaries',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('trace_id', sa.String(length=32), nullable=False),
        sa.Column('span_id', sa.String(length=16), nullable=False),
        sa.Column('parent_span_id', sa.String(length=16), nullable=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('model', sa.String(length=100), nullable=True),
        sa.Column('prompt_tokens', sa.Integer(), nullable=False),
        sa.Column('completion_tokens', sa.Integer(), nullable=False),
        sa.Column('total_tokens', sa.Integer(), nullable=False),
        sa.Column('cost_usd', sa.Float(), nullable=False),
        sa.Column('start_time', sa.Float(), nullable=False),
        sa.Column('duration_ms', sa.Float(), nullable=True),
        sa.Column('tenant_id', sa.String(length=100), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_span_summaries_trace_id'), 'span_summaries', ['trace_id'], unique=False)
    op.create_index(op.f('ix_span_summaries_span_id'), 'span_summaries', ['span_id'], unique=False)
    op.create_index(op.f('ix_span_summaries_tenant_id'), 'span_summaries', ['tenant_id'], unique=False)
    
    # Create traces table
    op.create_table(
        'traces',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('trace_id', sa.String(length=32), nullable=False),
        sa.Column('tenant_id', sa.String(length=100), nullable=False),
        sa.Column('root_span_name', sa.String(length=255), nullable=True),
        sa.Column('total_cost_usd', sa.Float(), nullable=False),
        sa.Column('total_tokens', sa.Integer(), nullable=False),
        sa.Column('span_count', sa.Integer(), nullable=False),
        sa.Column('start_time', sa.Float(), nullable=False),
        sa.Column('duration_ms', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('trace_id')
    )
    op.create_index(op.f('ix_traces_trace_id'), 'traces', ['trace_id'], unique=True)
    op.create_index(op.f('ix_traces_tenant_id'), 'traces', ['tenant_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_traces_tenant_id'), table_name='traces')
    op.drop_index(op.f('ix_traces_trace_id'), table_name='traces')
    op.drop_table('traces')
    op.drop_index(op.f('ix_span_summaries_tenant_id'), table_name='span_summaries')
    op.drop_index(op.f('ix_span_summaries_span_id'), table_name='span_summaries')
    op.drop_index(op.f('ix_span_summaries_trace_id'), table_name='span_summaries')
    op.drop_table('span_summaries')

