"""
清理定时任务模块

实现系统数据清理功能，包括清理旧登录记录、临时文件和处理账号注销。
使用APScheduler配置定时任务，在每天凌晨执行。

需求引用:
    - 需求8.5: 清理旧登录记录任务
"""

import logging
import os
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List

from sqlalchemy.orm import Session
from sqlalchemy import delete

from app.core.database import SessionLocal
from app.models.login_attempt import LoginAttempt
from app.models.user import User
from app.config import settings


# 配置日志
logger = logging.getLogger(__name__)


def cleanup_old_login_attempts(days_to_keep: int = 30) -> dict:
    """
    清理旧的登录尝试记录
    
    删除超过指定天数的登录尝试记录，以保持数据库整洁。
    默认保留最近30天的记录。
    
    Args:
        days_to_keep: 保留的天数，默认30天
    
    Returns:
        dict: 包含执行结果的字典
            - success: 是否成功
            - deleted_count: 删除的记录数量
            - cutoff_date: 截止日期
            - message: 执行消息
            - timestamp: 执行时间
    
    需求引用:
        - 需求8.5: 清理旧登录记录任务
        - 需求1.7: 记录登录尝试用于账户锁定机制
    
    使用方式:
        # 清理30天前的记录（默认）
        result = cleanup_old_login_attempts()
        
        # 清理90天前的记录
        result = cleanup_old_login_attempts(days_to_keep=90)
        
        # 由APScheduler自动调用
        scheduler.add_job(
            cleanup_old_login_attempts,
            trigger='cron',
            hour=2,
            minute=0
        )
    """
    db: Optional[Session] = None
    start_time = datetime.utcnow()
    
    try:
        logger.info(f"开始清理 {days_to_keep} 天前的登录尝试记录")
        
        # 计算截止日期
        cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
        
        # 创建数据库会话
        db = SessionLocal()
        
        # 删除旧记录
        stmt = delete(LoginAttempt).where(LoginAttempt.created_at < cutoff_date)
        result = db.execute(stmt)
        deleted_count = result.rowcount
        
        # 提交事务
        db.commit()
        
        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()
        
        logger.info(
            f"登录记录清理任务完成: 删除了 {deleted_count} 条记录, "
            f"截止日期 {cutoff_date.isoformat()}, "
            f"耗时 {duration:.2f} 秒"
        )
        
        return {
            "success": True,
            "deleted_count": deleted_count,
            "cutoff_date": cutoff_date.isoformat(),
            "days_kept": days_to_keep,
            "message": f"成功删除 {deleted_count} 条旧登录记录",
            "timestamp": end_time.isoformat(),
            "duration_seconds": duration
        }
        
    except Exception as e:
        logger.error(f"登录记录清理任务失败: {str(e)}", exc_info=True)
        
        # 回滚事务
        if db:
            db.rollback()
        
        return {
            "success": False,
            "deleted_count": 0,
            "message": f"清理失败: {str(e)}",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e)
        }
        
    finally:
        # 关闭数据库会话
        if db:
            db.close()


