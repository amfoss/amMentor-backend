"""alembic sanity check

Revision ID: 4ba7992b5758
Revises: 79c306503d60
Create Date: 2026-01-23 22:10:30.972604

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4ba7992b5758'
down_revision: Union[str, None] = '79c306503d60'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
