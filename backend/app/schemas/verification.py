"""
验证码相关的Pydantic模型

定义验证码发送和验证的请求/响应模型。
"""

from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class SendEmailCodeRequest(BaseModel):
    """发送邮箱验证码请求"""

    email: EmailStr = Field(..., description="邮箱地址")
    code_type: str = Field(
        ...,
        pattern="^(register|reset_password|bind_email)$",
        description="验证码类型: register/reset_password/bind_email",
    )


class SendSMSCodeRequest(BaseModel):
    """发送短信验证码请求"""

    phone: str = Field(..., pattern="^1[3-9]\\d{9}$", description="手机号码")
    code_type: str = Field(
        ...,
        pattern="^(register|reset_password|bind_phone)$",
        description="验证码类型: register/reset_password/bind_phone",
    )


class VerifyCodeRequest(BaseModel):
    """验证验证码请求"""

    target: str = Field(..., min_length=1, max_length=100, description="目标(邮箱/手机号)")
    code: str = Field(
        ..., min_length=6, max_length=6, pattern="^\\d{6}$", description="6位数字验证码"
    )
    code_type: str = Field(
        ...,
        pattern="^(register|reset_password|bind_email|bind_phone)$",
        description="验证码类型: register/reset_password/bind_email/bind_phone",
    )


class SendCodeResponse(BaseModel):
    """发送验证码响应"""

    success: bool = Field(..., description="是否发送成功")
    message: str = Field(..., description="响应消息")
    expires_in: int = Field(..., description="验证码有效期(秒)")


class VerifyCodeResponse(BaseModel):
    """验证验证码响应"""

    success: bool = Field(..., description="是否验证成功")
    message: str = Field(..., description="响应消息")


__all__ = [
    "SendEmailCodeRequest",
    "SendSMSCodeRequest",
    "VerifyCodeRequest",
    "SendCodeResponse",
    "VerifyCodeResponse",
]
