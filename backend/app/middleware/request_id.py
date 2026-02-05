"""
请求ID中间件

为每个请求生成唯一的追踪ID，用于日志记录和错误追踪。
请求ID会添加到响应头中，并存储在request.state中供其他中间件和处理器使用。
"""
import logging
import uuid
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    请求ID中间件

    为每个HTTP请求生成唯一的追踪ID，并将其：
    1. 存储在request.state.request_id中
    2. 添加到响应头X-Request-ID中
    3. 用于日志记录
    """

    def __init__(self, app, header_name: str = "X-Request-ID"):
        """
        初始化请求ID中间件

        Args:
            app: FastAPI应用实例
            header_name: 响应头名称，默认为X-Request-ID
        """
        super().__init__(app)
        self.header_name = header_name

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        处理请求并生成请求ID

        Args:
            request: FastAPI请求对象
            call_next: 下一个中间件或路由处理器

        Returns:
            响应对象
        """
        # 检查请求头中是否已有请求ID（用于分布式追踪）
        request_id = request.headers.get(self.header_name)

        # 如果没有，生成新的UUID
        if not request_id:
            request_id = str(uuid.uuid4())

        # 将请求ID存储到request.state中，供其他中间件和处理器使用
        request.state.request_id = request_id

        # 记录请求开始日志
        logger.info(
            f"Request started: {request.method} {request.url.path} "
            f"[request_id={request_id}]"
        )

        try:
            # 调用下一个中间件或路由处理器
            response = await call_next(request)

            # 将请求ID添加到响应头
            response.headers[self.header_name] = request_id

            # 记录请求完成日志
            logger.info(
                f"Request completed: {request.method} {request.url.path} "
                f"[request_id={request_id}, status={response.status_code}]"
            )

            return response

        except Exception as exc:
            # 记录异常日志
            logger.error(
                f"Request failed: {request.method} {request.url.path} "
                f"[request_id={request_id}] - {type(exc).__name__}: {str(exc)}"
            )
            # 重新抛出异常，让异常处理器处理
            raise


def register_request_id_middleware(app):
    """
    注册请求ID中间件到FastAPI应用

    Args:
        app: FastAPI应用实例
    """
    app.add_middleware(RequestIDMiddleware)
    logger.info("请求ID中间件已注册")


# 导出常用功能
__all__ = [
    "RequestIDMiddleware",
    "register_request_id_middleware",
]