def cleanup_temp_files(temp_dir: Optional[str] = None, days_to_keep: int = 7) -> dict:
    """
    清理临时文件
    
    删除超过指定天数的临时文件，释放磁盘空间。
    默认清理上传目录中的临时文件。
    
    Args:
        temp_dir: 临时文件目录，默认使用配置中的上传目录
        days_to_keep: 保留的天数，默认7天
    
    Returns:
        dict: 包含执行结果的字典
            - success: 是否成功
            - deleted_files: 删除的文件数量
            - deleted_size_mb: 删除的文件总大小（MB）
            - cutoff_date: 截止日期
            - message: 执行消息
            - timestamp: 执行时间
    
    使用方式:
        # 清理默认临时目录中7天前的文件
        result = cleanup_temp_files()
        
        # 清理指定目录中的文件
        result = cleanup_temp_files(temp_dir="/path/to/temp", days_to_keep=3)
        
        # 由APScheduler自动调用
        scheduler.add_job(
            cleanup_temp_files,
            trigger='cron',
            hour=3,
            minute=0
        )
    """
    start_time = datetime.utcnow()
    
    try:
        # 使用默认上传目录
        if temp_dir is None:
            temp_dir = settings.file_storage.upload_dir
        
        temp_path = Path(temp_dir)
        
        # 检查目录是否存在
        if not temp_path.exists():
            logger.warning(f"临时文件目录不存在: {temp_dir}")
            return {
                "success": True,
                "deleted_files": 0,
                "deleted_size_mb": 0.0,
                "message": f"目录不存在: {temp_dir}",
                "timestamp": datetime.utcnow().isoformat()
            }
        
        logger.info(f"开始清理 {days_to_keep} 天前的临时文件: {temp_dir}")
        
        # 计算截止日期
        cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
        cutoff_timestamp = cutoff_date.timestamp()
        
        deleted_files = 0
        deleted_size = 0
        temp_files: List[Path] = []
        
        # 查找需要删除的文件
        # 只清理临时文件（以.tmp结尾或在temp子目录中）
        temp_subdirs = ['temp', 'tmp', 'cache']
        
        for subdir in temp_subdirs:
            subdir_path = temp_path / subdir
            if subdir_path.exists() and subdir_path.is_dir():
                for file_path in subdir_path.rglob('*'):
                    if file_path.is_file():
                        # 检查文件修改时间
                        if file_path.stat().st_mtime < cutoff_timestamp:
                            temp_files.append(file_path)
        
        # 同时查找根目录下的.tmp文件
        for file_path in temp_path.glob('*.tmp'):
            if file_path.is_file():
                if file_path.stat().st_mtime < cutoff_timestamp:
                    temp_files.append(file_path)
        
        # 删除文件
        for file_path in temp_files:
            try:
                file_size = file_path.stat().st_size
                file_path.unlink()
                deleted_files += 1
                deleted_size += file_size
                logger.debug(f"删除临时文件: {file_path}")
            except Exception as e:
                logger.warning(f"删除文件失败 {file_path}: {str(e)}")
        
        # 清理空目录
        for subdir in temp_subdirs:
            subdir_path = temp_path / subdir
            if subdir_path.exists() and subdir_path.is_dir():
                try:
                    # 删除空子目录
                    for dir_path in sorted(subdir_path.rglob('*'), reverse=True):
                        if dir_path.is_dir() and not any(dir_path.iterdir()):
                            dir_path.rmdir()
                            logger.debug(f"删除空目录: {dir_path}")
                except Exception as e:
                    logger.warning(f"清理空目录失败: {str(e)}")
        
        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()
        deleted_size_mb = deleted_size / (1024 * 1024)
        
        logger.info(
            f"临时文件清理任务完成: 删除了 {deleted_files} 个文件, "
            f"释放 {deleted_size_mb:.2f} MB, "
            f"截止日期 {cutoff_date.isoformat()}, "
            f"耗时 {duration:.2f} 秒"
        )
        
        return {
            "success": True,
            "deleted_files": deleted_files,
            "deleted_size_mb": round(deleted_size_mb, 2),
            "cutoff_date": cutoff_date.isoformat(),
            "days_kept": days_to_keep,
            "temp_dir": str(temp_dir),
            "message": f"成功删除 {deleted_files} 个临时文件，释放 {deleted_size_mb:.2f} MB",
            "timestamp": end_time.isoformat(),
            "duration_seconds": duration
        }
        
    except Exception as e:
        logger.error(f"临时文件清理任务失败: {str(e)}", exc_info=True)
        
        return {
            "success": False,
            "deleted_files": 0,
            "deleted_size_mb": 0.0,
            "message": f"清理失败: {str(e)}",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e)
        }


