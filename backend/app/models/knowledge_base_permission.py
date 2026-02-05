"""
知识库权限模型

定义KnowledgeBasePermission数据库模型，用于管理知识库的访问权限。
"""

from datetime import datetime
from enum import Enum

from sqlalchemy import (Boolean, Column, DateTime, ForeignKey, Index, Integer,
                        String, UniqueConstraint)
from sqlalchemy.orm import relationship

from app.core.database import Base


class PermissionType(str, Enum):
    """权限类型枚举"""

    OWNER = "owner"  # 所有者: 完全控制
    EDITOR = "editor"  # 编辑者: 可上传/删除文档
    VIEWER = "viewer"  # 查看者: 只能查询


class KnowledgeBasePermission(Base):
    """
    知识库权限模型

    管理知识库的共享和访问权限。

    字段说明:
        id: 权限记录唯一标识
        knowledge_base_id: 知识库ID
        user_id: 被授权用户ID（null表示公开权限）
        permission_type: 权限类型（owner/editor/viewer）
        is_public: 是否公开（user_id为null时有效）
        created_at: 创建时间
    """

    __tablename__ = "knowledge_base_permissions"

    # 主键
    id = Column(Integer, primary_key=True, index=True, comment="权限ID")

    # 外键
    knowledge_base_id = Column(
        Integer,
        ForeignKey("knowledge_bases.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="知识库ID",
    )
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
        comment="用户ID",
    )

    # 权限信息
    permission_type = Column(
        String(20),
        nullable=False,
        default=PermissionType.VIEWER.value,
        comment="权限类型: owner/editor/viewer",
    )
    is_public = Column(Boolean, default=False, nullable=False, comment="是否公开")

    # 时间戳
    created_at = Column(
        DateTime, default=datetime.utcnow, nullable=False, comment="创建时间"
    )

    # 关系映射
    knowledge_base = relationship("KnowledgeBase", backref="permissions")
    user = relationship("User", backref="kb_permissions")

    # 约束和索引
    __table_args__ = (
        Index("idx_kbp_kb_user", "knowledge_base_id", "user_id"),
        UniqueConstraint("knowledge_base_id", "user_id", name="uq_kb_user_permission"),
        {"comment": "知识库权限表"},
    )

    def __repr__(self) -> str:
        return f"<KnowledgeBasePermission(kb_id={self.knowledge_base_id}, user_id={self.user_id}, type='{self.permission_type}')>"
