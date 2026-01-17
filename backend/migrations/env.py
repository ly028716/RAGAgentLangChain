"""
Alembic环境配置文件

配置数据库迁移环境，包括数据库连接、模型元数据和迁移选项。
"""

import sys
from logging.config import fileConfig
from pathlib import Path

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# 将backend目录添加到Python路径
# 这样可以导入app模块
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

# 导入配置和模型
from app.config import settings
from app.core.database import Base

# 导入所有模型，确保它们被注册到Base.metadata
from app.models import (
    User,
    Conversation,
    Message,
    KnowledgeBase,
    Document,
    AgentTool,
    AgentExecution,
    UserQuota,
    APIUsage,
    LoginAttempt,
)

# Alembic配置对象
config = context.config

# 设置数据库URL
# 从应用配置中读取，而不是从alembic.ini
config.set_main_option("sqlalchemy.url", settings.database.database_url)

# 配置日志
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# 设置目标元数据
# 这是所有模型的元数据，用于自动生成迁移
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """
    离线模式运行迁移
    
    在离线模式下，只生成SQL语句而不实际执行。
    适用于需要审查SQL或在没有数据库连接的环境中生成迁移脚本。
    
    使用方式:
        alembic upgrade head --sql
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        # 比较类型变化
        compare_type=True,
        # 比较服务器默认值
        compare_server_default=True,
        # 包含对象名称
        include_object=include_object,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """
    在线模式运行迁移
    
    在在线模式下，创建数据库连接并实际执行迁移。
    这是默认的迁移模式。
    
    使用方式:
        alembic upgrade head
    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            # 比较类型变化
            compare_type=True,
            # 比较服务器默认值
            compare_server_default=True,
            # 包含对象名称
            include_object=include_object,
        )

        with context.begin_transaction():
            context.run_migrations()


def include_object(object, name, type_, reflected, compare_to):
    """
    过滤要包含在迁移中的对象
    
    可以用于排除某些表或对象不参与迁移。
    
    Args:
        object: 数据库对象
        name: 对象名称
        type_: 对象类型（table, column, index等）
        reflected: 是否是反射的对象
        compare_to: 比较目标
    
    Returns:
        bool: 是否包含该对象
    """
    # 排除alembic版本表
    if type_ == "table" and name == "alembic_version":
        return False
    
    return True


# 根据运行模式选择迁移方式
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
