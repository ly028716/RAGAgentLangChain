"""
用户相关的Pydantic模型

定义用户信息和头像上传的请求/响应模型。
"""

from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field, EmailStr


class UserProfileResponse(BaseModel):
    """用户信息响应"""
    id: int = Field(..., description="用户ID")
    username: str = Field(..., description="用户名")
    email: Optional[str] = Field(None, description="邮箱")
    avatar: Optional[str] = Field(None, description="头像URL")
    created_at: datetime = Field(..., description="创建时间")
    is_active: bool = Field(..., description="是否激活")
    is_admin: bool = Field(default=False, description="是否为管理员")
    deletion_requested_at: Optional[datetime] = Field(None, description="注销请求时间")
    deletion_scheduled_at: Optional[datetime] = Field(None, description="计划删除时间")
    
    class Config:
        from_attributes = True


class UserProfileUpdate(BaseModel):
    """更新用户信息请求"""
    nickname: Optional[str] = Field(None, max_length=50, description="昵称")
    email: Optional[EmailStr] = Field(None, description="邮箱")


class AvatarUploadResponse(BaseModel):
    """头像上传响应"""
    avatar_url: str = Field(..., description="头像URL")
    thumbnail_url: str = Field(..., description="缩略图URL")
    message: str = Field(default="头像上传成功", description="响应消息")


class AvatarDeleteResponse(BaseModel):
    """删除头像响应"""
    success: bool = Field(..., description="是否成功")
    message: str = Field(..., description="响应消息")


# 账号注销相关Schema
class DeletionRequest(BaseModel):
    """账号注销请求"""
    password: str = Field(..., min_length=1, description="用户密码（用于验证身份）")
    reason: Optional[str] = Field(None, max_length=500, description="注销原因")


class DeletionRequestResponse(BaseModel):
    """账号注销请求响应"""
    success: bool = Field(..., description="是否成功")
    message: str = Field(..., description="响应消息")
    requested_at: Optional[str] = Field(None, description="请求时间")
    scheduled_at: Optional[str] = Field(None, description="计划删除时间")
    cooldown_days: Optional[int] = Field(None, description="冷静期天数")


class DeletionCancelResponse(BaseModel):
    """取消注销响应"""
    success: bool = Field(..., description="是否成功")
    message: str = Field(..., description="响应消息")


class DeletionStatusResponse(BaseModel):
    """注销状态响应"""
    has_deletion_request: bool = Field(..., description="是否有注销请求")
    requested_at: Optional[str] = Field(None, description="请求时间")
    scheduled_at: Optional[str] = Field(None, description="计划删除时间")
    reason: Optional[str] = Field(None, description="注销原因")
    remaining_days: Optional[int] = Field(None, description="剩余天数")
    remaining_hours: Optional[int] = Field(None, description="剩余小时数")
    can_cancel: Optional[bool] = Field(None, description="是否可以取消")
    message: str = Field(..., description="状态消息")


__all__ = [
    'UserProfileResponse',
    'UserProfileUpdate',
    'AvatarUploadResponse',
    'AvatarDeleteResponse',
    'DeletionRequest',
    'DeletionRequestResponse',
    'DeletionCancelResponse',
    'DeletionStatusResponse',
]
