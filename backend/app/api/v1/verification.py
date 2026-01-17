"""
验证码API路由

提供邮箱和短信验证码的发送和验证端点。
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.verification import (
    SendEmailCodeRequest,
    SendSMSCodeRequest,
    VerifyCodeRequest,
    SendCodeResponse,
    VerifyCodeResponse,
)
from app.services.verification_service import VerificationService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/verification", tags=["验证码"])


@router.post(
    "/send-email",
    response_model=SendCodeResponse,
    summary="发送邮箱验证码",
    description="发送6位数字验证码到指定邮箱，10分钟内有效。"
)
async def send_email_code(
    request: SendEmailCodeRequest,
    db: Session = Depends(get_db)
) -> SendCodeResponse:
    """
    发送邮箱验证码
    
    - 每小时最多发送5次
    - 两次发送间隔至少60秒
    - 验证码10分钟内有效
    """
    service = VerificationService(db)
    result = await service.send_email_code(
        email=request.email,
        code_type=request.code_type
    )
    
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=result["message"]
        )
    
    return SendCodeResponse(**result)


@router.post(
    "/send-sms",
    response_model=SendCodeResponse,
    summary="发送短信验证码",
    description="发送6位数字验证码到指定手机号，10分钟内有效。"
)
async def send_sms_code(
    request: SendSMSCodeRequest,
    db: Session = Depends(get_db)
) -> SendCodeResponse:
    """
    发送短信验证码
    
    - 每小时最多发送5次
    - 两次发送间隔至少60秒
    - 验证码10分钟内有效
    """
    service = VerificationService(db)
    result = await service.send_sms_code(
        phone=request.phone,
        code_type=request.code_type
    )
    
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=result["message"]
        )
    
    return SendCodeResponse(**result)


@router.post(
    "/verify",
    response_model=VerifyCodeResponse,
    summary="验证验证码",
    description="验证邮箱或短信验证码是否正确。"
)
def verify_code(
    request: VerifyCodeRequest,
    db: Session = Depends(get_db)
) -> VerifyCodeResponse:
    """
    验证验证码
    
    - 最多验证5次
    - 验证成功后验证码失效
    """
    service = VerificationService(db)
    result = service.verify_code(
        target=request.target,
        code=request.code,
        code_type=request.code_type
    )
    
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["message"]
        )
    
    return VerifyCodeResponse(**result)


__all__ = ['router']