def cleanup_old_api_usage(days_to_keep: int = 90) -> dict:
    """
    清理旧的API使用记录
    
    删除超过指定天数的API使用记录，保留最近的统计数据。
    默认保留最近90天的记录。
    
    Args:
        days_to_keep: 保留的天数，默认90天
    
    Returns:
        dict: 包含执行结果的字典
            - success: 是否成功
            - deleted_count: 删除的记录数量
            - cutoff_date: 截止日期
            - message: 执行消息
            - timestamp: 执行时间
    
    使用方式:
        # 清理90天前的记录（默认）
        result = cleanup_old_api_usage()
        
        # 清理180天前的记录
        result = cleanup_old_api_usage(days_to_keep=180)
    """
    db: Optional[Session] = None
    start_time = datetime.utcnow()
    
    try:
        logger.info(f"开始清理 {days_to_keep} 天前的API使用记录")
        
        # 计算截止日期
        cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
        
        # 创建数据库会话
        db = SessionLocal()
        
        # 导入APIUsage模型
        from app.models.api_usage import APIUsage
        
        # 删除旧记录
        stmt = delete(APIUsage).where(APIUsage.created_at < cutoff_date)
        result = db.execute(stmt)
        deleted_count = result.rowcount
        
        # 提交事务
        db.commit()
        
        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()
        
        logger.info(
            f"API使用记录清理任务完成: 删除了 {deleted_count} 条记录, "
            f"截止日期 {cutoff_date.isoformat()}, "
            f"耗时 {duration:.2f} 秒"
        )
        
        return {
            "success": True,
            "deleted_count": deleted_count,
            "cutoff_date": cutoff_date.isoformat(),
            "days_kept": days_to_keep,
            "message": f"成功删除 {deleted_count} 条旧API使用记录",
            "timestamp": end_time.isoformat(),
            "duration_seconds": duration
        }
        
    except Exception as e:
        logger.error(f"API使用记录清理任务失败: {str(e)}", exc_info=True)
        
        # 回滚事务
        if db:
            db.rollback()
        
        return {
            "success": False,
            "deleted_count": 0,
            "message": f"清理失败: {str(e)}",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e)
        }
        
    finally:
        # 关闭数据库会话
        if db:
            db.close()


def run_all_cleanup_tasks() -> dict:
    """
    运行所有清理任务
    
    依次执行所有清理任务，并汇总结果。
    
    Returns:
        dict: 包含所有任务执行结果的字典
    
    使用方式:
        # 手动运行所有清理任务
        result = run_all_cleanup_tasks()
        
        # 由APScheduler自动调用
        scheduler.add_job(
            run_all_cleanup_tasks,
            trigger='cron',
            hour=2,
            minute=0
        )
    """
    start_time = datetime.utcnow()
    
    logger.info("开始执行所有清理任务")
    
    results = {
        "start_time": start_time.isoformat(),
        "tasks": {}
    }
    
    # 清理登录记录
    try:
        login_result = cleanup_old_login_attempts(days_to_keep=30)
        results["tasks"]["login_attempts"] = login_result
    except Exception as e:
        logger.error(f"清理登录记录失败: {str(e)}")
        results["tasks"]["login_attempts"] = {
            "success": False,
            "error": str(e)
        }
    
    # 清理临时文件
    try:
        temp_result = cleanup_temp_files(days_to_keep=7)
        results["tasks"]["temp_files"] = temp_result
    except Exception as e:
        logger.error(f"清理临时文件失败: {str(e)}")
        results["tasks"]["temp_files"] = {
            "success": False,
            "error": str(e)
        }
    
    # 清理API使用记录
    try:
        api_result = cleanup_old_api_usage(days_to_keep=90)
        results["tasks"]["api_usage"] = api_result
    except Exception as e:
        logger.error(f"清理API使用记录失败: {str(e)}")
        results["tasks"]["api_usage"] = {
            "success": False,
            "error": str(e)
        }
    
    # 处理账号删除请求
    try:
        deletion_result = process_account_deletions()
        results["tasks"]["account_deletions"] = deletion_result
    except Exception as e:
        logger.error(f"处理账号删除请求失败: {str(e)}")
        results["tasks"]["account_deletions"] = {
            "success": False,
            "error": str(e)
        }
    
    end_time = datetime.utcnow()
    duration = (end_time - start_time).total_seconds()
    
    # 统计成功的任务数
    success_count = sum(1 for task in results["tasks"].values() if task.get("success", False))
    total_count = len(results["tasks"])
    
    results["end_time"] = end_time.isoformat()
    results["duration_seconds"] = duration
    results["success_count"] = success_count
    results["total_count"] = total_count
    results["all_success"] = success_count == total_count
    
    logger.info(
        f"所有清理任务完成: {success_count}/{total_count} 成功, "
        f"耗时 {duration:.2f} 秒"
    )
    
    return results


