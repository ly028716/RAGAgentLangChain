"""
配额数据访问层（Repository）

封装用户配额相关的数据库操作，提供统一的数据访问接口。
实现配额查询、更新、重置操作。

需求引用:
    - 需求11.1: 为每个用户设置默认的月度token配额
    - 需求11.4: 在每次API调用后扣除相应的token数量
"""

from datetime import date
from typing import List, Optional

from dateutil.relativedelta import relativedelta
from sqlalchemy import and_
from sqlalchemy.orm import Session

from app.models.user_quota import UserQuota

# 默认月度配额（tokens）
DEFAULT_MONTHLY_QUOTA = 100000


class QuotaRepository:
    """
    配额Repository类

    提供用户配额数据的CRUD操作和查询功能。

    使用方式:
        repo = QuotaRepository(db)
        quota = repo.create(user_id=1)
        quota = repo.get_by_user_id(1)
        repo.consume_quota(user_id=1, tokens=100)
    """

    def __init__(self, db: Session):
        """
        初始化Repository

        Args:
            db: SQLAlchemy数据库会话
        """
        self.db = db

    def create(
        self, user_id: int, monthly_quota: int = DEFAULT_MONTHLY_QUOTA
    ) -> UserQuota:
        """
        为用户创建配额记录

        Args:
            user_id: 用户ID
            monthly_quota: 月度配额上限（默认100000 tokens）

        Returns:
            UserQuota: 创建的配额对象

        需求引用:
            - 需求11.1: 为每个用户设置默认的月度token配额
        """
        # 计算下个月1日作为重置日期
        today = date.today()
        next_month = today + relativedelta(months=1)
        reset_date = date(next_month.year, next_month.month, 1)

        quota = UserQuota(
            user_id=user_id,
            monthly_quota=monthly_quota,
            used_quota=0,
            reset_date=reset_date,
        )
        self.db.add(quota)
        self.db.commit()
        self.db.refresh(quota)
        return quota

    def get_by_id(self, quota_id: int) -> Optional[UserQuota]:
        """
        根据ID获取配额记录

        Args:
            quota_id: 配额记录ID

        Returns:
            Optional[UserQuota]: 配额对象，不存在则返回None
        """
        return self.db.query(UserQuota).filter(UserQuota.id == quota_id).first()

    def get_by_user_id(self, user_id: int) -> Optional[UserQuota]:
        """
        根据用户ID获取配额记录

        Args:
            user_id: 用户ID

        Returns:
            Optional[UserQuota]: 配额对象，不存在则返回None
        """
        return self.db.query(UserQuota).filter(UserQuota.user_id == user_id).first()

    def get_or_create(
        self, user_id: int, monthly_quota: int = DEFAULT_MONTHLY_QUOTA
    ) -> UserQuota:
        """
        获取用户配额，如果不存在则创建

        Args:
            user_id: 用户ID
            monthly_quota: 月度配额上限（仅在创建时使用）

        Returns:
            UserQuota: 配额对象
        """
        quota = self.get_by_user_id(user_id)
        if quota is None:
            quota = self.create(user_id, monthly_quota)
        return quota

    def update_monthly_quota(self, user_id: int, new_quota: int) -> Optional[UserQuota]:
        """
        更新用户的月度配额上限

        Args:
            user_id: 用户ID
            new_quota: 新的月度配额上限

        Returns:
            Optional[UserQuota]: 更新后的配额对象，用户不存在则返回None
        """
        quota = self.get_by_user_id(user_id)
        if not quota:
            return None

        quota.monthly_quota = new_quota
        self.db.commit()
        self.db.refresh(quota)
        return quota

    def consume_quota(self, user_id: int, tokens_used: int) -> Optional[UserQuota]:
        """
        消耗用户配额（扣除token）

        Args:
            user_id: 用户ID
            tokens_used: 消耗的token数量

        Returns:
            Optional[UserQuota]: 更新后的配额对象，用户不存在则返回None

        需求引用:
            - 需求11.4: 在每次API调用后扣除相应的token数量
        """
        quota = self.get_by_user_id(user_id)
        if not quota:
            return None

        quota.used_quota += tokens_used
        self.db.commit()
        self.db.refresh(quota)
        return quota

    def check_quota(self, user_id: int, tokens_required: int) -> bool:
        """
        检查用户是否有足够的配额

        Args:
            user_id: 用户ID
            tokens_required: 需要的token数量

        Returns:
            bool: 配额充足返回True，否则返回False
        """
        quota = self.get_by_user_id(user_id)
        if not quota:
            return False

        return quota.has_sufficient_quota(tokens_required)

    def reset_quota(self, user_id: int) -> Optional[UserQuota]:
        """
        重置用户配额（将已使用配额清零，更新重置日期）

        Args:
            user_id: 用户ID

        Returns:
            Optional[UserQuota]: 更新后的配额对象，用户不存在则返回None
        """
        quota = self.get_by_user_id(user_id)
        if not quota:
            return None

        # 重置已使用配额
        quota.used_quota = 0

        # 计算下个月1日作为新的重置日期
        today = date.today()
        next_month = today + relativedelta(months=1)
        quota.reset_date = date(next_month.year, next_month.month, 1)

        self.db.commit()
        self.db.refresh(quota)
        return quota

    def get_quotas_to_reset(self, reset_date: date) -> List[UserQuota]:
        """
        获取需要重置的配额记录（重置日期小于等于指定日期）

        Args:
            reset_date: 重置日期

        Returns:
            List[UserQuota]: 需要重置的配额列表
        """
        return self.db.query(UserQuota).filter(UserQuota.reset_date <= reset_date).all()

    def reset_all_expired_quotas(self) -> int:
        """
        重置所有过期的配额（重置日期小于等于今天）

        Returns:
            int: 重置的配额数量
        """
        today = date.today()
        quotas = self.get_quotas_to_reset(today)

        count = 0
        for quota in quotas:
            quota.used_quota = 0
            # 计算下个月1日作为新的重置日期
            next_month = today + relativedelta(months=1)
            quota.reset_date = date(next_month.year, next_month.month, 1)
            count += 1

        if count > 0:
            self.db.commit()

        return count

    def get_all(self, skip: int = 0, limit: int = 100) -> List[UserQuota]:
        """
        获取所有配额记录（分页）

        Args:
            skip: 跳过的记录数
            limit: 返回的最大记录数

        Returns:
            List[UserQuota]: 配额列表
        """
        return self.db.query(UserQuota).offset(skip).limit(limit).all()

    def count(self) -> int:
        """
        获取配额记录总数

        Returns:
            int: 配额记录总数
        """
        return self.db.query(UserQuota).count()

    def delete(self, user_id: int) -> bool:
        """
        删除用户配额记录

        Args:
            user_id: 用户ID

        Returns:
            bool: 删除成功返回True，记录不存在返回False
        """
        quota = self.get_by_user_id(user_id)
        if not quota:
            return False

        self.db.delete(quota)
        self.db.commit()
        return True


# 导出
__all__ = ["QuotaRepository", "DEFAULT_MONTHLY_QUOTA"]
