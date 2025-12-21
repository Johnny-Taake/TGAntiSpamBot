"""upd chats table

Revision ID: 84426b4e2ad6
Revises: de4519ac09d0
Create Date: 2025-12-21 06:42:21.531492

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '84426b4e2ad6'
down_revision: Union[str, Sequence[str], None] = 'de4519ac09d0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('chats', sa.Column('enable_ai_check', sa.Boolean(), nullable=False))
    op.add_column('chats', sa.Column('cleanup_mentions', sa.Boolean(), nullable=True))
    op.add_column('chats', sa.Column('cleanup_links', sa.Boolean(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('chats', 'cleanup_links')
    op.drop_column('chats', 'cleanup_mentions')
    op.drop_column('chats', 'enable_ai_check')
