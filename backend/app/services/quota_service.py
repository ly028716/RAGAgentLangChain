"""
配额服务模块

实现用户配额管理相关业务逻辑，包括配额检查、消耗、更新和重置。
使用Redis原子操作确保并发安全。

需求引用:
    - 需求11.2: 检查用户的剩余配额是否足够
    - 需求11.4: 在每次API调用后扣除相应的token数量
    - 需求11.5: 管理员更新用户配额
    - 需求11.6: 每月1日自动重置所有用户的配额
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional, Tuple
from dateutil.relativedelta import relativedelta
from sqlalchemy.orm import Session

from app.config import settings
from app.core.redis import get_redis_client, RedisKeys
from app.repositories.quota_repository import QuotaRepository, DEFAULT_MONTHLY_QUOTA
from app.models.user_quota import UserQuota
from app.models.api_usage import APIUsage
from app.websocket.connection_manager import connection_manager


class QuotaServiceError(Exception):
    """配额服务异常基类"""
    pass


class QuotaNotFoundError(QuotaServiceError):
    """配额记录不存在异常"""
    pass


class InsufficientQuotaError(QuotaServiceError):
    """配额不足异常"""
    def __init__(self, message: str, remaining: int = 0, required: int = 0):
        super().__init__(message)
        self.remaining = remaining
        self.required = required


class InvalidQuotaValueError(QuotaServiceError):
    """无效配额值异常"""
    pass


class QuotaService:
    """
    配额服务类
    
    提供用户配额管理功能，包括配额检查、消耗、更新和重置。
    使用Redis原子操作确保并发安全。
    
    使用方式:
        service = QuotaService(db)
        quota = service.get_user_quota(user_id=1)
        if service.check_quota(user_id=1, tokens_required=100):
            service.consume_quota(user_id=1, tokens_used=100, api_type="chat")
    """
    
    def __init__(self, db: Session):
        """
        初始化配额服务
        
        Args:
            db: SQLAlchemy数据库会话
        """
        self.db = db
        self.quota_repo = QuotaRepository(db)
        self.default_quota = settings.quota.default_monthly_quota
    
    def get_user_quota(self, user_id: int) -> UserQuota:
        """
        获取用户配额信息
        
        如果用户没有配额记录，自动创建默认配额。
        
        Args:
            user_id: 用户ID
        
        Returns:
            UserQuota: 用户配额对象
        
        需求引用:
            - 需求11.7: 返回当月已使用token数、剩余token数和配额重置日期
        """
        quota = self.quota_repo.get_or_create(
            user_id=user_id,
            monthly_quota=self.default_quota
        )
        return quota
    
    def check_quota(self, user_id: int, tokens_required: int = 0) -> bool:
        """
        检查用户是否有足够的配额
        
        使用Redis缓存加速检查，同时确保数据一致性。
        
        Args:
            user_id: 用户ID
            tokens_required: 需要的token数量（默认为0，仅检查是否有剩余配额）
        
        Returns:
            bool: 配额充足返回True，否则返回False
        
        需求引用:
            - 需求11.2: 检查用户的剩余配额是否足够
        """
        try:
            # 首先尝试从Redis获取配额信息（快速路径）
            redis_client = get_redis_client()
            quota_key = RedisKeys.format_key(RedisKeys.USER_QUOTA, user_id=user_id)
            used_key = RedisKeys.format_key(RedisKeys.USER_QUOTA_USED, user_id=user_id)
            
            # 尝试从Redis获取
            monthly_quota = redis_client.get(quota_key)
            used_quota = redis_client.get(used_key)
            
            if monthly_quota is not None and used_quota is not None:
                remaining = int(monthly_quota) - int(used_quota)
                return remaining >= tokens_required
        except Exception:
            # Redis不可用时，回退到数据库
            pass
        
        # 从数据库获取配额
        quota = self.get_user_quota(user_id)
        
        # 同步到Redis缓存
        self._sync_quota_to_redis(user_id, quota)
        
        return quota.has_sufficient_quota(tokens_required)
    
    def consume_quota(
        self,
        user_id: int,
        tokens_used: int,
        api_type: str = "chat",
        cost: Decimal = Decimal("0.0000")
    ) -> Tuple[UserQuota, APIUsage]:
        """
        消耗用户配额（扣除token）
        
        使用Redis原子操作确保并发安全，同时记录API使用情况。
        
        Args:
            user_id: 用户ID
            tokens_used: 消耗的token数量
            api_type: API类型（chat/rag/agent等）
            cost: 调用费用（可选）
        
        Returns:
            Tuple[UserQuota, APIUsage]: (更新后的配额对象, API使用记录)
        
        Raises:
            InsufficientQuotaError: 配额不足
        
        需求引用:
            - 需求11.4: 在每次API调用后扣除相应的token数量
            - 需求8.1: 记录用户ID、API类型、token消耗和时间戳
        """
        # 获取当前配额
        quota = self.get_user_quota(user_id)
        
        # 检查配额是否充足
        if not quota.has_sufficient_quota(tokens_used):
            raise InsufficientQuotaError(
                f"配额不足，剩余 {quota.remaining_quota} tokens，需要 {tokens_used} tokens",
                remaining=quota.remaining_quota,
                required=tokens_used
            )
        
        # 使用Redis原子操作扣除配额
        try:
            redis_client = get_redis_client()
            used_key = RedisKeys.format_key(RedisKeys.USER_QUOTA_USED, user_id=user_id)
            
            # 原子递增
            new_used = redis_client.incrby(used_key, tokens_used)
            
            # 设置过期时间（到下个月1日）
            next_reset = self._get_next_reset_date()
            ttl = int((datetime.combine(next_reset, datetime.min.time()) - datetime.now()).total_seconds())
            if ttl > 0:
                redis_client.expire(used_key, ttl)
        except Exception:
            # Redis不可用时，仅使用数据库
            pass
        
        # 更新数据库中的配额
        quota = self.quota_repo.consume_quota(user_id, tokens_used)
        
        # 检查配额警告阈值（剩余10%时发送警告）
        usage_percentage = quota.usage_percentage
        if usage_percentage >= 90 and usage_percentage < 95:
            # 发送低配额警告
            try:
                import asyncio
                asyncio.create_task(connection_manager.send_personal_message(user_id, {
                    "type": "quota_warning",
                    "data": {
                        "level": "low",
                        "remaining_quota": quota.remaining_quota,
                        "usage_percentage": usage_percentage,
                        "message": f"配额即将用尽，剩余 {quota.remaining_quota} tokens ({100-usage_percentage:.1f}%)",
                        "timestamp": datetime.utcnow().isoformat()
                    }
                }))
            except Exception as e:
                # WebSocket通知失败不影响主流程
                pass
        elif usage_percentage >= 95:
            # 发送严重警告
            try:
                import asyncio
                asyncio.create_task(connection_manager.send_personal_message(user_id, {
                    "type": "quota_warning",
                    "data": {
                        "level": "critical",
                        "remaining_quota": quota.remaining_quota,
                        "usage_percentage": usage_percentage,
                        "message": f"配额严重不足，剩余 {quota.remaining_quota} tokens ({100-usage_percentage:.1f}%)",
                        "timestamp": datetime.utcnow().isoformat()
                    }
                }))
            except Exception as e:
                # WebSocket通知失败不影响主流程
                pass
        
        # 记录API使用情况
        api_usage = APIUsage(
            user_id=user_id,
            api_type=api_type,
            tokens_used=tokens_used,
            cost=cost
        )
        self.db.add(api_usage)
        self.db.commit()
        self.db.refresh(api_usage)
        
        return quota, api_usage
    
    def update_quota(
        self,
        user_id: int,
        new_quota: int
    ) -> UserQuota:
        """
        更新用户的月度配额上限（管理员功能）
        
        Args:
            user_id: 用户ID
            new_quota: 新的月度配额上限
        
        Returns:
            UserQuota: 更新后的配额对象
        
        Raises:
            InvalidQuotaValueError: 配额值无效
            QuotaNotFoundError: 用户配额记录不存在
        
        需求引用:
            - 需求11.5: 管理员更新用户配额
        """
        # 验证配额值
        if new_quota < 0:
            raise InvalidQuotaValueError("配额值不能为负数")
        
        if new_quota < 1000:
            raise InvalidQuotaValueError("配额值不能小于1000")
        
        # 确保用户有配额记录
        quota = self.get_user_quota(user_id)
        
        # 更新配额
        quota = self.quota_repo.update_monthly_quota(user_id, new_quota)
        
        if not quota:
            raise QuotaNotFoundError(f"用户 {user_id} 的配额记录不存在")
        
        # 同步到Redis
        self._sync_quota_to_redis(user_id, quota)
        
        return quota
    
    def reset_monthly_quota(self, user_id: int) -> UserQuota:
        """
        重置用户的月度配额
        
        将已使用配额清零，更新重置日期到下个月1日。
        
        Args:
            user_id: 用户ID
        
        Returns:
            UserQuota: 重置后的配额对象
        
        Raises:
            QuotaNotFoundError: 用户配额记录不存在
        """
        quota = self.quota_repo.reset_quota(user_id)
        
        if not quota:
            raise QuotaNotFoundError(f"用户 {user_id} 的配额记录不存在")
        
        # 清除Redis缓存
        self._clear_quota_from_redis(user_id)
        
        # 同步新配额到Redis
        self._sync_quota_to_redis(user_id, quota)
        
        return quota
    
    def reset_all_quotas(self) -> int:
        """
        重置所有过期的用户配额
        
        用于定时任务，在每月1日执行。
        
        Returns:
            int: 重置的配额数量
        
        需求引用:
            - 需求11.6: 每月1日自动重置所有用户的配额
        """
        count = self.quota_repo.reset_all_expired_quotas()
        
        # 清除所有Redis配额缓存
        # 注意：这里简化处理，实际生产环境可能需要更精细的缓存管理
        try:
            redis_client = get_redis_client()
            # 使用SCAN命令查找所有配额相关的键
            cursor = 0
            while True:
                cursor, keys = redis_client.scan(cursor, match="quota:*", count=100)
                if keys:
                    redis_client.delete(*keys)
                if cursor == 0:
                    break
        except Exception:
            # Redis不可用时忽略
            pass
        
        return count
    
    def get_quota_info(self, user_id: int) -> dict:
        """
        获取用户配额详细信息
        
        返回格式化的配额信息，包括使用百分比和重置日期。
        
        Args:
            user_id: 用户ID
        
        Returns:
            dict: 配额信息字典
        
        需求引用:
            - 需求11.7: 返回当月已使用token数、剩余token数和配额重置日期
        """
        quota = self.get_user_quota(user_id)
        
        return {
            "monthly_quota": quota.monthly_quota,
            "used_quota": quota.used_quota,
            "remaining_quota": quota.remaining_quota,
            "reset_date": quota.reset_date.isoformat(),
            "usage_percentage": quota.usage_percentage
        }
    
    def _sync_quota_to_redis(self, user_id: int, quota: UserQuota) -> None:
        """
        同步配额信息到Redis缓存
        
        Args:
            user_id: 用户ID
            quota: 配额对象
        """
        try:
            redis_client = get_redis_client()
            quota_key = RedisKeys.format_key(RedisKeys.USER_QUOTA, user_id=user_id)
            used_key = RedisKeys.format_key(RedisKeys.USER_QUOTA_USED, user_id=user_id)
            
            # 计算到下个月1日的TTL
            next_reset = self._get_next_reset_date()
            ttl = int((datetime.combine(next_reset, datetime.min.time()) - datetime.now()).total_seconds())
            
            if ttl > 0:
                redis_client.setex(quota_key, ttl, str(quota.monthly_quota))
                redis_client.setex(used_key, ttl, str(quota.used_quota))
        except Exception:
            # Redis不可用时忽略
            pass
    
    def _clear_quota_from_redis(self, user_id: int) -> None:
        """
        清除Redis中的配额缓存
        
        Args:
            user_id: 用户ID
        """
        try:
            redis_client = get_redis_client()
            quota_key = RedisKeys.format_key(RedisKeys.USER_QUOTA, user_id=user_id)
            used_key = RedisKeys.format_key(RedisKeys.USER_QUOTA_USED, user_id=user_id)
            
            redis_client.delete(quota_key, used_key)
        except Exception:
            # Redis不可用时忽略
            pass
    
    def _get_next_reset_date(self) -> date:
        """
        获取下一个配额重置日期（下个月1日）
        
        Returns:
            date: 下个月1日的日期
        """
        today = date.today()
        next_month = today + relativedelta(months=1)
        return date(next_month.year, next_month.month, 1)


# 导出
__all__ = [
    'QuotaService',
    'QuotaServiceError',
    'QuotaNotFoundError',
    'InsufficientQuotaError',
    'InvalidQuotaValueError',
]
