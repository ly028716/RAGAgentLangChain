"""
验证码模型

定义VerificationCode数据库模型，用于存储邮箱/短信验证码。
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Index

from app.core.database import Base


class VerificationCode(Base):
    """
    验证码模型
    
    存储邮箱和短信验证码信息。
    
    字段说明:
        id: 验证码唯一标识
        target: 目标(邮箱/手机号)
        code: 6位验证码
        code_type: 类型(register/reset_password/bind_email)
        channel: 渠道(email/sms)
        expires_at: 过期时间
        is_used: 是否已使用
        attempts: 验证尝试次数
        created_at: 创建时间
    """
    __tablename__ = "verification_codes"
    
    id = Column(Integer, primary_key=True, index=True, comment="验证码ID")
    target = Column(String(100), nullable=False, index=True, comment="目标(邮箱/手机号)")
    code = Column(String(6), nullable=False, comment="验证码")
    code_type = Column(String(20), nullable=False, comment="类型: register/reset_password/bind_email")
    channel = Column(String(10), nullable=False, comment="渠道: email/sms")
    expires_at = Column(DateTime, nullable=False, comment="过期时间")
    is_used = Column(Boolean, default=False, comment="是否已使用")
    attempts = Column(Integer, default=0, comment="验证尝试次数")
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    
    __table_args__ = (
        Index('idx_vc_target_type', 'target', 'code_type'),
        Index('idx_vc_expires', 'expires_at'),
        {'comment': '验证码表'}
    )
    
    def __repr__(self) -> str:
        return f"<VerificationCode(id={self.id}, target='{self.target}', code_type='{self.code_type}')>"
