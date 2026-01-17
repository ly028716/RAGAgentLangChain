"""添加验证码表

创建验证码表用于存储邮箱和短信验证码。

Revision ID: 002_verification
Revises: 001_initial
Create Date: 2026-01-11
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '002_verification'
down_revision: Union[str, None] = '001_initial'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """升级数据库 - 创建验证码表"""
    
    # 创建verification_codes表
    op.create_table(
        'verification_codes',
        sa.Column('id', sa.Integer(), nullable=False, comment='验证码ID'),
        sa.Column('target', sa.String(100), nullable=False, comment='目标(邮箱/手机号)'),
        sa.Column('code', sa.String(6), nullable=False, comment='验证码'),
        sa.Column('code_type', sa.String(20), nullable=False, comment='类型: register/reset_password/bind_email'),
        sa.Column('channel', sa.String(10), nullable=False, comment='渠道: email/sms'),
        sa.Column('expires_at', sa.DateTime(), nullable=False, comment='过期时间'),
        sa.Column('is_used', sa.Boolean(), nullable=False, default=False, comment='是否已使用'),
        sa.Column('attempts', sa.Integer(), nullable=False, default=0, comment='验证尝试次数'),
        sa.Column('created_at', sa.DateTime(), nullable=False, comment='创建时间'),
        sa.PrimaryKeyConstraint('id'),
        comment='验证码表'
    )
    op.create_index('ix_verification_codes_id', 'verification_codes', ['id'], unique=False)
    op.create_index('ix_verification_codes_target', 'verification_codes', ['target'], unique=False)
    op.create_index('idx_vc_target_type', 'verification_codes', ['target', 'code_type'], unique=False)
    op.create_index('idx_vc_expires', 'verification_codes', ['expires_at'], unique=False)


def downgrade() -> None:
    """降级数据库 - 删除验证码表"""
    
    op.drop_index('idx_vc_expires', table_name='verification_codes')
    op.drop_index('idx_vc_target_type', table_name='verification_codes')
    op.drop_index('ix_verification_codes_target', table_name='verification_codes')
    op.drop_index('ix_verification_codes_id', table_name='verification_codes')
    op.drop_table('verification_codes')
