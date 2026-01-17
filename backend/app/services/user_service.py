"""
用户服务模块

实现用户账号管理相关业务逻辑，包括账号注销功能。
"""

import logging
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.orm import Session

from app.core.security import verify_password
from app.repositories.user_repository import UserRepository
from app.models.user import User
from app.services.file_service import file_service

logger = logging.getLogger(__name__)


class UserServiceError(Exception):
    """用户服务异常基类"""
    pass


class UserNotFoundError(UserServiceError):
    """用户不存在异常"""
    pass


class PasswordMismatchError(UserServiceError):
    """密码不匹配异常"""
    pass


class DeletionAlreadyRequestedError(UserServiceError):
    """已请求注销异常"""
    pass


class NoDeletionRequestError(UserServiceError):
    """无注销请求异常"""
    pass


class DeletionCooldownExpiredError(UserServiceError):
    """冷静期已过异常"""
    pass


class UserService:
    """
    用户服务类
    
    提供用户账号管理功能，包括账号注销。
    """
    
    # 冷静期天数
    DELETION_COOLDOWN_DAYS = 7
    
    def __init__(self, db: Session):
        """
        初始化用户服务
        
        Args:
            db: SQLAlchemy数据库会话
        """
        self.db = db
        self.user_repo = UserRepository(db)
    
    def request_deletion(
        self,
        user_id: int,
        password: str,
        reason: Optional[str] = None
    ) -> dict:
        """
        请求账号注销
        
        流程:
        1. 验证用户密码
        2. 设置 deletion_requested_at 和 deletion_scheduled_at
        3. 返回计划删除时间
        
        Args:
            user_id: 用户ID
            password: 用户密码（用于验证身份）
            reason: 注销原因（可选）
        
        Returns:
            dict: 包含注销请求信息的字典
        
        Raises:
            UserNotFoundError: 用户不存在
            PasswordMismatchError: 密码不正确
            DeletionAlreadyRequestedError: 已经请求过注销
        """
        # 获取用户
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise UserNotFoundError("用户不存在")
        
        # 先验证密码（安全性：避免通过不同错误消息泄露用户状态）
        if not verify_password(password, user.password_hash):
            raise PasswordMismatchError("密码不正确")
        
        # 检查是否已经请求过注销
        if user.deletion_requested_at is not None:
            raise DeletionAlreadyRequestedError(
                f"您已于 {user.deletion_requested_at.strftime('%Y-%m-%d %H:%M')} 请求注销账号，"
                f"计划于 {user.deletion_scheduled_at.strftime('%Y-%m-%d %H:%M')} 执行删除"
            )
        
        # 设置注销时间
        now = datetime.utcnow()
        scheduled_at = now + timedelta(days=self.DELETION_COOLDOWN_DAYS)
        
        user.deletion_requested_at = now
        user.deletion_scheduled_at = scheduled_at
        user.deletion_reason = reason
        
        self.db.commit()
        self.db.refresh(user)
        
        logger.info(f"用户 {user.username} (ID: {user_id}) 请求注销账号，计划于 {scheduled_at} 执行")
        
        return {
            "success": True,
            "message": "账号注销请求已提交",
            "requested_at": now.isoformat(),
            "scheduled_at": scheduled_at.isoformat(),
            "cooldown_days": self.DELETION_COOLDOWN_DAYS
        }
    
    def cancel_deletion(self, user_id: int) -> dict:
        """
        取消注销请求（冷静期内）
        
        Args:
            user_id: 用户ID
        
        Returns:
            dict: 包含取消结果的字典
        
        Raises:
            UserNotFoundError: 用户不存在
            NoDeletionRequestError: 没有注销请求
            DeletionCooldownExpiredError: 冷静期已过，无法取消
        """
        # 获取用户
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise UserNotFoundError("用户不存在")
        
        # 检查是否有注销请求
        if user.deletion_requested_at is None:
            raise NoDeletionRequestError("您没有待处理的注销请求")
        
        # 检查是否在冷静期内
        now = datetime.utcnow()
        if user.deletion_scheduled_at and now >= user.deletion_scheduled_at:
            raise DeletionCooldownExpiredError("冷静期已过，无法取消注销请求")
        
        # 清除注销请求
        user.deletion_requested_at = None
        user.deletion_scheduled_at = None
        user.deletion_reason = None
        
        self.db.commit()
        self.db.refresh(user)
        
        logger.info(f"用户 {user.username} (ID: {user_id}) 取消了注销请求")
        
        return {
            "success": True,
            "message": "注销请求已取消，您的账号将保持正常状态"
        }
    
    def get_deletion_status(self, user_id: int) -> dict:
        """
        查询注销状态
        
        Args:
            user_id: 用户ID
        
        Returns:
            dict: 包含注销状态的字典
        
        Raises:
            UserNotFoundError: 用户不存在
        """
        # 获取用户
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise UserNotFoundError("用户不存在")
        
        if user.deletion_requested_at is None:
            return {
                "has_deletion_request": False,
                "message": "您的账号状态正常，没有待处理的注销请求"
            }
        
        now = datetime.utcnow()
        remaining_time = user.deletion_scheduled_at - now if user.deletion_scheduled_at else timedelta(0)
        remaining_days = max(0, remaining_time.days)
        remaining_hours = max(0, remaining_time.seconds // 3600)
        
        can_cancel = user.deletion_scheduled_at and now < user.deletion_scheduled_at
        
        return {
            "has_deletion_request": True,
            "requested_at": user.deletion_requested_at.isoformat(),
            "scheduled_at": user.deletion_scheduled_at.isoformat() if user.deletion_scheduled_at else None,
            "reason": user.deletion_reason,
            "remaining_days": remaining_days,
            "remaining_hours": remaining_hours,
            "can_cancel": can_cancel,
            "message": f"您的账号将于 {remaining_days} 天 {remaining_hours} 小时后被删除" if can_cancel else "冷静期已过，账号即将被删除"
        }
    
    def execute_deletion(self, user_id: int) -> dict:
        """
        执行账号删除（定时任务调用）
        
        清理顺序:
        1. 删除用户头像文件
        2. 删除用户记录（级联删除关联的对话、知识库、配额等）
        
        注意: 向量数据库中的文档向量会在知识库删除时通过级联触发清理，
        如果需要显式清理，应在 KnowledgeBase 模型的删除事件中处理。
        
        Args:
            user_id: 用户ID
        
        Returns:
            dict: 包含删除结果的字典
        """
        user = self.user_repo.get_by_id(user_id)
        if not user:
            return {
                "success": False,
                "message": "用户不存在"
            }
        
        username = user.username
        
        try:
            # 删除用户头像文件
            try:
                file_service.delete_avatar(user_id)
            except Exception as e:
                logger.warning(f"删除用户 {user_id} 头像失败: {e}")
            
            # 删除用户记录（级联删除关联数据）
            # 由于User模型设置了cascade="all, delete-orphan"，
            # 删除用户时会自动删除关联的conversations, knowledge_bases, quota
            self.user_repo.delete(user_id)
            
            logger.info(f"用户 {username} (ID: {user_id}) 的账号已被删除")
            
            return {
                "success": True,
                "message": f"用户 {username} 的账号已被成功删除",
                "deleted_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"删除用户 {user_id} 失败: {e}")
            self.db.rollback()
            return {
                "success": False,
                "message": f"删除失败: {str(e)}"
            }


# 导出
__all__ = [
    'UserService',
    'UserServiceError',
    'UserNotFoundError',
    'PasswordMismatchError',
    'DeletionAlreadyRequestedError',
    'NoDeletionRequestError',
    'DeletionCooldownExpiredError',
]