def process_account_deletions() -> dict:
    """
    处理到期的账号删除请求
    
    查找所有已过冷静期的注销请求，执行账号删除。
    
    Returns:
        dict: 包含执行结果的字典
            - success: 是否成功
            - processed_count: 处理的账号数量
            - deleted_count: 成功删除的账号数量
            - failed_count: 删除失败的账号数量
            - message: 执行消息
            - timestamp: 执行时间
    
    使用方式:
        # 手动执行
        result = process_account_deletions()
        
        # 由APScheduler自动调用
        scheduler.add_job(
            process_account_deletions,
            trigger='cron',
            hour=3,
            minute=0
        )
    """
    db: Optional[Session] = None
    start_time = datetime.utcnow()
    
    try:
        logger.info("开始处理到期的账号删除请求")
        
        # 创建数据库会话
        db = SessionLocal()
        
        # 查找所有已过冷静期的注销请求
        now = datetime.utcnow()
        users_to_delete = db.query(User).filter(
            User.deletion_scheduled_at.isnot(None),
            User.deletion_scheduled_at <= now
        ).all()
        
        processed_count = len(users_to_delete)
        deleted_count = 0
        failed_count = 0
        failed_users = []
        
        if processed_count == 0:
            logger.info("没有需要处理的账号删除请求")
            return {
                "success": True,
                "processed_count": 0,
                "deleted_count": 0,
                "failed_count": 0,
                "message": "没有需要处理的账号删除请求",
                "timestamp": datetime.utcnow().isoformat()
            }
        
        # 导入UserService
        from app.services.user_service import UserService
        
        for user in users_to_delete:
            try:
                user_service = UserService(db)
                result = user_service.execute_deletion(user.id)
                
                if result.get("success"):
                    deleted_count += 1
                    logger.info(f"成功删除用户 {user.username} (ID: {user.id})")
                else:
                    failed_count += 1
                    failed_users.append({
                        "user_id": user.id,
                        "username": user.username,
                        "error": result.get("message")
                    })
                    logger.error(f"删除用户 {user.username} (ID: {user.id}) 失败: {result.get('message')}")
                    
            except Exception as e:
                failed_count += 1
                failed_users.append({
                    "user_id": user.id,
                    "username": user.username,
                    "error": str(e)
                })
                logger.error(f"删除用户 {user.username} (ID: {user.id}) 时发生异常: {e}")
        
        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()
        
        logger.info(
            f"账号删除任务完成: 处理 {processed_count} 个请求, "
            f"成功 {deleted_count} 个, 失败 {failed_count} 个, "
            f"耗时 {duration:.2f} 秒"
        )
        
        return {
            "success": failed_count == 0,
            "processed_count": processed_count,
            "deleted_count": deleted_count,
            "failed_count": failed_count,
            "failed_users": failed_users if failed_users else None,
            "message": f"处理了 {processed_count} 个账号删除请求，成功 {deleted_count} 个，失败 {failed_count} 个",
            "timestamp": end_time.isoformat(),
            "duration_seconds": duration
        }
        
    except Exception as e:
        logger.error(f"账号删除任务失败: {str(e)}", exc_info=True)
        
        return {
            "success": False,
            "processed_count": 0,
            "deleted_count": 0,
            "failed_count": 0,
            "message": f"任务执行失败: {str(e)}",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e)
        }
        
    finally:
        # 关闭数据库会话
        if db:
            db.close()


# 导出
__all__ = [
    'cleanup_old_login_attempts',
    'cleanup_temp_files',
    'cleanup_old_api_usage',
    'run_all_cleanup_tasks',
    'process_account_deletions',
]
