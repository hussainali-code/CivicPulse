"""initial schema

Revision ID: 0001_initial
Revises: 
Create Date: 2026-09-27 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '0001_initial'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create Enums
    category_enum = postgresql.ENUM(
        'water', 'electricity', 'sanitation', 'roads', 'streetlights', 'other',
        name='category_enum'
    )
    category_enum.create(op.get_bind(), checkfirst=True)

    priority_enum = postgresql.ENUM(
        'high', 'normal', 'low',
        name='priority_enum'
    )
    priority_enum.create(op.get_bind(), checkfirst=True)

    status_enum = postgresql.ENUM(
        'open', 'in_progress', 'resolved', 'rejected',
        name='status_enum'
    )
    status_enum.create(op.get_bind(), checkfirst=True)

    # 2. Create Complaints Table
    op.create_table(
        'complaints',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('text', sa.String(length=2000), nullable=False),
        sa.Column('location', sa.String(length=200), nullable=False),
        sa.Column('reporter_contact', sa.String(length=255), nullable=True),
        sa.Column('category', category_enum, nullable=False),
        sa.Column('priority', priority_enum, nullable=False),
        sa.Column('status', status_enum, server_default='open', nullable=False),
        sa.Column('ai_summary', sa.String(length=140), nullable=True),
        sa.Column('triaged_by', sa.String(length=50), nullable=False),
        sa.Column('triage_latency_ms', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.CheckConstraint('char_length(text) >= 10', name='chk_text_min_length'),
        sa.CheckConstraint('char_length(location) >= 3', name='chk_location_min_length'),
        sa.PrimaryKeyConstraint('id')
    )

    # 3. Create Indexes
    op.create_index(
        'idx_complaints_status_priority',
        'complaints',
        ['status', 'priority'],
        unique=False
    )
    op.create_index(
        'idx_complaints_created_at',
        'complaints',
        [sa.text('created_at DESC')],
        unique=False
    )


def downgrade() -> None:
    # 1. Drop Indexes
    op.drop_index('idx_complaints_created_at', table_name='complaints')
    op.drop_index('idx_complaints_status_priority', table_name='complaints')

    # 2. Drop Table
    op.drop_table('complaints')

    # 3. Drop Enums
    status_enum = postgresql.ENUM('open', 'in_progress', 'resolved', 'rejected', name='status_enum')
    status_enum.drop(op.get_bind(), checkfirst=True)

    priority_enum = postgresql.ENUM('high', 'normal', 'low', name='priority_enum')
    priority_enum.drop(op.get_bind(), checkfirst=True)

    category_enum = postgresql.ENUM('water', 'electricity', 'sanitation', 'roads', 'streetlights', 'other', name='category_enum')
    category_enum.drop(op.get_bind(), checkfirst=True)
