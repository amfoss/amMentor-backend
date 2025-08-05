"""remove submitted_late

Revision ID: 8f84ff4de4af
Revises: 12599f674ee9
Create Date: 2025-07-30 06:27:06.564253

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8f84ff4de4af'
down_revision: Union[str, None] = '12599f674ee9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.drop_column('submissions', 'submitted_late')


def downgrade() -> None:
    """Downgrade schema."""
    op.add_column('your_table_name', sa.Column('submitted_late', sa.Boolean(), default=False))
