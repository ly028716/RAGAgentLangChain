"""
认证服务模块

实现用户注册、登录、密码修改等认证相关业务逻辑。
需求: 需求1.1, 需求1.2, 需求1.4, 需求1.7
"""

import logging
from datetime import datetime
from typing import Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.config import settings
from app.core.security import (
    hash_password,
    verify_password,
    create_token_pair,
    verify_refresh_token,
    add_token_to_blacklist,
)
from app.core.redis import get_redis_client, RedisKeys
from app.repositories.user_repository import UserRepository
from app.models.user import User
from app.models.login_attempt import LoginAttempt

logger = logging.getLogger(__name__)


class AuthServiceError(Exception):
    """认证服务异常基类"""
    pass


class UserAlreadyExistsError(AuthServiceError):
    """用户已存在异常"""
    pass


class InvalidCredentialsError(AuthServiceError):
    """凭证无效异常"""
    pass


class AccountLockedError(AuthServiceError):
    """账户已锁定异常"""
    def __init__(self, message: str, remaining_minutes: int = 0):
        super().__init__(message)
        self.remaining_minutes = remaining_minutes


class UserNotFoundError(AuthServiceError):
    """用户不存在异常"""
    pass


class PasswordMismatchError(AuthServiceError):
    """密码不匹配异常"""
    pass


