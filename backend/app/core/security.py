"""
安全模块

实现密码加密、JWT令牌生成和验证、令牌黑名单检查等安全功能。
需求: 需求1.2, 需求1.3, 需求9.1
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Optional

import bcrypt
from jose import JWTError, jwt

from app.config import settings
from app.core.redis import RedisKeys, get_redis_client

logger = logging.getLogger(__name__)


# bcrypt工作因子（从配置读取，默认12）
BCRYPT_ROUNDS = settings.security.bcrypt_rounds


# JWT令牌类型常量
ACCESS_TOKEN_TYPE = "access"
REFRESH_TOKEN_TYPE = "refresh"


def hash_password(password: str) -> str:
    """
    对密码进行哈希加密

    使用bcrypt算法，工作因子为12，确保密码安全存储。

    Args:
        password: 明文密码

    Returns:
        str: 加密后的密码哈希值

    Example:
        >>> hashed = hash_password("MySecurePassword123")
        >>> print(hashed)  # $2b$12$...
    """
    # 将密码编码为bytes
    password_bytes = password.encode("utf-8")
    # 生成salt并哈希密码
    salt = bcrypt.gensalt(rounds=BCRYPT_ROUNDS)
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    验证密码是否正确

    将明文密码与存储的哈希值进行比较。

    Args:
        plain_password: 明文密码
        hashed_password: 存储的密码哈希值

    Returns:
        bool: 密码是否匹配

    Example:
        >>> hashed = hash_password("MyPassword123")
        >>> verify_password("MyPassword123", hashed)
        True
        >>> verify_password("WrongPassword", hashed)
        False
    """
    try:
        password_bytes = plain_password.encode("utf-8")
        hashed_bytes = hashed_password.encode("utf-8")
        return bcrypt.checkpw(password_bytes, hashed_bytes)
    except Exception:
        return False


def create_access_token(
    subject: int,
    username: str,
    expires_delta: Optional[timedelta] = None,
    additional_claims: Optional[dict] = None,
) -> str:
    """
    创建访问令牌（Access Token）

    生成包含用户信息的JWT访问令牌，用于API认证。
    默认有效期为7天（从配置读取）。

    Args:
        subject: 用户ID（作为令牌主题）
        username: 用户名
        expires_delta: 自定义过期时间，默认使用配置值
        additional_claims: 额外的JWT声明

    Returns:
        str: JWT访问令牌

    Example:
        >>> token = create_access_token(subject=1, username="testuser")
        >>> print(token)  # eyJ0eXAiOiJKV1QiLCJhbGc...
    """
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            days=settings.jwt.access_token_expire_days
        )

    to_encode = {
        "sub": str(subject),  # 用户ID
        "username": username,
        "type": ACCESS_TOKEN_TYPE,
        "exp": expire,
        "iat": datetime.utcnow(),
    }

    if additional_claims:
        to_encode.update(additional_claims)

    encoded_jwt = jwt.encode(
        to_encode,
        settings.jwt.secret_key,
        algorithm=settings.jwt.algorithm,
    )
    return encoded_jwt


def create_refresh_token(
    subject: int,
    username: str,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """
    创建刷新令牌（Refresh Token）

    生成用于刷新访问令牌的JWT刷新令牌。
    默认有效期为30天（从配置读取）。

    Args:
        subject: 用户ID（作为令牌主题）
        username: 用户名
        expires_delta: 自定义过期时间，默认使用配置值

    Returns:
        str: JWT刷新令牌

    Example:
        >>> refresh_token = create_refresh_token(subject=1, username="testuser")
    """
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            days=settings.jwt.refresh_token_expire_days
        )

    to_encode = {
        "sub": str(subject),
        "username": username,
        "type": REFRESH_TOKEN_TYPE,
        "exp": expire,
        "iat": datetime.utcnow(),
    }

    encoded_jwt = jwt.encode(
        to_encode,
        settings.jwt.secret_key,
        algorithm=settings.jwt.algorithm,
    )
    return encoded_jwt


