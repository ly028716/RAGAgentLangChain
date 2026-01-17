"""添加is_admin字段到用户表

Revision ID: 005_is_admin
Revises: 004_user_deletion
Create Date: 2025-01-16

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '005_is_admin'
down_revision = '004_user_deletion'
branch_labels = None
depends_on = None


def upgrade():
    """添加is_admin字段"""
    # 添加is_admin字段，默认为False
    op.add_column('users', sa.Column('is_admin', sa.Boolean(), nullable=False, server_default='0', comment='是否为管理员'))
    
    # 创建索引以提高查询性能
    op.create_index('ix_users_is_admin', 'users', ['is_admin'])


def downgrade():
    """移除is_admin字段"""
    op.drop_index('ix_users_is_admin', table_name='users')
    op.drop_column('users', 'is_admin')
