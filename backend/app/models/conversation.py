"""
对话模型

定义Conversation数据库模型，用于存储用户的对话会话信息。
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Index
from sqlalchemy.orm import relationship

from app.core.database import Base


class Conversation(Base):
    """
    对话模型
    
    存储用户与AI的对话会话信息。每个对话包含多条消息。
    
    字段说明:
        id: 对话唯一标识
        user_id: 所属用户ID（外键）
        title: 对话标题
        created_at: 对话创建时间
        updated_at: 对话最后更新时间
        is_deleted: 软删除标记
    
    关系:
        user: 所属用户
        messages: 对话中的所有消息
    
    索引:
        - user_id: 用于快速查询用户的所有对话
        - created_at: 用于按时间排序
        - (user_id, created_at): 复合索引，优化用户对话列表查询
    """
    __tablename__ = "conversations"
    
    # 主键
    id = Column(Integer, primary_key=True, index=True, comment="对话ID")
    
    # 外键
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="用户ID"
    )
    
    # 基本信息
    title = Column(
        String(200),
        nullable=False,
        default="新对话",
        comment="对话标题"
    )
    
    # 时间戳
    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        index=True,
        comment="创建时间"
    )
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
        comment="更新时间"
    )
    
    # 状态
    is_deleted = Column(
        Boolean,
        default=False,
        nullable=False,
        comment="是否已删除（软删除）"
    )
    
    # 关系映射
    user = relationship("User", back_populates="conversations")
    messages = relationship(
        "Message",
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="Message.created_at"
    )
    
    # 复合索引
    __table_args__ = (
        Index('idx_user_created', 'user_id', 'created_at'),
        {'comment': '对话表'}
    )
    
    def __repr__(self) -> str:
        """字符串表示"""
        return f"<Conversation(id={self.id}, user_id={self.user_id}, title='{self.title}')>"
    
    def __str__(self) -> str:
        """用户友好的字符串表示"""
        return f"Conversation: {self.title}"
