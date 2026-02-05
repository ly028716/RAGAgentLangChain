"""
用户API路由

提供用户信息管理、头像上传和账号注销端点。
"""

import logging

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.user import (AvatarDeleteResponse, AvatarUploadResponse,
                              DeletionCancelResponse, DeletionRequest,
                              DeletionRequestResponse, DeletionStatusResponse,
                              UserProfileResponse, UserProfileUpdate)
from app.services.file_service import file_service
from app.services.user_service import (DeletionAlreadyRequestedError,
                                       DeletionCooldownExpiredError,
                                       NoDeletionRequestError,
                                       PasswordMismatchError,
                                       UserNotFoundError, UserService)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/user", tags=["用户"])


@router.get(
    "/profile",
    response_model=UserProfileResponse,
    summary="获取当前用户信息",
    description="获取当前登录用户的详细信息。",
)
def get_profile(current_user: User = Depends(get_current_user)) -> UserProfileResponse:
    """获取当前用户信息"""
    return UserProfileResponse.model_validate(current_user)


@router.put(
    "/profile",
    response_model=UserProfileResponse,
    summary="更新用户信息",
    description="更新当前用户的个人信息。",
)
def update_profile(
    data: UserProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UserProfileResponse:
    """更新用户信息"""
    user_repo = UserRepository(db)

    # 更新字段
    if data.email is not None:
        # 检查邮箱是否已被使用
        existing = user_repo.get_by_email(data.email)
        if existing and existing.id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="该邮箱已被使用"
            )
        current_user.email = data.email

    db.commit()
    db.refresh(current_user)

    return UserProfileResponse.model_validate(current_user)


@router.post(
    "/avatar",
    response_model=AvatarUploadResponse,
    summary="上传头像",
    description="上传用户头像，支持JPEG、PNG、GIF、WebP格式，最大2MB。",
)
async def upload_avatar(
    file: UploadFile = File(..., description="头像文件"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AvatarUploadResponse:
    """上传用户头像"""
    result = await file_service.save_avatar(current_user.id, file)

    # 更新用户头像URL
    current_user.avatar = result["avatar_url"]
    db.commit()

    return AvatarUploadResponse(
        avatar_url=result["avatar_url"],
        thumbnail_url=result["thumbnail_url"],
        message="头像上传成功",
    )


@router.delete(
    "/avatar",
    response_model=AvatarDeleteResponse,
    summary="删除头像",
    description="删除当前用户的头像。",
)
def delete_avatar(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> AvatarDeleteResponse:
    """删除用户头像"""
    success = file_service.delete_avatar(current_user.id)

    if success:
        current_user.avatar = None
        db.commit()

    return AvatarDeleteResponse(
        success=success, message="头像删除成功" if success else "头像删除失败"
    )


@router.get("/avatar/{user_id}", summary="获取用户头像", description="获取指定用户的头像文件。")
def get_avatar(user_id: int, db: Session = Depends(get_db)):
    """获取用户头像"""
    avatar_path = file_service.get_avatar_path(user_id)

    if not avatar_path or not avatar_path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="头像不存在")

    # 根据文件扩展名确定正确的media_type
    extension = avatar_path.suffix.lower()
    media_types = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".gif": "image/gif",
        ".webp": "image/webp",
    }
    media_type = media_types.get(extension, "image/jpeg")

    return FileResponse(
        path=str(avatar_path), media_type=media_type, filename=avatar_path.name
    )


# ==================== 账号注销相关API ====================


@router.post(
    "/deletion/request",
    response_model=DeletionRequestResponse,
    summary="请求注销账号",
    description="请求注销账号，需要验证密码。注销请求后有7天冷静期，期间可以取消。",
)
def request_deletion(
    data: DeletionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DeletionRequestResponse:
    """请求注销账号"""
    user_service = UserService(db)

    try:
        result = user_service.request_deletion(
            user_id=current_user.id, password=data.password, reason=data.reason
        )
        return DeletionRequestResponse(**result)
    except PasswordMismatchError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="密码不正确")
    except DeletionAlreadyRequestedError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except UserNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")


@router.post(
    "/deletion/cancel",
    response_model=DeletionCancelResponse,
    summary="取消注销请求",
    description="在冷静期内取消注销请求，恢复账号正常状态。",
)
def cancel_deletion(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> DeletionCancelResponse:
    """取消注销请求"""
    user_service = UserService(db)

    try:
        result = user_service.cancel_deletion(user_id=current_user.id)
        return DeletionCancelResponse(**result)
    except NoDeletionRequestError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except DeletionCooldownExpiredError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except UserNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")


@router.get(
    "/deletion/status",
    response_model=DeletionStatusResponse,
    summary="查询注销状态",
    description="查询当前账号的注销状态，包括是否有待处理的注销请求、剩余冷静期等信息。",
)
def get_deletion_status(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> DeletionStatusResponse:
    """查询注销状态"""
    user_service = UserService(db)

    try:
        result = user_service.get_deletion_status(user_id=current_user.id)
        return DeletionStatusResponse(**result)
    except UserNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")


__all__ = ["router"]
