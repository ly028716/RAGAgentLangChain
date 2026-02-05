"""修复工具类型枚举大小写不一致

Revision ID: 007_fix_tooltype_enum
Revises: 006_fix_message_role_enum
Create Date: 2026-01-23

"""

from alembic import op


revision = "007_fix_tooltype_enum"
down_revision = "006_fix_message_role_enum"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    dialect = bind.dialect.name

    if dialect == "mysql":
        # 更新现有数据：将大写转换为小写
        op.execute("UPDATE agent_tools SET tool_type='builtin' WHERE tool_type='BUILTIN'")
        op.execute("UPDATE agent_tools SET tool_type='custom' WHERE tool_type='CUSTOM'")

        # 修改枚举定义为小写
        op.execute(
            "ALTER TABLE agent_tools MODIFY tool_type "
            "ENUM('builtin','custom') NOT NULL DEFAULT 'builtin' COMMENT '工具类型（builtin/custom）'"
        )
        return

    if dialect == "postgresql":
        # PostgreSQL: 重命名枚举值
        for old, new in (("BUILTIN", "builtin"), ("CUSTOM", "custom")):
            try:
                op.execute(f"ALTER TYPE tooltype RENAME VALUE '{old}' TO '{new}'")
            except Exception:
                # 如果值已经是小写，忽略错误
                pass
        return


def downgrade():
    bind = op.get_bind()
    dialect = bind.dialect.name

    if dialect == "mysql":
        # 回滚：将小写转换为大写
        op.execute("UPDATE agent_tools SET tool_type='BUILTIN' WHERE tool_type='builtin'")
        op.execute("UPDATE agent_tools SET tool_type='CUSTOM' WHERE tool_type='custom'")

        # 修改枚举定义为大写
        op.execute(
            "ALTER TABLE agent_tools MODIFY tool_type "
            "ENUM('BUILTIN','CUSTOM') NOT NULL DEFAULT 'BUILTIN' COMMENT '工具类型（builtin/custom）'"
        )
        return

    if dialect == "postgresql":
        # PostgreSQL: 重命名枚举值回大写
        for old, new in (("builtin", "BUILTIN"), ("custom", "CUSTOM")):
            try:
                op.execute(f"ALTER TYPE tooltype RENAME VALUE '{old}' TO '{new}'")
            except Exception:
                pass
