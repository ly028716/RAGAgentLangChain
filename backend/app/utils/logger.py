"""
日志配置模块

该模块提供统一的日志配置功能，支持：
- 文件日志（RotatingFileHandler）
- 控制台日志
- 日志格式化
- 日志级别配置
- 日志文件轮转（10MB，10个备份）

使用方式:
    from app.utils.logger import setup_logging, get_logger
    
    # 在应用启动时配置日志
    setup_logging()
    
    # 在模块中获取logger
    logger = get_logger(__name__)
    logger.info("这是一条日志消息")
"""

import logging
import os
from logging.handlers import RotatingFileHandler
from typing import Optional

from app.config import settings


def setup_logging(
    log_level: Optional[str] = None,
    log_file: Optional[str] = None,
    log_max_bytes: Optional[int] = None,
    log_backup_count: Optional[int] = None,
) -> logging.Logger:
    """
    配置应用程序的日志系统

    该函数配置根日志记录器，设置文件处理器和控制台处理器。
    文件处理器使用RotatingFileHandler实现日志文件轮转。

    Args:
        log_level: 日志级别（DEBUG, INFO, WARNING, ERROR, CRITICAL）
                  如果为None，则使用配置文件中的值
        log_file: 日志文件路径，如果为None，则使用配置文件中的值
        log_max_bytes: 日志文件最大大小（字节），如果为None，则使用配置文件中的值
        log_backup_count: 日志备份文件数量，如果为None，则使用配置文件中的值

    Returns:
        logging.Logger: 配置好的根日志记录器

    Example:
        >>> setup_logging()
        >>> logger = logging.getLogger(__name__)
        >>> logger.info("应用程序已启动")
    """
    # 使用配置文件中的值或传入的参数
    level = log_level or settings.logging.log_level
    file_path = log_file or settings.logging.log_file
    max_bytes = log_max_bytes or settings.logging.log_max_bytes
    backup_count = log_backup_count or settings.logging.log_backup_count

    # 确保日志目录存在
    log_dir = os.path.dirname(file_path)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)

    # 获取根日志记录器
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper()))

    # 清除现有的处理器（避免重复配置）
    root_logger.handlers.clear()

    # 创建日志格式器
    # 格式: 时间 - 日志记录器名称 - 日志级别 - 消息
    # 示例: 2025-01-09 10:30:45,123 - app.services.auth_service - INFO - 用户登录成功
    formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # 创建详细格式器（用于文件日志，包含更多信息）
    detailed_formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(funcName)s() - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # 配置文件处理器（RotatingFileHandler）
    # 当日志文件达到max_bytes大小时，自动轮转
    # 保留backup_count个备份文件
    try:
        file_handler = RotatingFileHandler(
            filename=file_path,
            maxBytes=max_bytes,  # 默认10MB
            backupCount=backup_count,  # 默认10个备份
            encoding="utf-8",
        )
        file_handler.setLevel(getattr(logging, level.upper()))
        file_handler.setFormatter(detailed_formatter)
        root_logger.addHandler(file_handler)
    except Exception as e:
        # 如果文件处理器创建失败，记录错误但不中断应用启动
        print(f"警告: 无法创建日志文件处理器: {e}")

    # 配置控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, level.upper()))
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # 记录日志系统初始化信息
    root_logger.info("=" * 80)
    root_logger.info("日志系统初始化完成")
    root_logger.info(f"日志级别: {level}")
    root_logger.info(f"日志文件: {file_path}")
    root_logger.info(f"日志文件最大大小: {max_bytes / 1024 / 1024:.2f}MB")
    root_logger.info(f"日志备份数量: {backup_count}")
    root_logger.info("=" * 80)

    return root_logger


def get_logger(name: str) -> logging.Logger:
    """
    获取指定名称的日志记录器

    这是一个便捷函数，用于在各个模块中获取日志记录器。
    建议在每个模块的顶部使用 logger = get_logger(__name__)

    Args:
        name: 日志记录器名称，通常使用 __name__

    Returns:
        logging.Logger: 日志记录器实例

    Example:
        >>> logger = get_logger(__name__)
        >>> logger.info("这是一条信息日志")
        >>> logger.error("这是一条错误日志")
        >>> logger.debug("这是一条调试日志")
    """
    return logging.getLogger(name)


def configure_module_logger(
    module_name: str, level: Optional[str] = None, propagate: bool = True
) -> logging.Logger:
    """
    为特定模块配置独立的日志记录器

    该函数允许为特定模块设置不同的日志级别，
    而不影响其他模块的日志配置。

    Args:
        module_name: 模块名称
        level: 日志级别，如果为None则使用根日志记录器的级别
        propagate: 是否将日志传播到父记录器

    Returns:
        logging.Logger: 配置好的模块日志记录器

    Example:
        >>> # 为langchain模块设置DEBUG级别
        >>> langchain_logger = configure_module_logger('langchain', level='DEBUG')
        >>>
        >>> # 为sqlalchemy设置WARNING级别（减少SQL日志）
        >>> db_logger = configure_module_logger('sqlalchemy.engine', level='WARNING')
    """
    logger = logging.getLogger(module_name)

    if level:
        logger.setLevel(getattr(logging, level.upper()))

    logger.propagate = propagate

    return logger


def set_third_party_log_levels():
    """
    配置第三方库的日志级别

    该函数用于减少第三方库的日志输出，避免日志文件被大量无关信息填充。
    通常在应用启动时调用一次。

    Example:
        >>> setup_logging()
        >>> set_third_party_log_levels()
    """
    # 减少SQLAlchemy的日志输出
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.pool").setLevel(logging.WARNING)

    # 减少httpx的日志输出
    logging.getLogger("httpx").setLevel(logging.WARNING)

    # 减少uvicorn的访问日志（保留错误日志）
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)

    # 减少websocket的日志输出
    logging.getLogger("websockets").setLevel(logging.WARNING)

    # LangChain日志配置
    logging.getLogger("langchain").setLevel(logging.INFO)

    # Redis日志配置
    logging.getLogger("redis").setLevel(logging.WARNING)

    # APScheduler日志配置
    logging.getLogger("apscheduler").setLevel(logging.INFO)


# 日志级别常量（便于使用）
DEBUG = logging.DEBUG
INFO = logging.INFO
WARNING = logging.WARNING
ERROR = logging.ERROR
CRITICAL = logging.CRITICAL


__all__ = [
    "setup_logging",
    "get_logger",
    "configure_module_logger",
    "set_third_party_log_levels",
    "DEBUG",
    "INFO",
    "WARNING",
    "ERROR",
    "CRITICAL",
]
