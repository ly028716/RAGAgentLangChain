"""
API使用记录模型

定义APIUsage数据库模型，用于记录用户的API调用和token消耗。
"""

from datetime import datetime
from decimal import Decimal
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Numeric, Index

from app.core.database import Base


class APIUsage(Base):
    """
    API使用记录模型
    
    记录每次API调用的详细信息，用于统计和计费。
    
    字段说明:
        id: 记录唯一标识
        user_id: 调用用户ID（外键）
        api_type: API类型（如chat, rag, agent等）
        tokens_used: 本次调用消耗的token数量
        cost: 本次调用的费用（可选，用于计费）
        created_at: 调用时间
    
    索引:
        - user_id: 用于查询用户的使用记录
        - created_at: 用于按时间范围查询
        - api_type: 用于按API类型统计
        - (user_id, created_at): 复合索引，优化用户使用记录查询
        - (user_id, api_type): 复合索引，优化按类型统计
    
    需求引用:
        - 需求8.1: 在每次调用通义千问API后记录用户ID、API类型、token消耗和时间戳
        - 需求8.2: 返回总token消耗、API调用次数、活跃用户数和功能使用热度
        - 需求8.3: 按用户维度统计token消耗并支持按时间范围筛选
    """
    __tablename__ = "api_usage"
    
    # 主键
    id = Column(Integer, primary_key=True, index=True, comment="记录ID")
    
    # 外键
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="用户ID"
    )
    
    # 使用信息
    api_type = Column(
        String(50),
        nullable=False,
        index=True,
        comment="API类型（chat/rag/agent等）"
    )
    tokens_used = Column(
        Integer,
        nullable=False,
        comment="消耗的token数量"
    )
    cost = Column(
        Numeric(10, 4),
        default=Decimal("0.0000"),
        nullable=False,
        comment="调用费用"
    )
    
    # 时间戳
    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        index=True,
        comment="调用时间"
    )
    
    # 复合索引
    __table_args__ = (
        Index('idx_usage_user_created', 'user_id', 'created_at'),
        Index('idx_usage_user_api_type', 'user_id', 'api_type'),
        Index('idx_usage_api_type_created', 'api_type', 'created_at'),
        {'comment': 'API使用记录表'}
    )
    
    def __repr__(self) -> str:
        """字符串表示"""
        return f"<APIUsage(id={self.id}, user_id={self.user_id}, api_type='{self.api_type}', tokens={self.tokens_used})>"
    
    def __str__(self) -> str:
        """用户友好的字符串表示"""
        return f"API Usage: {self.api_type} - {self.tokens_used} tokens"
