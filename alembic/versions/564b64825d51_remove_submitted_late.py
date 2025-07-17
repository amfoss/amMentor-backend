"""remove submitted_late

Revision ID: 564b64825d51
Revises: eb395efd59b7
Create Date: 2025-07-15 10:31:44.975046

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '564b64825d51'
down_revision: Union[str, None] = 'eb395efd59b7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