class AuthService:
    """
    认证服务类
    
    提供用户注册、登录、密码修改等认证功能。
    
    使用方式:
        auth_service = AuthService(db)
        user = auth_service.register("username", "password123", "email@example.com")
        tokens = auth_service.login("username", "password123", "127.0.0.1")
    """
    
    def __init__(self, db: Session):
        """
        初始化认证服务
        
        Args:
            db: SQLAlchemy数据库会话
        """
        self.db = db
        self.user_repo = UserRepository(db)
        self.max_login_attempts = settings.security.max_login_attempts
        self.lockout_minutes = settings.security.account_lockout_minutes
    
    def register(
        self,
        username: str,
        password: str,
        email: Optional[str] = None
    ) -> User:
        """
        用户注册
        
        创建新用户账户，包含用户名唯一性检查和密码加密。
        
        Args:
            username: 用户名（必须唯一）
            password: 明文密码（至少8位，包含字母和数字）
            email: 邮箱地址（可选，必须唯一）
        
        Returns:
            User: 创建的用户对象
        
        Raises:
            UserAlreadyExistsError: 用户名或邮箱已存在
        
        需求引用:
            - 需求1.1: 用户名唯一且密码强度符合要求时创建新用户账户
        """
        # 检查用户名是否已存在
        if self.user_repo.username_exists(username):
            raise UserAlreadyExistsError(f"用户名 '{username}' 已存在")
        
        # 检查邮箱是否已存在
        if email and self.user_repo.email_exists(email):
            raise UserAlreadyExistsError(f"邮箱 '{email}' 已被注册")
        
        # 加密密码
        password_hash = hash_password(password)
        
        # 创建用户
        try:
            user = self.user_repo.create(
                username=username,
                password_hash=password_hash,
                email=email
            )
            return user
        except IntegrityError:
            self.db.rollback()
            raise UserAlreadyExistsError("用户名或邮箱已存在")
    
    def login(
        self,
        username: str,
        password: str,
        ip_address: str = "0.0.0.0"
    ) -> dict:
        """
        用户登录
        
        验证用户凭证，生成JWT令牌，记录登录尝试。
        
        Args:
            username: 用户名
            password: 明文密码
            ip_address: 登录请求的IP地址
        
        Returns:
            dict: 包含access_token, refresh_token, token_type, expires_in的字典
        
        Raises:
            AccountLockedError: 账户已被锁定
            InvalidCredentialsError: 用户名或密码错误
        
        需求引用:
            - 需求1.2: 凭证正确时生成JWT令牌
            - 需求1.5: 记录每次登录的时间戳
            - 需求1.7: 连续5次登录失败后锁定账户15分钟
        """
        # 检查账户是否被锁定
        is_locked, remaining_minutes = self._check_account_locked(username)
        if is_locked:
            raise AccountLockedError(
                f"账户已被锁定，请在 {remaining_minutes} 分钟后重试",
                remaining_minutes=remaining_minutes
            )
        
        # 获取用户
        user = self.user_repo.get_by_username(username)
        
        # 验证用户存在且密码正确
        if not user or not verify_password(password, user.password_hash):
            # 记录登录失败
            self._record_login_attempt(username, ip_address, success=False)
            self._increment_failed_attempts(username)
            raise InvalidCredentialsError("用户名或密码错误")
        
        # 检查用户是否激活
        if not user.is_active:
            self._record_login_attempt(username, ip_address, success=False)
            raise InvalidCredentialsError("账户已被禁用")
        
        # 登录成功，清除失败计数
        self._clear_failed_attempts(username)
        
        # 记录登录成功
        self._record_login_attempt(username, ip_address, success=True)
        
        # 更新最后登录时间
        self.user_repo.update_last_login(user.id)
        
        # 生成令牌对
        tokens = create_token_pair(user.id, user.username)
        
        return tokens
    
    def refresh_token(self, refresh_token: str) -> dict:
        """
        刷新访问令牌
        
        使用刷新令牌获取新的访问令牌。
        
        Args:
            refresh_token: 刷新令牌
        
        Returns:
            dict: 包含新的access_token, refresh_token, token_type, expires_in的字典
        
        Raises:
            InvalidCredentialsError: 刷新令牌无效或已过期
        """
        # 验证刷新令牌
        payload = verify_refresh_token(refresh_token)
        if not payload:
            raise InvalidCredentialsError("刷新令牌无效或已过期")
        
        user_id = int(payload["sub"])
        username = payload["username"]
        
        # 验证用户是否存在且激活
        user = self.user_repo.get_by_id(user_id)
        if not user or not user.is_active:
            raise InvalidCredentialsError("用户不存在或已被禁用")
        
        # 将旧的刷新令牌加入黑名单
        add_token_to_blacklist(refresh_token)
        
        # 生成新的令牌对
        tokens = create_token_pair(user.id, user.username)
        
        return tokens
    
    def change_password(
        self,
        user_id: int,
        old_password: str,
        new_password: str
    ) -> bool:
        """
        修改密码
        
        验证旧密码后更新为新密码。
        
        Args:
            user_id: 用户ID
            old_password: 旧密码
            new_password: 新密码
        
        Returns:
            bool: 密码修改是否成功
        
        Raises:
            UserNotFoundError: 用户不存在
            PasswordMismatchError: 旧密码不正确
        
        需求引用:
            - 需求1.4: 提供正确的旧密码时使用bcrypt加密新密码并更新
        """
        # 获取用户
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise UserNotFoundError("用户不存在")
        
        # 验证旧密码
        if not verify_password(old_password, user.password_hash):
            raise PasswordMismatchError("旧密码不正确")
        
        # 加密新密码
        new_password_hash = hash_password(new_password)
        
        # 更新密码
        self.user_repo.update(user_id, password_hash=new_password_hash)
        
        return True
    
    def logout(self, access_token: str, refresh_token: Optional[str] = None) -> bool:
        """
        用户登出
        
        将令牌加入黑名单，使其失效。
        
        Args:
            access_token: 访问令牌
            refresh_token: 刷新令牌（可选）
        
        Returns:
            bool: 登出是否成功
        """
        # 将访问令牌加入黑名单
        add_token_to_blacklist(access_token)
        
        # 如果提供了刷新令牌，也加入黑名单
        if refresh_token:
            add_token_to_blacklist(refresh_token)
        
        return True
    
    def _check_account_locked(self, username: str) -> Tuple[bool, int]:
        """
        检查账户是否被锁定
        
        Args:
            username: 用户名
        
        Returns:
            Tuple[bool, int]: (是否锁定, 剩余锁定分钟数)
        """
        try:
            redis_client = get_redis_client()
            lock_key = RedisKeys.format_key(
                RedisKeys.ACCOUNT_LOCKED,
                username=username
            )
            
            ttl = redis_client.ttl(lock_key)
            if ttl > 0:
                remaining_minutes = (ttl + 59) // 60  # 向上取整
                return True, remaining_minutes
            
            return False, 0
        except Exception as e:
            logger.error(f"检查账户锁定状态失败: {e}")
            return False, 0
    
    def _increment_failed_attempts(self, username: str) -> int:
        """
        增加登录失败次数
        
        如果达到最大失败次数，锁定账户。
        
        Args:
            username: 用户名
        
        Returns:
            int: 当前失败次数
        """
        try:
            redis_client = get_redis_client()
            attempts_key = RedisKeys.format_key(
                RedisKeys.LOGIN_ATTEMPTS,
                username=username
            )
            
            # 增加失败次数
            attempts = redis_client.incr(attempts_key)
            
            # 设置过期时间（锁定时长）
            redis_client.expire(attempts_key, self.lockout_minutes * 60)
            
            # 检查是否需要锁定账户
            if attempts >= self.max_login_attempts:
                self._lock_account(username)
            
            return attempts
        except Exception as e:
            logger.error(f"增加登录失败次数失败: {e}")
            return 0
    
    def _clear_failed_attempts(self, username: str) -> None:
        """
        清除登录失败次数
        
        Args:
            username: 用户名
        """
        try:
            redis_client = get_redis_client()
            attempts_key = RedisKeys.format_key(
                RedisKeys.LOGIN_ATTEMPTS,
                username=username
            )
            redis_client.delete(attempts_key)
        except Exception as e:
            logger.error(f"清除登录失败次数失败: {e}")
    
    def _lock_account(self, username: str) -> None:
        """
        锁定账户
        
        Args:
            username: 用户名
        """
        try:
            redis_client = get_redis_client()
            lock_key = RedisKeys.format_key(
                RedisKeys.ACCOUNT_LOCKED,
                username=username
            )
            
            # 设置锁定标记，过期时间为锁定时长
            redis_client.setex(
                lock_key,
                self.lockout_minutes * 60,
                "1"
            )
        except Exception as e:
            logger.error(f"锁定账户失败: {e}")
    
    def _record_login_attempt(
        self,
        username: str,
        ip_address: str,
        success: bool
    ) -> None:
        """
        记录登录尝试到数据库
        
        Args:
            username: 用户名
            ip_address: IP地址
            success: 是否成功
        """
        try:
            login_attempt = LoginAttempt(
                username=username,
                ip_address=ip_address,
                success=success
            )
            self.db.add(login_attempt)
            self.db.commit()
        except Exception as e:
            logger.error(f"记录登录尝试失败: {e}")
            self.db.rollback()
    
    def get_failed_attempts(self, username: str) -> int:
        """
        获取当前登录失败次数
        
        Args:
            username: 用户名
        
        Returns:
            int: 当前失败次数
        """
        try:
            redis_client = get_redis_client()
            attempts_key = RedisKeys.format_key(
                RedisKeys.LOGIN_ATTEMPTS,
                username=username
            )
            
            attempts = redis_client.get(attempts_key)
            return int(attempts) if attempts else 0
        except Exception as e:
            logger.error(f"获取登录失败次数失败: {e}")
            return 0
    
    def unlock_account(self, username: str) -> bool:
        """
        解锁账户（管理员功能）
        
        Args:
            username: 用户名
        
        Returns:
            bool: 解锁是否成功
        """
        try:
            redis_client = get_redis_client()
            
            # 删除锁定标记
            lock_key = RedisKeys.format_key(
                RedisKeys.ACCOUNT_LOCKED,
                username=username
            )
            redis_client.delete(lock_key)
            
            # 清除失败次数
            self._clear_failed_attempts(username)

            return True
        except Exception as e:
            logger.error(f"解锁账户失败: {e}")
            return False


# 导出
__all__ = [
    'AuthService',
    'AuthServiceError',
    'UserAlreadyExistsError',
    'InvalidCredentialsError',
    'AccountLockedError',
    'UserNotFoundError',
    'PasswordMismatchError',
]
