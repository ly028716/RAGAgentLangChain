"""
系统提示词模型

定义SystemPrompt数据库模型，用于存储系统提示词配置。
"""

from datetime import datetime

from sqlalchemy import (Boolean, Column, DateTime, ForeignKey, Index, Integer,
                        String, Text)
from sqlalchemy.orm import relationship

from app.core.database import Base


class SystemPrompt(Base):
    """
    系统提示词模型

    存储系统内置和用户自定义的提示词。

    字段说明:
        id: 提示词唯一标识
        user_id: 所属用户ID（null为全局/系统提示词）
        name: 提示词名称
        content: 提示词内容
        category: 分类（general/professional/creative）
        is_default: 是否为用户默认提示词
        is_system: 是否为系统内置提示词
        created_at: 创建时间
        updated_at: 更新时间
    """

    __tablename__ = "system_prompts"

    # 主键
    id = Column(Integer, primary_key=True, index=True, comment="提示词ID")

    # 外键（null表示系统级提示词）
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
        comment="用户ID",
    )

    # 基本信息
    name = Column(String(100), nullable=False, comment="提示词名称")
    content = Column(Text, nullable=False, comment="提示词内容")
    category = Column(
        String(50),
        nullable=True,
        default="general",
        comment="分类: general/professional/creative",
    )

    # 状态标识
    is_default = Column(Boolean, default=False, nullable=False, comment="是否为默认提示词")
    is_system = Column(Boolean, default=False, nullable=False, comment="是否为系统内置")

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
    user = relationship("User", backref="system_prompts")

    # 复合索引
    __table_args__ = (
        Index("idx_sp_user_default", "user_id", "is_default"),
        Index("idx_sp_category", "category"),
        {"comment": "系统提示词表"},
    )

    def __repr__(self) -> str:
        return (
            f"<SystemPrompt(id={self.id}, name='{self.name}', user_id={self.user_id})>"
        )

    def __str__(self) -> str:
        return f"SystemPrompt: {self.name}"
