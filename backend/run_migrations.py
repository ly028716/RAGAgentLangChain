#!/usr/bin/env python
"""运行数据库迁移的脚本"""
from alembic.config import Config
from alembic import command

def run_migrations():
    """运行 alembic 数据库迁移"""
    alembic_cfg = Config("alembic.ini")
    command.upgrade(alembic_cfg, "head")
    print("数据库迁移完成!")

if __name__ == "__main__":
    run_migrations()
