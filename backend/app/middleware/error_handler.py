"""
错误处理中间件

提供统一的异常处理和错误响应格式
"""
from enum import Enum
from typing import Optional, Any, Dict
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import logging
import traceback

logger = logging.getLogger(__name__)


class ErrorCode(str, Enum):
    """错误码枚举"""
    
    # 认证错误 (1xxx)
    INVALID_CREDENTIALS = "1001"
    TOKEN_EXPIRED = "1002"
    TOKEN_INVALID = "1003"
    USER_NOT_FOUND = "1004"
    USER_ALREADY_EXISTS = "1005"
    ACCOUNT_LOCKED = "1006"
    PERMISSION_DENIED = "1007"
    
    # 业务错误 (2xxx)
    CONVERSATION_NOT_FOUND = "2001"
    MESSAGE_SEND_FAILED = "2002"
    KNOWLEDGE_BASE_NOT_FOUND = "2003"
    DOCUMENT_UPLOAD_FAILED = "2004"
    DOCUMENT_PROCESS_FAILED = "2005"
    AGENT_EXECUTION_FAILED = "2006"
    INVALID_FILE_TYPE = "2007"
    FILE_TOO_LARGE = "2008"
    QUOTA_EXCEEDED = "2009"
    RESOURCE_NOT_FOUND = "2010"
    
    # 系统错误 (3xxx)
    DATABASE_ERROR = "3001"
    REDIS_ERROR = "3002"
    VECTOR_DB_ERROR = "3003"
    LLM_API_ERROR = "3004"
    INTERNAL_SERVER_ERROR = "3005"
    SERVICE_UNAVAILABLE = "3006"
    
    # 权限错误 (4xxx)
    RESOURCE_NOT_OWNED = "4001"
    INSUFFICIENT_PERMISSIONS = "4002"
    
    # 验证错误 (5xxx)
    VALIDATION_ERROR = "5001"
    INVALID_PARAMETER = "5002"
    MISSING_PARAMETER = "5003"


class AppException(Exception):
    """应用自定义异常类"""
    
    def __init__(
        self,
        error_code: ErrorCode,
        message: str,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        初始化应用异常
        
        Args:
            error_code: 错误码
            message: 错误消息
            status_code: HTTP状态码
            details: 额外的错误详情
        """
        self.error_code = error_code
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)
    
    def to_dict(self, request_id: Optional[str] = None) -> Dict[str, Any]:
        """
        转换为字典格式
        
        Args:
            request_id: 请求追踪ID
            
        Returns:
            错误响应字典
        """
        error_response = {
            "error_code": self.error_code.value,
            "message": self.message,
            "status_code": self.status_code
        }
        
        if self.details:
            error_response["details"] = self.details
        
        if request_id:
            error_response["request_id"] = request_id
        
        return error_response


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    """
    处理应用自定义异常
    
    Args:
        request: FastAPI请求对象
        exc: 应用异常实例
        
    Returns:
        JSON响应
    """
    request_id = getattr(request.state, "request_id", None)
    
    # 记录错误日志
    logger.error(
        f"AppException: {exc.error_code.value} - {exc.message} "
        f"[request_id={request_id}, path={request.url.path}]"
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.to_dict(request_id=request_id)
    )


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """
    处理HTTP异常
    
    Args:
        request: FastAPI请求对象
        exc: HTTP异常实例
        
    Returns:
        JSON响应
    """
    request_id = getattr(request.state, "request_id", None)
    
    # 记录错误日志
    logger.warning(
        f"HTTPException: {exc.status_code} - {exc.detail} "
        f"[request_id={request_id}, path={request.url.path}]"
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error_code": str(exc.status_code),
            "message": exc.detail,
            "status_code": exc.status_code,
            "request_id": request_id
        }
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """
    处理请求验证异常
    
    Args:
        request: FastAPI请求对象
        exc: 验证异常实例
        
    Returns:
        JSON响应
    """
    request_id = getattr(request.state, "request_id", None)
    
    # 提取验证错误详情
    errors = []
    for error in exc.errors():
        errors.append({
            "field": ".".join(str(loc) for loc in error["loc"]),
            "message": error["msg"],
            "type": error["type"]
        })
    
    # 记录错误日志
    logger.warning(
        f"ValidationError: {len(errors)} validation errors "
        f"[request_id={request_id}, path={request.url.path}]"
    )
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error_code": ErrorCode.VALIDATION_ERROR.value,
            "message": "请求参数验证失败",
            "status_code": status.HTTP_422_UNPROCESSABLE_ENTITY,
            "details": {"errors": errors},
            "request_id": request_id
        }
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    处理未捕获的通用异常
    
    Args:
        request: FastAPI请求对象
        exc: 异常实例
        
    Returns:
        JSON响应
    """
    request_id = getattr(request.state, "request_id", None)
    
    # 记录详细的错误日志和堆栈跟踪
    logger.error(
        f"Unhandled Exception: {type(exc).__name__} - {str(exc)} "
        f"[request_id={request_id}, path={request.url.path}]\n"
        f"Traceback:\n{traceback.format_exc()}"
    )
    
    # 生产环境不暴露详细错误信息
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error_code": ErrorCode.INTERNAL_SERVER_ERROR.value,
            "message": "服务器内部错误，请稍后重试",
            "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
            "request_id": request_id
        }
    )


def register_exception_handlers(app):
    """
    注册所有异常处理器到FastAPI应用
    
    Args:
        app: FastAPI应用实例
    """
    app.add_exception_handler(AppException, app_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, general_exception_handler)
    
    logger.info("异常处理器已注册")
