"""
通义千问LLM配置模块

配置和管理通义千问大语言模型实例，提供LLM调用的重试机制。
支持流式和非流式输出模式。
"""

import logging
from typing import Any, AsyncGenerator, Dict, List, Optional

from langchain_community.llms import Tongyi
from langchain_core.callbacks import CallbackManagerForLLMRun
from langchain_core.language_models.llms import LLM
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
)

from app.config import settings

logger = logging.getLogger(__name__)


# 定义可重试的异常类型
RETRYABLE_EXCEPTIONS = (
    ConnectionError,
    TimeoutError,
    Exception,  # 捕获dashscope API的通用异常
)


class TongyiLLM:
    """
    通义千问LLM封装类
    
    提供统一的LLM调用接口，支持：
    - 流式和非流式输出
    - 自动重试机制（3次，指数退避）
    - 自定义模型参数
    
    使用方式:
        from app.core.llm import get_llm, get_streaming_llm
        
        # 获取非流式LLM实例
        llm = get_llm()
        response = await llm.ainvoke("你好")
        
        # 获取流式LLM实例
        streaming_llm = get_streaming_llm()
        async for chunk in streaming_llm.astream("你好"):
            print(chunk)
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        streaming: bool = False,
    ):
        """
        初始化通义千问LLM实例
        
        Args:
            api_key: DashScope API密钥，默认从配置读取
            model_name: 模型名称，默认从配置读取
            temperature: 温度参数，控制输出随机性
            max_tokens: 最大输出token数
            streaming: 是否启用流式输出
        """
        self.api_key = api_key or settings.tongyi.dashscope_api_key
        self.model_name = model_name or settings.tongyi.tongyi_model_name
        self.temperature = temperature if temperature is not None else settings.tongyi.tongyi_temperature
        self.max_tokens = max_tokens or settings.tongyi.tongyi_max_tokens
        self.streaming = streaming
        
        self._llm: Optional[Tongyi] = None
    
    @property
    def llm(self) -> Tongyi:
        """
        获取或创建LLM实例（懒加载）
        
        Returns:
            Tongyi: 通义千问LLM实例
        """
        if self._llm is None:
            self._llm = self._create_llm()
        return self._llm
    
    def _create_llm(self) -> Tongyi:
        """
        创建通义千问LLM实例
        
        Returns:
            Tongyi: 配置好的LLM实例
        """
        logger.info(
            f"创建通义千问LLM实例: model={self.model_name}, "
            f"temperature={self.temperature}, max_tokens={self.max_tokens}, "
            f"streaming={self.streaming}"
        )
        
        return Tongyi(
            dashscope_api_key=self.api_key,
            model_name=self.model_name,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            streaming=self.streaming,
        )
    
    def update_params(
        self,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> None:
        """
        更新LLM参数
        
        Args:
            temperature: 新的温度参数
            max_tokens: 新的最大token数
        """
        if temperature is not None:
            self.temperature = temperature
        if max_tokens is not None:
            self.max_tokens = max_tokens
        
        # 重新创建LLM实例以应用新参数
        self._llm = None
        logger.info(f"LLM参数已更新: temperature={self.temperature}, max_tokens={self.max_tokens}")


# 创建重试装饰器
def create_retry_decorator(max_attempts: int = 3, min_wait: int = 2, max_wait: int = 10):
    """
    创建LLM调用重试装饰器
    
    Args:
        max_attempts: 最大重试次数
        min_wait: 最小等待时间（秒）
        max_wait: 最大等待时间（秒）
    
    Returns:
        重试装饰器
    """
    return retry(
        stop=stop_after_attempt(max_attempts),
        wait=wait_exponential(multiplier=1, min=min_wait, max=max_wait),
        retry=retry_if_exception_type(RETRYABLE_EXCEPTIONS),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True,
    )


# 默认重试装饰器（3次，指数退避：2秒、4秒、8秒）
llm_retry = create_retry_decorator(max_attempts=3, min_wait=2, max_wait=10)


@llm_retry
async def invoke_llm(
    prompt: str,
    llm: Optional[TongyiLLM] = None,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
) -> str:
    """
    调用LLM生成响应（带重试机制）
    
    Args:
        prompt: 输入提示词
        llm: TongyiLLM实例，默认使用全局实例
        temperature: 温度参数（可选，覆盖默认值）
        max_tokens: 最大token数（可选，覆盖默认值）
    
    Returns:
        str: LLM生成的响应文本
    
    Raises:
        Exception: 重试3次后仍然失败时抛出异常
    """
    if llm is None:
        llm = get_llm(temperature=temperature, max_tokens=max_tokens)
    
    logger.debug(f"调用LLM: prompt长度={len(prompt)}")
    
    try:
        response = await llm.llm.ainvoke(prompt)
        logger.debug(f"LLM响应成功: 响应长度={len(response)}")
        return response
    except Exception as e:
        logger.error(f"LLM调用失败: {str(e)}")
        raise


@llm_retry
def invoke_llm_sync(
    prompt: str,
    llm: Optional[TongyiLLM] = None,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
) -> str:
    """
    同步调用LLM生成响应（带重试机制）
    
    Args:
        prompt: 输入提示词
        llm: TongyiLLM实例，默认使用全局实例
        temperature: 温度参数（可选，覆盖默认值）
        max_tokens: 最大token数（可选，覆盖默认值）
    
    Returns:
        str: LLM生成的响应文本
    
    Raises:
        Exception: 重试3次后仍然失败时抛出异常
    """
    if llm is None:
        llm = get_llm(temperature=temperature, max_tokens=max_tokens)
    
    logger.debug(f"同步调用LLM: prompt长度={len(prompt)}")
    
    try:
        response = llm.llm.invoke(prompt)
        logger.debug(f"LLM响应成功: 响应长度={len(response)}")
        return response
    except Exception as e:
        logger.error(f"LLM调用失败: {str(e)}")
        raise


async def stream_llm(
    prompt: str,
    llm: Optional[TongyiLLM] = None,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
) -> AsyncGenerator[str, None]:
    """
    流式调用LLM生成响应
    
    Args:
        prompt: 输入提示词
        llm: TongyiLLM实例，默认使用流式LLM实例
        temperature: 温度参数（可选，覆盖默认值）
        max_tokens: 最大token数（可选，覆盖默认值）
    
    Yields:
        str: LLM生成的响应文本片段
    
    Raises:
        Exception: 调用失败时抛出异常
    """
    if llm is None:
        llm = get_streaming_llm(temperature=temperature, max_tokens=max_tokens)
    
    logger.debug(f"流式调用LLM: prompt长度={len(prompt)}")
    
    try:
        async for chunk in llm.llm.astream(prompt):
            yield chunk
        logger.debug("流式LLM响应完成")
    except Exception as e:
        logger.error(f"流式LLM调用失败: {str(e)}")
        raise


# 全局LLM实例缓存
_llm_instances: Dict[str, TongyiLLM] = {}


def get_llm(
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
    model_name: Optional[str] = None,
) -> TongyiLLM:
    """
    获取非流式LLM实例
    
    Args:
        temperature: 温度参数
        max_tokens: 最大token数
        model_name: 模型名称
    
    Returns:
        TongyiLLM: 配置好的LLM实例
    """
    # 使用参数生成缓存键
    cache_key = f"llm_{model_name or 'default'}_{temperature}_{max_tokens}_False"
    
    if cache_key not in _llm_instances:
        _llm_instances[cache_key] = TongyiLLM(
            model_name=model_name,
            temperature=temperature,
            max_tokens=max_tokens,
            streaming=False,
        )
    
    return _llm_instances[cache_key]


def get_streaming_llm(
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
    model_name: Optional[str] = None,
) -> TongyiLLM:
    """
    获取流式LLM实例
    
    Args:
        temperature: 温度参数
        max_tokens: 最大token数
        model_name: 模型名称
    
    Returns:
        TongyiLLM: 配置好的流式LLM实例
    """
    # 使用参数生成缓存键
    cache_key = f"llm_{model_name or 'default'}_{temperature}_{max_tokens}_True"
    
    if cache_key not in _llm_instances:
        _llm_instances[cache_key] = TongyiLLM(
            model_name=model_name,
            temperature=temperature,
            max_tokens=max_tokens,
            streaming=True,
        )
    
    return _llm_instances[cache_key]


def clear_llm_cache() -> None:
    """
    清除LLM实例缓存
    
    用于在配置更新后重新创建LLM实例
    """
    global _llm_instances
    _llm_instances.clear()
    logger.info("LLM实例缓存已清除")


def get_llm_config() -> Dict[str, Any]:
    """
    获取当前LLM配置信息
    
    Returns:
        dict: LLM配置字典
    """
    return {
        "model_name": settings.tongyi.tongyi_model_name,
        "temperature": settings.tongyi.tongyi_temperature,
        "max_tokens": settings.tongyi.tongyi_max_tokens,
        "embedding_model": settings.tongyi.embedding_model,
    }


# 导出
__all__ = [
    'TongyiLLM',
    'get_llm',
    'get_streaming_llm',
    'invoke_llm',
    'invoke_llm_sync',
    'stream_llm',
    'clear_llm_cache',
    'get_llm_config',
    'llm_retry',
    'create_retry_decorator',
]
