"""
配额相关Pydantic模型

定义配额API请求和响应的数据模型。

需求引用:
    - 需求11.7: 返回当月已使用token数、剩余token数和配额重置日期
"""

from datetime import date
from pydantic import BaseModel, Field


class QuotaResponse(BaseModel):
    """
    配额信息响应模型
    
    返回用户的配额使用情况。
    
    需求引用:
        - 需求11.7: 返回当月已使用token数、剩余token数和配额重置日期
    """
    monthly_quota: int = Field(..., description="月度配额上限（tokens）")
    used_quota: int = Field(..., description="当月已使用配额（tokens）")
    remaining_quota: int = Field(..., description="剩余配额（tokens）")
    reset_date: str = Field(..., description="配额重置日期（ISO格式）")
    usage_percentage: float = Field(..., description="使用百分比")
    
    class Config:
        json_schema_extra = {
            "example": {
                "monthly_quota": 100000,
                "used_quota": 25000,
                "remaining_quota": 75000,
                "reset_date": "2025-02-01",
                "usage_percentage": 25.0
            }
        }


class QuotaUpdateRequest(BaseModel):
    """
    配额更新请求模型（管理员）
    
    用于管理员更新用户的月度配额。
    
    需求引用:
        - 需求11.5: 管理员更新用户配额
    """
    user_id: int = Field(..., gt=0, description="用户ID")
    monthly_quota: int = Field(..., ge=1000, description="新的月度配额上限（最小1000 tokens）")
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_id": 1,
                "monthly_quota": 200000
            }
        }


class QuotaUpdateResponse(BaseModel):
    """
    配额更新响应模型
    
    返回更新后的配额信息。
    """
    user_id: int = Field(..., description="用户ID")
    monthly_quota: int = Field(..., description="更新后的月度配额上限")
    used_quota: int = Field(..., description="当前已使用配额")
    remaining_quota: int = Field(..., description="剩余配额")
    reset_date: str = Field(..., description="配额重置日期")
    updated_at: str = Field(..., description="更新时间")
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_id": 1,
                "monthly_quota": 200000,
                "used_quota": 25000,
                "remaining_quota": 175000,
                "reset_date": "2025-02-01",
                "updated_at": "2025-01-08T10:00:00Z"
            }
        }


class QuotaErrorResponse(BaseModel):
    """
    配额错误响应模型
    
    用于配额不足等错误情况。
    """
    message: str = Field(..., description="错误消息")
    remaining_quota: int = Field(..., description="剩余配额")
    reset_date: str = Field(..., description="配额重置日期")
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "配额不足，无法进行对话",
                "remaining_quota": 0,
                "reset_date": "2025-02-01"
            }
        }


# 导出
__all__ = [
    'QuotaResponse',
    'QuotaUpdateRequest',
    'QuotaUpdateResponse',
    'QuotaErrorResponse',
]
