"""
登录尝试记录模型

定义LoginAttempt数据库模型，用于记录用户登录尝试，支持账户锁定机制。
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Index

from app.core.database import Base


class LoginAttempt(Base):
    """
    登录尝试记录模型
    
    记录每次登录尝试的详细信息，用于安全审计和账户锁定机制。
    
    字段说明:
        id: 记录唯一标识
        username: 尝试登录的用户名
        ip_address: 登录请求的IP地址
        success: 登录是否成功
        created_at: 尝试时间
    
    索引:
        - username: 用于查询特定用户的登录尝试
        - created_at: 用于按时间范围查询和清理旧记录
        - (username, created_at): 复合索引，优化账户锁定检查
        - (username, success): 复合索引，优化失败次数统计
    
    需求引用:
        - 需求1.7: 用户连续5次登录失败后锁定账户15分钟
        - 需求9.7: 记录所有认证失败尝试
        - 需求8.5: 清理旧登录记录任务
    
    注意:
        - 此表用于持久化存储登录尝试记录
        - 实时的登录失败计数和账户锁定状态存储在Redis中
        - 此表主要用于审计和历史记录查询
    """
    __tablename__ = "login_attempts"
    
    # 主键
    id = Column(Integer, primary_key=True, index=True, comment="记录ID")
    
    # 登录信息
    username = Column(
        String(50),
        nullable=False,
        index=True,
        comment="尝试登录的用户名"
    )
    ip_address = Column(
        String(45),
        nullable=False,
        comment="登录请求IP地址（支持IPv6）"
    )
    success = Column(
        Boolean,
        nullable=False,
        comment="登录是否成功"
    )
    
    # 时间戳
    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        index=True,
        comment="尝试时间"
    )
    
    # 复合索引
    __table_args__ = (
        Index('idx_login_username_created', 'username', 'created_at'),
        Index('idx_login_username_success', 'username', 'success'),
        Index('idx_login_ip_created', 'ip_address', 'created_at'),
        {'comment': '登录尝试记录表'}
    )
    
    def __repr__(self) -> str:
        """字符串表示"""
        status = "成功" if self.success else "失败"
        return f"<LoginAttempt(id={self.id}, username='{self.username}', success={self.success})>"
    
    def __str__(self) -> str:
        """用户友好的字符串表示"""
        status = "成功" if self.success else "失败"
        return f"Login Attempt: {self.username} - {status}"
