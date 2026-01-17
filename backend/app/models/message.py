"""
消息模型

定义Message数据库模型，用于存储对话中的消息内容。
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum, Index
from sqlalchemy.orm import relationship
import enum

from app.core.database import Base


class MessageRole(str, enum.Enum):
    """消息角色枚举"""
    USER = "user"           # 用户消息
    ASSISTANT = "assistant" # AI助手消息
    SYSTEM = "system"       # 系统消息


class Message(Base):
    """
    消息模型
    
    存储对话中的每条消息，包括用户输入和AI回复。
    
    字段说明:
        id: 消息唯一标识
        conversation_id: 所属对话ID（外键）
        role: 消息角色（user/assistant/system）
        content: 消息内容
        tokens: 消息消耗的token数量
        created_at: 消息创建时间
    
    关系:
        conversation: 所属对话
    
    索引:
        - conversation_id: 用于快速查询对话的所有消息
        - created_at: 用于按时间排序
        - (conversation_id, created_at): 复合索引，优化消息列表查询
    """
    __tablename__ = "messages"
    
    # 主键
    id = Column(Integer, primary_key=True, index=True, comment="消息ID")
    
    # 外键
    conversation_id = Column(
        Integer,
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="对话ID"
    )
    
    # 消息信息
    role = Column(
        Enum(MessageRole),
        nullable=False,
        comment="消息角色"
    )
    content = Column(
        Text,
        nullable=False,
        comment="消息内容"
    )
    tokens = Column(
        Integer,
        default=0,
        nullable=False,
        comment="消耗的token数量"
    )
    
    # 时间戳
    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        index=True,
        comment="创建时间"
    )
    
    # 关系映射
    conversation = relationship("Conversation", back_populates="messages")
    
    # 复合索引
    __table_args__ = (
        Index('idx_conversation_created', 'conversation_id', 'created_at'),
        {'comment': '消息表'}
    )
    
    def __repr__(self) -> str:
        """字符串表示"""
        content_preview = self.content[:50] + "..." if len(self.content) > 50 else self.content
        return f"<Message(id={self.id}, conversation_id={self.conversation_id}, role={self.role.value})>"
    
    def __str__(self) -> str:
        """用户友好的字符串表示"""
        content_preview = self.content[:30] + "..." if len(self.content) > 30 else self.content
        return f"Message[{self.role.value}]: {content_preview}"
