"""
数据库连接和ORM配置模块

配置SQLAlchemy引擎、会话管理和Base模型类。
实现数据库连接池和依赖注入函数。
"""

from typing import Generator

from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import QueuePool

from app.config import settings

# 创建SQLAlchemy引擎
# 配置连接池：pool_size=10（常驻连接数），max_overflow=20（最大溢出连接数）
# pool_pre_ping=True：每次从池中获取连接时先测试连接是否有效
# pool_recycle：连接回收时间，防止MySQL连接超时
engine = create_engine(
    settings.database.database_url,
    poolclass=QueuePool,
    pool_size=settings.database.db_pool_size,
    max_overflow=settings.database.db_max_overflow,
    pool_pre_ping=True,
    pool_recycle=settings.database.db_pool_recycle,
    echo=settings.app.debug,  # 调试模式下打印SQL语句
)


# 配置会话工厂
# autocommit=False：不自动提交事务
# autoflush=False：不自动刷新
# bind：绑定到引擎
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# 创建Base模型类
# 所有ORM模型都应该继承这个Base类
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """
    数据库会话依赖函数

    用于FastAPI的依赖注入，自动管理数据库会话的生命周期。
    在请求结束时自动关闭会话。

    使用方式:
        @app.get("/users")
        def get_users(db: Session = Depends(get_db)):
            users = db.query(User).all()
            return users

    Yields:
        Session: SQLAlchemy数据库会话
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """
    初始化数据库

    创建所有表（如果不存在）。
    注意：生产环境应该使用Alembic进行数据库迁移。
    """
    # 导入所有模型，确保它们被注册到Base.metadata
    # 这里需要在实际使用时导入所有模型类
    # from app.models import user, conversation, message, knowledge_base, document, agent_tool, agent_execution, api_usage, user_quota, login_attempt

    Base.metadata.create_all(bind=engine)


def close_db() -> None:
    """
    关闭数据库连接

    在应用关闭时调用，清理所有数据库连接。
    """
    engine.dispose()


# 数据库连接事件监听器
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_conn, connection_record):
    """
    SQLite特定配置

    如果使用SQLite，启用外键约束。
    """
    if "sqlite" in settings.database.database_url:
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


@event.listens_for(engine, "checkout")
def receive_checkout(dbapi_connection, connection_record, connection_proxy):
    """
    连接检出事件

    可用于记录连接池状态或执行连接级别的配置。
    """
    pass


# 导出
__all__ = [
    "engine",
    "SessionLocal",
    "Base",
    "get_db",
    "init_db",
    "close_db",
]
