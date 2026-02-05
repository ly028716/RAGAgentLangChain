"""
系统提示词相关的Pydantic模型

定义系统提示词的请求/响应模型。
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class SystemPromptBase(BaseModel):
    """系统提示词基础模型"""

    name: str = Field(..., min_length=1, max_length=100, description="提示词名称")
    content: str = Field(..., min_length=1, max_length=10000, description="提示词内容")
    category: Optional[str] = Field(
        default="general",
        pattern="^(general|professional|creative)$",
        description="分类: general/professional/creative",
    )


class SystemPromptCreate(SystemPromptBase):
    """创建系统提示词请求"""

    pass


class SystemPromptUpdate(BaseModel):
    """更新系统提示词请求"""

    name: Optional[str] = Field(None, min_length=1, max_length=100, description="提示词名称")
    content: Optional[str] = Field(
        None, min_length=1, max_length=10000, description="提示词内容"
    )
    category: Optional[str] = Field(
        None,
        pattern="^(general|professional|creative)$",
        description="分类: general/professional/creative",
    )


class SystemPromptResponse(SystemPromptBase):
    """系统提示词响应"""

    id: int = Field(..., description="提示词ID")
    user_id: Optional[int] = Field(None, description="用户ID")
    is_default: bool = Field(..., description="是否为默认提示词")
    is_system: bool = Field(..., description="是否为系统内置")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    class Config:
        from_attributes = True


class SystemPromptListResponse(BaseModel):
    """系统提示词列表响应"""

    items: List[SystemPromptResponse] = Field(..., description="提示词列表")
    total: int = Field(..., description="总数")


class SetDefaultPromptRequest(BaseModel):
    """设置默认提示词请求"""

    pass  # 无需额外参数，通过URL路径传递ID


class SetDefaultPromptResponse(BaseModel):
    """设置默认提示词响应"""

    success: bool = Field(..., description="是否成功")
    message: str = Field(..., description="响应消息")


__all__ = [
    "SystemPromptBase",
    "SystemPromptCreate",
    "SystemPromptUpdate",
    "SystemPromptResponse",
    "SystemPromptListResponse",
    "SetDefaultPromptRequest",
    "SetDefaultPromptResponse",
]
