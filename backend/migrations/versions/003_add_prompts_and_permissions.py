"""添加系统提示词表和知识库权限表

创建系统提示词表和知识库权限表，扩展用户表和知识库表。

Revision ID: 003_prompts_permissions
Revises: 002_verification
Create Date: 2026-01-11
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '003_prompts_permissions'
down_revision: Union[str, None] = '002_verification'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """升级数据库"""
    
    # 创建system_prompts表
    op.create_table(
        'system_prompts',
        sa.Column('id', sa.Integer(), nullable=False, comment='提示词ID'),
        sa.Column('user_id', sa.Integer(), nullable=True, comment='用户ID'),
        sa.Column('name', sa.String(100), nullable=False, comment='提示词名称'),
        sa.Column('content', sa.Text(), nullable=False, comment='提示词内容'),
        sa.Column('category', sa.String(50), nullable=True, default='general', comment='分类: general/professional/creative'),
        sa.Column('is_default', sa.Boolean(), nullable=False, default=False, comment='是否为默认提示词'),
        sa.Column('is_system', sa.Boolean(), nullable=False, default=False, comment='是否为系统内置'),
        sa.Column('created_at', sa.DateTime(), nullable=False, comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), nullable=False, comment='更新时间'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        comment='系统提示词表'
    )
    op.create_index('ix_system_prompts_id', 'system_prompts', ['id'], unique=False)
    op.create_index('ix_system_prompts_user_id', 'system_prompts', ['user_id'], unique=False)
    op.create_index('idx_sp_user_default', 'system_prompts', ['user_id', 'is_default'], unique=False)
    op.create_index('idx_sp_category', 'system_prompts', ['category'], unique=False)
    
    # 创建knowledge_base_permissions表
    op.create_table(
        'knowledge_base_permissions',
        sa.Column('id', sa.Integer(), nullable=False, comment='权限ID'),
        sa.Column('knowledge_base_id', sa.Integer(), nullable=False, comment='知识库ID'),
        sa.Column('user_id', sa.Integer(), nullable=True, comment='用户ID'),
        sa.Column('permission_type', sa.String(20), nullable=False, default='viewer', comment='权限类型: owner/editor/viewer'),
        sa.Column('is_public', sa.Boolean(), nullable=False, default=False, comment='是否公开'),
        sa.Column('created_at', sa.DateTime(), nullable=False, comment='创建时间'),
        sa.ForeignKeyConstraint(['knowledge_base_id'], ['knowledge_bases.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('knowledge_base_id', 'user_id', name='uq_kb_user_permission'),
        comment='知识库权限表'
    )
    op.create_index('ix_knowledge_base_permissions_id', 'knowledge_base_permissions', ['id'], unique=False)
    op.create_index('idx_kbp_kb_user', 'knowledge_base_permissions', ['knowledge_base_id', 'user_id'], unique=False)
    
    # 扩展knowledge_bases表 - 添加visibility字段
    op.add_column('knowledge_bases', sa.Column('visibility', sa.String(20), nullable=True, default='private', comment='可见性: private/shared/public'))
    
    # 扩展conversations表 - 添加system_prompt_id字段
    op.add_column('conversations', sa.Column('system_prompt_id', sa.Integer(), nullable=True, comment='系统提示词ID'))
    op.create_foreign_key('fk_conv_prompt', 'conversations', 'system_prompts', ['system_prompt_id'], ['id'])


def downgrade() -> None:
    """降级数据库"""
    
    # 删除conversations表的外键和字段
    op.drop_constraint('fk_conv_prompt', 'conversations', type_='foreignkey')
    op.drop_column('conversations', 'system_prompt_id')
    
    # 删除knowledge_bases表的字段
    op.drop_column('knowledge_bases', 'visibility')
    
    # 删除knowledge_base_permissions表
    op.drop_index('idx_kbp_kb_user', table_name='knowledge_base_permissions')
    op.drop_index('ix_knowledge_base_permissions_id', table_name='knowledge_base_permissions')
    op.drop_table('knowledge_base_permissions')
    
    # 删除system_prompts表
    op.drop_index('idx_sp_category', table_name='system_prompts')
    op.drop_index('idx_sp_user_default', table_name='system_prompts')
    op.drop_index('ix_system_prompts_user_id', table_name='system_prompts')
    op.drop_index('ix_system_prompts_id', table_name='system_prompts')
    op.drop_table('system_prompts')
