"""
知识库权限相关的Pydantic模型

定义知识库权限管理的请求/响应模型。
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class PermissionBase(BaseModel):
    """权限基础模型"""

    user_id: Optional[int] = Field(None, description="用户ID（null表示公开权限）")
    permission_type: str = Field(
        ..., pattern="^(owner|editor|viewer)$", description="权限类型: owner/editor/viewer"
    )


class PermissionCreate(PermissionBase):
    """创建权限请求"""

    pass


class PermissionUpdate(BaseModel):
    """更新权限请求"""

    permission_type: str = Field(
        ..., pattern="^(owner|editor|viewer)$", description="权限类型: owner/editor/viewer"
    )


class PermissionResponse(BaseModel):
    """权限响应"""

    id: int = Field(..., description="权限ID")
    knowledge_base_id: int = Field(..., description="知识库ID")
    user_id: Optional[int] = Field(None, description="用户ID")
    username: Optional[str] = Field(None, description="用户名")
    permission_type: str = Field(..., description="权限类型")
    is_public: bool = Field(..., description="是否公开")
    created_at: datetime = Field(..., description="创建时间")

    class Config:
        from_attributes = True


class PermissionListResponse(BaseModel):
    """权限列表响应"""

    items: List[PermissionResponse] = Field(..., description="权限列表")
    total: int = Field(..., description="总数")


class VisibilityUpdate(BaseModel):
    """更新可见性请求"""

    visibility: str = Field(
        ...,
        pattern="^(private|shared|public)$",
        description="可见性: private/shared/public",
    )


class VisibilityResponse(BaseModel):
    """可见性响应"""

    knowledge_base_id: int = Field(..., description="知识库ID")
    visibility: str = Field(..., description="可见性")
    message: str = Field(..., description="响应消息")


class ShareKnowledgeBaseRequest(BaseModel):
    """分享知识库请求"""

    username: str = Field(..., min_length=1, max_length=50, description="目标用户名")
    permission_type: str = Field(
        default="viewer", pattern="^(editor|viewer)$", description="权限类型: editor/viewer"
    )


__all__ = [
    "PermissionBase",
    "PermissionCreate",
    "PermissionUpdate",
    "PermissionResponse",
    "PermissionListResponse",
    "VisibilityUpdate",
    "VisibilityResponse",
    "ShareKnowledgeBaseRequest",
]
