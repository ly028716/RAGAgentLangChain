"""修复消息角色枚举大小写不一致

Revision ID: 006_fix_message_role_enum
Revises: 005_is_admin
Create Date: 2026-01-19

"""

from alembic import op


revision = "006_fix_message_role_enum"
down_revision = "005_is_admin"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    dialect = bind.dialect.name

    if dialect == "mysql":
        op.execute("UPDATE messages SET role='user' WHERE role='USER'")
        op.execute("UPDATE messages SET role='assistant' WHERE role='ASSISTANT'")
        op.execute("UPDATE messages SET role='system' WHERE role='SYSTEM'")
        op.execute(
            "ALTER TABLE messages MODIFY role "
            "ENUM('user','assistant','system') NOT NULL COMMENT '消息角色'"
        )
        return

    if dialect == "postgresql":
        for old, new in (("USER", "user"), ("ASSISTANT", "assistant"), ("SYSTEM", "system")):
            try:
                op.execute(f"ALTER TYPE messagerole RENAME VALUE '{old}' TO '{new}'")
            except Exception:
                pass
        return


def downgrade():
    bind = op.get_bind()
    dialect = bind.dialect.name

    if dialect == "mysql":
        op.execute("UPDATE messages SET role='USER' WHERE role='user'")
        op.execute("UPDATE messages SET role='ASSISTANT' WHERE role='assistant'")
        op.execute("UPDATE messages SET role='SYSTEM' WHERE role='system'")
        op.execute(
            "ALTER TABLE messages MODIFY role "
            "ENUM('USER','ASSISTANT','SYSTEM') NOT NULL COMMENT '消息角色'"
        )
        return

    if dialect == "postgresql":
        for old, new in (("user", "USER"), ("assistant", "ASSISTANT"), ("system", "SYSTEM")):
            try:
                op.execute(f"ALTER TYPE messagerole RENAME VALUE '{old}' TO '{new}'")
            except Exception:
                pass