def create_token_pair(user_id: int, username: str) -> dict:
    """
    创建访问令牌和刷新令牌对

    同时生成访问令牌和刷新令牌，用于登录响应。

    Args:
        user_id: 用户ID
        username: 用户名

    Returns:
        dict: 包含access_token, refresh_token, token_type, expires_in的字典

    Example:
        >>> tokens = create_token_pair(user_id=1, username="testuser")
        >>> print(tokens["access_token"])
        >>> print(tokens["refresh_token"])
    """
    access_token = create_access_token(subject=user_id, username=username)
    refresh_token = create_refresh_token(subject=user_id, username=username)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": settings.jwt.access_token_expire_days * 24 * 60 * 60,  # 秒
    }


def verify_token(token: str, token_type: str = ACCESS_TOKEN_TYPE) -> Optional[dict]:
    """
    验证JWT令牌

    解码并验证JWT令牌的有效性，包括签名、过期时间和令牌类型。

    Args:
        token: JWT令牌字符串
        token_type: 期望的令牌类型（access或refresh）

    Returns:
        Optional[dict]: 令牌载荷（payload），验证失败返回None

    Example:
        >>> payload = verify_token(token, token_type="access")
        >>> if payload:
        ...     user_id = payload["sub"]
        ...     username = payload["username"]
    """
    try:
        payload = jwt.decode(
            token,
            settings.jwt.secret_key,
            algorithms=[settings.jwt.algorithm],
        )

        # 验证令牌类型
        if payload.get("type") != token_type:
            return None

        # 验证必要字段
        if not payload.get("sub") or not payload.get("username"):
            return None

        return payload
    except JWTError:
        return None


def decode_token(token: str) -> Optional[dict]:
    """
    解码JWT令牌（不验证类型）

    仅解码令牌，不检查令牌类型。用于需要获取令牌信息但不关心类型的场景。

    Args:
        token: JWT令牌字符串

    Returns:
        Optional[dict]: 令牌载荷（payload），解码失败返回None
    """
    try:
        payload = jwt.decode(
            token,
            settings.jwt.secret_key,
            algorithms=[settings.jwt.algorithm],
        )
        return payload
    except JWTError:
        return None


def get_token_expiry(token: str) -> Optional[datetime]:
    """
    获取令牌过期时间

    Args:
        token: JWT令牌字符串

    Returns:
        Optional[datetime]: 令牌过期时间，解码失败返回None
    """
    payload = decode_token(token)
    if payload and "exp" in payload:
        return datetime.fromtimestamp(payload["exp"])
    return None


# ============ 令牌黑名单功能（使用Redis） ============


def add_token_to_blacklist(token: str, expires_in: Optional[int] = None) -> bool:
    """
    将令牌添加到黑名单

    使用Redis存储已撤销的令牌，用于登出或令牌失效场景。
    黑名单条目会在令牌原本过期时间后自动删除。

    Args:
        token: 要加入黑名单的JWT令牌
        expires_in: 黑名单条目的过期时间（秒），默认使用令牌的剩余有效期

    Returns:
        bool: 是否成功添加到黑名单

    Example:
        >>> add_token_to_blacklist(access_token)
        True
    """
    try:
        redis_client = get_redis_client()

        # 计算过期时间
        if expires_in is None:
            expiry = get_token_expiry(token)
            if expiry:
                expires_in = int((expiry - datetime.utcnow()).total_seconds())
                if expires_in <= 0:
                    # 令牌已过期，无需加入黑名单
                    return True
            else:
                # 无法获取过期时间，使用默认值（7天）
                expires_in = settings.jwt.access_token_expire_days * 24 * 60 * 60

        # 使用令牌的哈希值作为键（避免键过长）
        key = RedisKeys.format_key(
            RedisKeys.USER_TOKEN_BLACKLIST, token=_hash_token_for_key(token)
        )

        # 设置黑名单条目，带过期时间
        redis_client.setex(key, expires_in, "1")
        return True
    except Exception as e:
        logger.error(f"添加令牌到黑名单失败: {e}")
        return False


