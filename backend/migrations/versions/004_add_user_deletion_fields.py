"""添加用户注销相关字段

Revision ID: 004_user_deletion
Revises: 003_prompts_permissions
Create Date: 2026-01-12
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '004_user_deletion'
down_revision = '003_prompts_permissions'
branch_labels = None
depends_on = None


def upgrade():
    """添加用户注销相关字段"""
    # 添加注销请求时间字段
    op.add_column(
        'users',
        sa.Column('deletion_requested_at', sa.DateTime(), nullable=True, comment='注销请求时间')
    )
    
    # 添加计划删除时间字段
    op.add_column(
        'users',
        sa.Column('deletion_scheduled_at', sa.DateTime(), nullable=True, comment='计划删除时间')
    )
    
    # 添加注销原因字段
    op.add_column(
        'users',
        sa.Column('deletion_reason', sa.Text(), nullable=True, comment='注销原因')
    )
    
    # 创建索引以便快速查询待删除的用户
    op.create_index(
        'idx_users_deletion_scheduled',
        'users',
        ['deletion_scheduled_at'],
        unique=False
    )


def downgrade():
    """移除用户注销相关字段"""
    # 删除索引
    op.drop_index('idx_users_deletion_scheduled', table_name='users')
    
    # 删除字段
    op.drop_column('users', 'deletion_reason')
    op.drop_column('users', 'deletion_scheduled_at')
    op.drop_column('users', 'deletion_requested_at')
