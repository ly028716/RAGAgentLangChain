"""
Prometheus监控中间件

提供Prometheus指标收集功能，包括请求计数、请求时长、LLM调用统计等。

需求引用:
    - 需求8.1: 记录API调用和token消耗
"""

import time
from typing import Callable

from fastapi import Request, Response
from prometheus_client import Counter, Histogram, Gauge
from starlette.middleware.base import BaseHTTPMiddleware

from app.utils.logger import get_logger


logger = get_logger(__name__)


# ==================== Prometheus指标定义 ====================

# 1. 请求计数器
request_count = Counter(
    'http_requests_total',
    'Total number of HTTP requests',
    ['method', 'endpoint', 'status_code']
)

# 2. 请求时长直方图
request_duration = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint'],
    buckets=(0.01, 0.05, 0.1, 0.5, 1.0, 2.5, 5.0, 10.0)
)

# 3. LLM调用计数器
llm_call_count = Counter(
    'llm_calls_total',
    'Total number of LLM API calls',
    ['model', 'api_type', 'status']
)

# 4. LLM Token使用量计数器
llm_token_usage = Counter(
    'llm_tokens_total',
    'Total number of tokens used in LLM calls',
    ['model', 'token_type']  # token_type: prompt, completion, total
)

# 5. 活跃请求数量（Gauge）
active_requests = Gauge(
    'http_requests_active',
    'Number of active HTTP requests',
    ['method', 'endpoint']
)

# 6. 数据库连接池指标
db_connections = Gauge(
    'db_connections_active',
    'Number of active database connections'
)

# 7. Redis连接状态
redis_connection_status = Gauge(
    'redis_connection_status',
    'Redis connection status (1=connected, 0=disconnected)'
)


class PrometheusMiddleware(BaseHTTPMiddleware):
    """
    Prometheus监控中间件
    
    功能:
        - 记录每个HTTP请求的方法、路径、状态码
        - 记录请求处理时长
        - 跟踪活跃请求数量
        - 排除/metrics端点本身，避免递归统计
    
    需求引用:
        - 需求8.1: 记录API调用统计
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        处理HTTP请求并收集指标
        
        Args:
            request: FastAPI请求对象
            call_next: 下一个中间件或路由处理器
        
        Returns:
            Response: HTTP响应对象
        """
        # 排除/metrics端点，避免递归统计
        if request.url.path == "/metrics":
            return await call_next(request)
        
        # 获取请求信息
        method = request.method
        endpoint = request.url.path
        
        # 增加活跃请求计数
        active_requests.labels(method=method, endpoint=endpoint).inc()
        
        # 记录开始时间
        start_time = time.time()
        
        try:
            # 处理请求
            response = await call_next(request)
            
            # 记录状态码
            status_code = response.status_code
            
            # 记录请求计数
            request_count.labels(
                method=method,
                endpoint=endpoint,
                status_code=status_code
            ).inc()
            
            # 记录请求时长
            duration = time.time() - start_time
            request_duration.labels(
                method=method,
                endpoint=endpoint
            ).observe(duration)
            
            return response
            
        except Exception as e:
            # 记录异常请求
            request_count.labels(
                method=method,
                endpoint=endpoint,
                status_code=500
            ).inc()
            
            duration = time.time() - start_time
            request_duration.labels(
                method=method,
                endpoint=endpoint
            ).observe(duration)
            
            logger.error(f"请求处理异常: {method} {endpoint} - {str(e)}")
            raise
            
        finally:
            # 减少活跃请求计数
            active_requests.labels(method=method, endpoint=endpoint).dec()


def record_llm_call(
    model: str,
    api_type: str,
    status: str,
    prompt_tokens: int = 0,
    completion_tokens: int = 0
) -> None:
    """
    记录LLM调用指标
    
    Args:
        model: 模型名称（如 "qwen-turbo"）
        api_type: API类型（如 "chat", "rag", "agent"）
        status: 调用状态（"success", "error"）
        prompt_tokens: 提示词token数量
        completion_tokens: 生成内容token数量
    
    需求引用:
        - 需求8.1: 记录LLM调用和token消耗
    
    示例:
        >>> record_llm_call("qwen-turbo", "chat", "success", 100, 200)
    """
    # 记录LLM调用次数
    llm_call_count.labels(
        model=model,
        api_type=api_type,
        status=status
    ).inc()
    
    # 记录token使用量
    if prompt_tokens > 0:
        llm_token_usage.labels(
            model=model,
            token_type="prompt"
        ).inc(prompt_tokens)
    
    if completion_tokens > 0:
        llm_token_usage.labels(
            model=model,
            token_type="completion"
        ).inc(completion_tokens)
    
    # 记录总token数
    total_tokens = prompt_tokens + completion_tokens
    if total_tokens > 0:
        llm_token_usage.labels(
            model=model,
            token_type="total"
        ).inc(total_tokens)
    
    logger.debug(
        f"LLM调用记录: model={model}, api_type={api_type}, "
        f"status={status}, prompt_tokens={prompt_tokens}, "
        f"completion_tokens={completion_tokens}"
    )


def update_db_connections(count: int) -> None:
    """
    更新数据库连接池指标
    
    Args:
        count: 当前活跃连接数
    """
    db_connections.set(count)


def update_redis_status(connected: bool) -> None:
    """
    更新Redis连接状态
    
    Args:
        connected: 是否已连接
    """
    redis_connection_status.set(1 if connected else 0)
