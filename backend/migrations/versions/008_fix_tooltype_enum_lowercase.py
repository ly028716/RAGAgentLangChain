"""fix tooltype enum to lowercase

Revision ID: 008_fix_tooltype_enum_lowercase
Revises: 007_fix_tooltype_enum
Create Date: 2026-01-27 21:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '008_fix_tooltype_enum_lowercase'
down_revision = '007_fix_tooltype_enum'
branch_labels = None
depends_on = None


def upgrade():
    """
    修复 agent_tools 表的 tool_type 枚举类型
    将枚举值从大写 ENUM('BUILTIN', 'CUSTOM') 改为小写 ENUM('builtin', 'custom')
    """
    # 修改枚举类型定义
    op.execute("""
        ALTER TABLE agent_tools
        MODIFY COLUMN tool_type ENUM('builtin', 'custom') NOT NULL
        COMMENT '工具类型：builtin-内置工具，custom-自定义工具'
    """)


def downgrade():
    """
    回滚：将枚举类型改回大写
    """
    op.execute("""
        ALTER TABLE agent_tools
        MODIFY COLUMN tool_type ENUM('BUILTIN', 'CUSTOM') NOT NULL
        COMMENT '工具类型：BUILTIN-内置工具，CUSTOM-自定义工具'
    """)
