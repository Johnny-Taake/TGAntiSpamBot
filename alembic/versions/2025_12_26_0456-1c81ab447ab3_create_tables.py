"""create tables

Revision ID: 1c81ab447ab3
Revises:
Create Date: 2025-12-26 04:56:47.026774

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision: str = '1c81ab447ab3'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('chats',
    sa.Column('telegram_chat_id', sa.BigInteger(), nullable=False),
    sa.Column('title', sa.String(length=255), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('chat_link', sa.String(length=512), nullable=True),
    sa.Column('enable_ai_check', sa.Boolean(), nullable=False),
    sa.Column('cleanup_mentions', sa.Boolean(), nullable=False),
    sa.Column('cleanup_emojis', sa.Boolean(), nullable=False),
    sa.Column('cleanup_links', sa.Boolean(), nullable=False),
    sa.Column('allowed_link_domains', sqlite.JSON(), nullable=False),
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_chats')),
    sqlite_autoincrement=True
    )
    op.create_index(op.f('ix_chats_telegram_chat_id'), 'chats', ['telegram_chat_id'], unique=True)
    op.create_table('user_states',
    sa.Column('chat_id', sa.Integer(), nullable=False),
    sa.Column('telegram_user_id', sa.BigInteger(), nullable=False),
    sa.Column('joined_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('valid_messages', sa.Integer(), nullable=False),
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.ForeignKeyConstraint(['chat_id'], ['chats.id'], name=op.f('fk_user_states_chat_id_chats'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_user_states')),
    sa.UniqueConstraint('chat_id', 'telegram_user_id', name='uq_user_state_chat_user')
    )
    op.create_index(op.f('ix_user_states_chat_id'), 'user_states', ['chat_id'], unique=False)
    op.create_index(op.f('ix_user_states_telegram_user_id'), 'user_states', ['telegram_user_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_user_states_telegram_user_id'), table_name='user_states')
    op.drop_index(op.f('ix_user_states_chat_id'), table_name='user_states')
    op.drop_table('user_states')
    op.drop_index(op.f('ix_chats_telegram_chat_id'), table_name='chats')
    op.drop_table('chats')
