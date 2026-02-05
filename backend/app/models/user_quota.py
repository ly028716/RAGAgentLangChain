"""
用户配额模型

定义UserQuota数据库模型，用于管理用户的月度token使用配额。
"""

from datetime import date, datetime

from sqlalchemy import Column, Date, DateTime, ForeignKey, Index, Integer
from sqlalchemy.orm import relationship

from app.core.database import Base


class UserQuota(Base):
    """
    用户配额模型

    存储用户的月度token使用配额信息。每个用户有一个配额记录。

    字段说明:
        id: 配额记录唯一标识
        user_id: 所属用户ID（外键，唯一）
        monthly_quota: 月度配额上限（默认100000 tokens）
        used_quota: 当月已使用配额
        reset_date: 配额重置日期
        created_at: 记录创建时间
        updated_at: 记录最后更新时间

    关系:
        user: 所属用户（一对一）

    索引:
        - user_id: 唯一索引，确保每个用户只有一条配额记录
        - reset_date: 用于定时任务查询需要重置的配额

    需求引用:
        - 需求11.1: 为每个用户设置默认的月度token配额
        - 需求11.4: 在每次API调用后扣除相应的token数量
        - 需求11.6: 每月1日自动重置所有用户的配额
    """

    __tablename__ = "user_quotas"

    # 主键
    id = Column(Integer, primary_key=True, index=True, comment="配额记录ID")

    # 外键（唯一，一对一关系）
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
        comment="用户ID",
    )

    # 配额信息
    monthly_quota = Column(
        Integer, default=100000, nullable=False, comment="月度配额上限（tokens）"
    )
    used_quota = Column(Integer, default=0, nullable=False, comment="当月已使用配额（tokens）")
    reset_date = Column(Date, nullable=False, index=True, comment="配额重置日期")

    # 时间戳
    created_at = Column(
        DateTime, default=datetime.utcnow, nullable=False, comment="创建时间"
    )
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
        comment="更新时间",
    )

    # 关系映射
    user = relationship("User", back_populates="quota")

    # 表配置
    __table_args__ = (Index("idx_quota_reset_date", "reset_date"), {"comment": "用户配额表"})

    @property
    def remaining_quota(self) -> int:
        """计算剩余配额"""
        return max(0, self.monthly_quota - self.used_quota)

    @property
    def usage_percentage(self) -> float:
        """计算使用百分比"""
        if self.monthly_quota == 0:
            return 100.0
        return round((self.used_quota / self.monthly_quota) * 100, 2)

    def has_sufficient_quota(self, tokens_required: int) -> bool:
        """检查是否有足够的配额"""
        return self.remaining_quota >= tokens_required

    def __repr__(self) -> str:
        """字符串表示"""
        return f"<UserQuota(id={self.id}, user_id={self.user_id}, used={self.used_quota}/{self.monthly_quota})>"

    def __str__(self) -> str:
        """用户友好的字符串表示"""
        return f"Quota: {self.used_quota}/{self.monthly_quota} tokens"