def is_token_blacklisted(token: str) -> bool:
    """
    检查令牌是否在黑名单中

    验证令牌是否已被撤销。应在每次令牌验证时调用。

    Args:
        token: 要检查的JWT令牌

    Returns:
        bool: 令牌是否在黑名单中

    Example:
        >>> if is_token_blacklisted(token):
        ...     raise HTTPException(status_code=401, detail="令牌已失效")
    """
    try:
        redis_client = get_redis_client()

        key = RedisKeys.format_key(
            RedisKeys.USER_TOKEN_BLACKLIST, token=_hash_token_for_key(token)
        )

        return redis_client.exists(key) > 0
    except Exception as e:
        logger.error(f"检查令牌黑名单失败: {e}")
        # 出错时保守处理，认为令牌有效
        return False


def remove_token_from_blacklist(token: str) -> bool:
    """
    从黑名单中移除令牌

    Args:
        token: 要移除的JWT令牌

    Returns:
        bool: 是否成功移除
    """
    try:
        redis_client = get_redis_client()

        key = RedisKeys.format_key(
            RedisKeys.USER_TOKEN_BLACKLIST, token=_hash_token_for_key(token)
        )

        redis_client.delete(key)
        return True
    except Exception as e:
        logger.error(f"从黑名单移除令牌失败: {e}")
        return False


def _hash_token_for_key(token: str) -> str:
    """
    为Redis键生成令牌的哈希值

    使用令牌的最后32个字符作为键的一部分，
    避免完整令牌作为键导致键过长。

    Args:
        token: JWT令牌

    Returns:
        str: 令牌的哈希标识
    """
    import hashlib

    return hashlib.sha256(token.encode()).hexdigest()[:32]


# ============ 完整的令牌验证（包含黑名单检查） ============


def verify_access_token(token: str) -> Optional[dict]:
    """
    验证访问令牌（包含黑名单检查）

    完整的访问令牌验证流程：
    1. 验证JWT签名和过期时间
    2. 验证令牌类型为access
    3. 检查令牌是否在黑名单中

    Args:
        token: JWT访问令牌

    Returns:
        Optional[dict]: 令牌载荷，验证失败返回None

    Example:
        >>> payload = verify_access_token(token)
        >>> if payload:
        ...     user_id = int(payload["sub"])
    """
    # 先检查黑名单
    if is_token_blacklisted(token):
        return None

    # 验证令牌
    return verify_token(token, token_type=ACCESS_TOKEN_TYPE)


def verify_refresh_token(token: str) -> Optional[dict]:
    """
    验证刷新令牌（包含黑名单检查）

    完整的刷新令牌验证流程：
    1. 验证JWT签名和过期时间
    2. 验证令牌类型为refresh
    3. 检查令牌是否在黑名单中

    Args:
        token: JWT刷新令牌

    Returns:
        Optional[dict]: 令牌载荷，验证失败返回None
    """
    # 先检查黑名单
    if is_token_blacklisted(token):
        return None

    # 验证令牌
    return verify_token(token, token_type=REFRESH_TOKEN_TYPE)


# 导出
__all__ = [
    # 密码相关
    "hash_password",
    "verify_password",
    # 令牌创建
    "create_access_token",
    "create_refresh_token",
    "create_token_pair",
    # 令牌验证
    "verify_token",
    "verify_access_token",
    "verify_refresh_token",
    "decode_token",
    "get_token_expiry",
    # 黑名单管理
    "add_token_to_blacklist",
    "is_token_blacklisted",
    "remove_token_from_blacklist",
    # 常量
    "ACCESS_TOKEN_TYPE",
    "REFRESH_TOKEN_TYPE",
]
