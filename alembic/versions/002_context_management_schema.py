"""
Context management schema.

Revision ID: 002
Revises: 001
Create Date: 2023-07-15 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create context_priority enum type
    op.execute(
        "CREATE TYPE contextpriority AS ENUM ('low', 'medium', 'high', 'critical')"
    )
    
    # Create context_type enum type
    op.execute(
        "CREATE TYPE contexttype AS ENUM ('message', 'summary', 'user_preference', 'system', 'metadata')"
    )
    
    # Create context_window table
    op.create_table(
        'contextwindow',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('conversation_id', sa.Integer(), nullable=False),
        sa.Column('max_tokens', sa.Integer(), nullable=False, default=4000),
        sa.Column('current_tokens', sa.Integer(), nullable=False, default=0),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['conversation_id'], ['conversation.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_contextwindow_id'), 'contextwindow', ['id'], unique=False)
    
    # Create context_item table
    op.create_table(
        'contextitem',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('context_window_id', sa.Integer(), nullable=False),
        sa.Column('message_id', sa.Integer(), nullable=True),
        sa.Column('content', sa.Text(), nullable=True),
        sa.Column('context_type', sa.Enum('message', 'summary', 'user_preference', 'system', 'metadata', name='contexttype'), nullable=False),
        sa.Column('token_count', sa.Integer(), nullable=False, default=0),
        sa.Column('priority', sa.Enum('low', 'medium', 'high', 'critical', name='contextpriority'), nullable=False, default='medium'),
        sa.Column('relevance_score', sa.Float(), nullable=False, default=1.0),
        sa.Column('position', sa.Integer(), nullable=False, default=0),
        sa.Column('is_included', sa.Boolean(), nullable=False, default=True),
        sa.Column('meta_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['context_window_id'], ['contextwindow.id'], ),
        sa.ForeignKeyConstraint(['message_id'], ['message.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_contextitem_id'), 'contextitem', ['id'], unique=False)
    
    # Create context_tag table
    op.create_table(
        'contexttag',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('context_item_id', sa.Integer(), nullable=False),
        sa.Column('tag_key', sa.String(100), nullable=False),
        sa.Column('tag_value', sa.String(255), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['context_item_id'], ['contextitem.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('context_item_id', 'tag_key', name='uix_context_tag')
    )
    op.create_index(op.f('ix_contexttag_id'), 'contexttag', ['id'], unique=False)
    
    # Create context_summary table
    op.create_table(
        'contextsummary',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('conversation_id', sa.Integer(), nullable=False),
        sa.Column('start_message_id', sa.Integer(), nullable=True),
        sa.Column('end_message_id', sa.Integer(), nullable=True),
        sa.Column('summary_content', sa.Text(), nullable=False),
        sa.Column('token_count', sa.Integer(), nullable=False, default=0),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('meta_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['conversation_id'], ['conversation.id'], ),
        sa.ForeignKeyConstraint(['start_message_id'], ['message.id'], ),
        sa.ForeignKeyConstraint(['end_message_id'], ['message.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_contextsummary_id'), 'contextsummary', ['id'], unique=False)
    
    # Create user_preference table
    op.create_table(
        'userpreference',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('preference_key', sa.String(100), nullable=False),
        sa.Column('preference_value', sa.String(255), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=False, default=1.0),
        sa.Column('source_message_id', sa.Integer(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
        sa.ForeignKeyConstraint(['source_message_id'], ['message.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'preference_key', name='uix_user_preference')
    )
    op.create_index(op.f('ix_userpreference_id'), 'userpreference', ['id'], unique=False)


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_index(op.f('ix_userpreference_id'), table_name='userpreference')
    op.drop_table('userpreference')
    
    op.drop_index(op.f('ix_contextsummary_id'), table_name='contextsummary')
    op.drop_table('contextsummary')
    
    op.drop_index(op.f('ix_contexttag_id'), table_name='contexttag')
    op.drop_table('contexttag')
    
    op.drop_index(op.f('ix_contextitem_id'), table_name='contextitem')
    op.drop_table('contextitem')
    
    op.drop_index(op.f('ix_contextwindow_id'), table_name='contextwindow')
    op.drop_table('contextwindow')
    
    # Drop enum types
    op.execute('DROP TYPE IF EXISTS contexttype')
    op.execute('DROP TYPE IF EXISTS contextpriority')
