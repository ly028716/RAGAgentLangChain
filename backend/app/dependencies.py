"""
FastAPI依赖注入模块

实现认证中间件和依赖函数，包括JWT令牌验证和当前用户获取。

需求引用:
    - 需求1.3: 未提供有效JWT令牌时返回401未授权错误
"""

from typing import Optional
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import verify_access_token
from app.models.user import User
from app.repositories.user_repository import UserRepository


# HTTP Bearer认证方案
# auto_error=False: 手动处理认证错误以返回正确的401状态码
security = HTTPBearer(auto_error=False)


def get_token_from_header(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> str:
    """
    从请求头中提取JWT令牌
    
    使用FastAPI的HTTPBearer安全方案自动从Authorization头提取令牌。
    
    Args:
        credentials: HTTP Bearer认证凭证
    
    Returns:
        str: JWT令牌字符串
    
    Raises:
        HTTPException 401: 未提供认证令牌
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未提供认证令牌",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return credentials.credentials


def get_current_user_id(
    token: str = Depends(get_token_from_header)
) -> int:
    """
    验证JWT令牌并返回当前用户ID
    
    验证流程:
    1. 验证JWT签名和过期时间
    2. 验证令牌类型为access
    3. 检查令牌是否在黑名单中
    
    Args:
        token: JWT访问令牌
    
    Returns:
        int: 当前用户ID
    
    Raises:
        HTTPException 401: 令牌无效、已过期或已被撤销
    
    需求引用:
        - 需求1.3: 未提供有效JWT令牌时返回401未授权错误
    """
    # verify_access_token 已包含黑名单检查
    payload = verify_access_token(token)
    
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="令牌无效或已过期",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    try:
        user_id = int(payload["sub"])
    except (KeyError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="令牌格式无效",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user_id


def get_current_user(
    user_id: int = Depends(get_current_user_id),
    request: Request = None,
    db: Session = Depends(get_db)
) -> User:
    """
    获取当前认证用户
    
    验证JWT令牌并从数据库获取完整的用户对象。
    同时验证用户是否存在且处于激活状态。
    
    使用方式:
        @app.get("/profile")
        def get_profile(current_user: User = Depends(get_current_user)):
            return {"username": current_user.username}
    
    Args:
        user_id: 从JWT令牌中提取的用户ID
        db: 数据库会话
    
    Returns:
        User: 当前认证用户对象
    
    Raises:
        HTTPException 401: 令牌无效或已过期
        HTTPException 404: 用户不存在
        HTTPException 403: 用户账户已停用
    
    需求引用:
        - 需求1.3: 未提供有效JWT令牌时返回401未授权错误
    """
    user_repo = UserRepository(db)
    user = user_repo.get_by_id(user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="用户账户已停用"
        )
    
    if request is not None:
        request.state.user = user

    return user


def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    获取当前激活用户（别名）
    
    与get_current_user功能相同，提供更明确的语义。
    
    Args:
        current_user: 当前用户对象
    
    Returns:
        User: 当前激活用户对象
    """
    return current_user


def get_optional_current_user(
    request: Request,
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    获取可选的当前用户
    
    如果提供了有效的JWT令牌，返回用户对象；
    如果未提供令牌或令牌无效，返回None而不是抛出异常。
    
    适用于同时支持认证和匿名访问的端点。
    
    使用方式:
        @app.get("/public")
        def public_endpoint(user: Optional[User] = Depends(get_optional_current_user)):
            if user:
                return {"message": f"Hello, {user.username}"}
            return {"message": "Hello, guest"}
    
    Args:
        request: HTTP请求对象
        db: 数据库会话
    
    Returns:
        Optional[User]: 当前用户对象或None
    """
    auth_header = request.headers.get("Authorization")
    
    if not auth_header or not auth_header.startswith("Bearer "):
        return None
    
    token = auth_header.split(" ")[1]
    payload = verify_access_token(token)
    
    if not payload:
        return None
    
    try:
        user_id = int(payload["sub"])
    except (KeyError, ValueError):
        return None
    
    user_repo = UserRepository(db)
    user = user_repo.get_by_id(user_id)
    
    if not user or not user.is_active:
        return None
    
    return user


def get_current_admin_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    获取当前管理员用户
    
    验证当前用户是否具有管理员权限。
    用于需要管理员权限的API端点。
    
    使用方式:
        @app.get("/admin/stats")
        def get_admin_stats(admin: User = Depends(get_current_admin_user)):
            return {"message": "Admin only"}
    
    Args:
        current_user: 当前认证用户对象
    
    Returns:
        User: 当前管理员用户对象
    
    Raises:
        HTTPException 403: 用户不是管理员
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限"
        )
    
    return current_user

# 导出
__all__ = [
    # 依赖函数
    'get_token_from_header',
    'get_current_user_id',
    'get_current_user',
    'get_current_active_user',
    'get_optional_current_user',
    'get_current_admin_user',
    # 安全方案
    'security',
]
