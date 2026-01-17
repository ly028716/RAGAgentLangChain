"""
用户模型

定义User数据库模型，包含用户基本信息、认证信息和关系映射。
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text
from sqlalchemy.orm import relationship

from app.core.database import Base


class User(Base):
    """
    用户模型
    
    存储用户的基本信息和认证相关数据。
    
    字段说明:
        id: 用户唯一标识
        username: 用户名，唯一，用于登录
        email: 邮箱地址，唯一，可选
        password_hash: 密码哈希值（bcrypt加密）
        avatar: 头像URL，可选
        created_at: 账户创建时间
        updated_at: 账户最后更新时间
        last_login: 最后登录时间
        is_active: 账户是否激活
        deletion_requested_at: 注销请求时间
        deletion_scheduled_at: 计划删除时间
        deletion_reason: 注销原因
    
    关系:
        conversations: 用户的所有对话
        knowledge_bases: 用户的所有知识库
        quota: 用户配额信息（一对一）
    """
    __tablename__ = "users"
    
    # 主键
    id = Column(Integer, primary_key=True, index=True, comment="用户ID")
    
    # 基本信息
    username = Column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
        comment="用户名"
    )
    email = Column(
        String(100),
        unique=True,
        nullable=True,
        index=True,
        comment="邮箱地址"
    )
    password_hash = Column(
        String(255),
        nullable=False,
        comment="密码哈希值"
    )
    avatar = Column(
        String(255),
        nullable=True,
        comment="头像URL"
    )
    
    # 时间戳
    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        comment="创建时间"
    )
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
        comment="更新时间"
    )
    last_login = Column(
        DateTime,
        nullable=True,
        comment="最后登录时间"
    )
    
    # 状态
    is_active = Column(
        Boolean,
        default=True,
        nullable=False,
        comment="是否激活"
    )
    is_admin = Column(
        Boolean,
        default=False,
        nullable=False,
        comment="是否为管理员"
    )
    
    # 账号注销相关字段
    deletion_requested_at = Column(
        DateTime,
        nullable=True,
        comment="注销请求时间"
    )
    deletion_scheduled_at = Column(
        DateTime,
        nullable=True,
        comment="计划删除时间"
    )
    deletion_reason = Column(
        Text,
        nullable=True,
        comment="注销原因"
    )
    
    # 关系映射
    conversations = relationship("Conversation", back_populates="user", cascade="all, delete-orphan")
    knowledge_bases = relationship("KnowledgeBase", back_populates="user", cascade="all, delete-orphan")
    quota = relationship("UserQuota", back_populates="user", uselist=False, cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        """字符串表示"""
        return f"<User(id={self.id}, username='{self.username}', email='{self.email}', is_admin={self.is_admin})>"
    
    def __str__(self) -> str:
        """用户友好的字符串表示"""
        return f"User: {self.username}"
