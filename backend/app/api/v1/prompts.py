"""
系统提示词API路由

提供系统提示词的CRUD操作端点。
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.system_prompt import (SetDefaultPromptResponse,
                                       SystemPromptCreate,
                                       SystemPromptListResponse,
                                       SystemPromptResponse,
                                       SystemPromptUpdate)
from app.services.system_prompt_service import SystemPromptService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/prompts", tags=["系统提示词"])


@router.get(
    "",
    response_model=SystemPromptListResponse,
    summary="获取提示词列表",
    description="获取系统提示词和用户自定义提示词列表。",
)
def get_prompts(
    category: Optional[str] = Query(None, description="分类筛选"),
    skip: int = Query(0, ge=0, description="跳过数量"),
    limit: int = Query(20, ge=1, le=100, description="返回数量"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SystemPromptListResponse:
    """获取提示词列表"""
    service = SystemPromptService(db)
    prompts, total = service.get_prompts(
        user_id=current_user.id, category=category, skip=skip, limit=limit
    )

    return SystemPromptListResponse(
        items=[SystemPromptResponse.model_validate(p) for p in prompts], total=total
    )


@router.post(
    "",
    response_model=SystemPromptResponse,
    status_code=status.HTTP_201_CREATED,
    summary="创建提示词",
    description="创建用户自定义提示词。",
)
def create_prompt(
    data: SystemPromptCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SystemPromptResponse:
    """创建提示词"""
    service = SystemPromptService(db)
    prompt = service.create_prompt(current_user.id, data)
    return SystemPromptResponse.model_validate(prompt)


@router.get(
    "/{prompt_id}",
    response_model=SystemPromptResponse,
    summary="获取提示词详情",
    description="获取指定提示词的详细信息。",
)
def get_prompt(
    prompt_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SystemPromptResponse:
    """获取提示词详情"""
    service = SystemPromptService(db)
    prompt = service.get_prompt_by_id(prompt_id, current_user.id)

    if not prompt:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="提示词不存在")

    return SystemPromptResponse.model_validate(prompt)


@router.put(
    "/{prompt_id}",
    response_model=SystemPromptResponse,
    summary="更新提示词",
    description="更新用户自定义提示词（不能更新系统提示词）。",
)
def update_prompt(
    prompt_id: int,
    data: SystemPromptUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SystemPromptResponse:
    """更新提示词"""
    service = SystemPromptService(db)
    prompt = service.update_prompt(prompt_id, current_user.id, data)

    if not prompt:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="提示词不存在或无权修改")

    return SystemPromptResponse.model_validate(prompt)


@router.delete(
    "/{prompt_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="删除提示词",
    description="删除用户自定义提示词（不能删除系统提示词）。",
)
def delete_prompt(
    prompt_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """删除提示词"""
    service = SystemPromptService(db)
    success = service.delete_prompt(prompt_id, current_user.id)

    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="提示词不存在或无权删除")


@router.put(
    "/{prompt_id}/default",
    response_model=SetDefaultPromptResponse,
    summary="设为默认提示词",
    description="将指定提示词设为用户的默认提示词。",
)
def set_default_prompt(
    prompt_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SetDefaultPromptResponse:
    """设为默认提示词"""
    service = SystemPromptService(db)
    success = service.set_default_prompt(prompt_id, current_user.id)

    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="提示词不存在")

    return SetDefaultPromptResponse(success=True, message="设置成功")


__all__ = ["router"]
