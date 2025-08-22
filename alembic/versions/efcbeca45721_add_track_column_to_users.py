"""add: track column to users

Revision ID: efcbeca45721
Revises: 40774b92ab4a
Create Date: 2025-08-15 03:41:47.298109

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'efcbeca45721'
down_revision: Union[str, None] = '40774b92ab4a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('users', sa.Column('track', sa.Integer(), nullable=False ))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('users', 'track')
    
