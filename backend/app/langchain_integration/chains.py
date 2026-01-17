"""
LangChain对话链模块

实现对话管理器，使用ConversationBufferMemory维护上下文，
支持流式和非流式对话响应。

需求引用:
    - 需求2.2: 调用通义千问API生成回复
    - 需求2.3: 使用SSE协议实时推送AI生成的文本片段，首字响应时间小于3秒
"""

import logging
from typing import AsyncGenerator, Dict, List, Optional, Any

from langchain.chains import ConversationChain
from langchain.memory import ConversationBufferMemory
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain.prompts import PromptTemplate

from app.core.llm import get_llm, get_streaming_llm, TongyiLLM
from app.config import settings

logger = logging.getLogger(__name__)


# 默认对话提示模板
DEFAULT_CONVERSATION_TEMPLATE = """你是一个智能AI助手，能够帮助用户解答各种问题。请用中文回答用户的问题，保持友好、专业的态度。

当前对话历史:
{history}

用户: {input}
AI助手:"""


class ChatConfig:
    """
    对话配置类
    
    用于配置对话的模型参数。
    """
    
    def __init__(
        self,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        mode: str = "normal"
    ):
        """
        初始化对话配置
        
        Args:
            temperature: 温度参数，控制输出随机性 (0.0-2.0)
            max_tokens: 最大输出token数
            mode: 对话模式 (normal/professional/creative)
        """
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.mode = mode
        
        # 根据模式调整参数
        if mode == "professional":
            self.temperature = min(temperature, 0.3)
        elif mode == "creative":
            self.temperature = max(temperature, 1.0)


class ConversationManager:
    """
    对话管理器类
    
    管理对话上下文，提供流式和非流式对话功能。
    使用ConversationBufferMemory维护对话历史。
    
    使用方式:
        manager = ConversationManager()
        
        # 非流式对话
        response, tokens = await manager.chat(
            conversation_id=1,
            message="你好",
            config=ChatConfig()
        )
        
        # 流式对话
        async for chunk in manager.stream_chat(
            conversation_id=1,
            message="你好",
            config=ChatConfig()
        ):
            print(chunk, end="")
    """
    
    def __init__(self):
        """初始化对话管理器"""
        # 对话记忆存储: conversation_id -> ConversationBufferMemory
        self._memories: Dict[int, ConversationBufferMemory] = {}
        
        # 对话提示模板
        self._prompt_template = PromptTemplate(
            input_variables=["history", "input"],
            template=DEFAULT_CONVERSATION_TEMPLATE
        )
    
    def get_or_create_memory(
        self,
        conversation_id: int,
        history: Optional[List[Dict[str, str]]] = None
    ) -> ConversationBufferMemory:
        """
        获取或创建对话记忆
        
        Args:
            conversation_id: 对话ID
            history: 历史消息列表，用于初始化记忆
        
        Returns:
            ConversationBufferMemory: 对话记忆对象
        """
        if conversation_id not in self._memories:
            memory = ConversationBufferMemory(
                return_messages=True,
                human_prefix="用户",
                ai_prefix="AI助手"
            )
            
            # 如果提供了历史消息，加载到记忆中
            if history:
                for msg in history:
                    if msg.get("role") == "USER":
                        memory.chat_memory.add_user_message(msg.get("content", ""))
                    elif msg.get("role") == "ASSISTANT":
                        memory.chat_memory.add_ai_message(msg.get("content", ""))
            
            self._memories[conversation_id] = memory
        
        return self._memories[conversation_id]
    
    def load_history(
        self,
        conversation_id: int,
        messages: List[Dict[str, str]]
    ) -> None:
        """
        加载对话历史到记忆
        
        Args:
            conversation_id: 对话ID
            messages: 消息列表，每个消息包含role和content
        """
        memory = self.get_or_create_memory(conversation_id)
        
        # 清除现有记忆
        memory.clear()
        
        # 加载新的历史
        for msg in messages:
            role = msg.get("role", "")
            content = msg.get("content", "")

            if role == "USER":
                memory.chat_memory.add_user_message(content)
            elif role == "ASSISTANT":
                memory.chat_memory.add_ai_message(content)
    
    def clear_memory(self, conversation_id: int) -> None:
        """
        清除对话记忆
        
        Args:
            conversation_id: 对话ID
        """
        if conversation_id in self._memories:
            self._memories[conversation_id].clear()
            del self._memories[conversation_id]
    
    def _get_llm(
        self,
        config: ChatConfig,
        streaming: bool = False
    ) -> TongyiLLM:
        """
        根据配置获取LLM实例
        
        Args:
            config: 对话配置
            streaming: 是否流式输出
        
        Returns:
            TongyiLLM: LLM实例
        """
        if streaming:
            return get_streaming_llm(
                temperature=config.temperature,
                max_tokens=config.max_tokens
            )
        return get_llm(
            temperature=config.temperature,
            max_tokens=config.max_tokens
        )
    
    def _build_prompt(
        self,
        message: str,
        memory: ConversationBufferMemory
    ) -> str:
        """
        构建对话提示
        
        Args:
            message: 用户消息
            memory: 对话记忆
        
        Returns:
            str: 完整的提示文本
        """
        # 获取历史对话
        history = memory.load_memory_variables({})
        history_str = ""
        
        if "history" in history:
            messages = history["history"]
            for msg in messages:
                if isinstance(msg, HumanMessage):
                    history_str += f"用户: {msg.content}\n"
                elif isinstance(msg, AIMessage):
                    history_str += f"AI助手: {msg.content}\n"
        
        return self._prompt_template.format(
            history=history_str.strip(),
            input=message
        )
    
    async def chat(
        self,
        conversation_id: int,
        message: str,
        config: Optional[ChatConfig] = None,
        history: Optional[List[Dict[str, str]]] = None
    ) -> tuple[str, int]:
        """
        非流式对话
        
        Args:
            conversation_id: 对话ID
            message: 用户消息
            config: 对话配置
            history: 历史消息列表（可选，用于初始化记忆）
        
        Returns:
            tuple[str, int]: (AI回复内容, 估算的token数量)
        
        需求引用:
            - 需求2.2: 调用通义千问API生成回复
        """
        if config is None:
            config = ChatConfig()
        
        # 获取或创建记忆
        memory = self.get_or_create_memory(conversation_id, history)
        
        # 获取LLM实例
        llm = self._get_llm(config, streaming=False)
        
        # 构建提示
        prompt = self._build_prompt(message, memory)
        
        logger.debug(f"对话 {conversation_id}: 发送消息，prompt长度={len(prompt)}")
        
        try:
            # 调用LLM
            response = await llm.llm.ainvoke(prompt)
            
            # 更新记忆
            memory.chat_memory.add_user_message(message)
            memory.chat_memory.add_ai_message(response)
            
            # 估算token数量（简单估算：中文约2字符/token，英文约4字符/token）
            estimated_tokens = self._estimate_tokens(prompt + response)
            
            logger.debug(f"对话 {conversation_id}: 收到回复，长度={len(response)}, tokens≈{estimated_tokens}")
            
            return response, estimated_tokens
            
        except Exception as e:
            logger.error(f"对话 {conversation_id}: LLM调用失败 - {str(e)}")
            raise
    
    async def stream_chat(
        self,
        conversation_id: int,
        message: str,
        config: Optional[ChatConfig] = None,
        history: Optional[List[Dict[str, str]]] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        流式对话
        
        使用SSE协议实时推送AI生成的文本片段。
        
        Args:
            conversation_id: 对话ID
            message: 用户消息
            config: 对话配置
            history: 历史消息列表（可选，用于初始化记忆）
        
        Yields:
            Dict[str, Any]: 流式响应数据
                - type: "token" | "done" | "error"
                - content: 文本片段（type为token时）
                - tokens_used: 总token数（type为done时）
                - error: 错误信息（type为error时）
        
        需求引用:
            - 需求2.3: 使用SSE协议实时推送AI生成的文本片段，首字响应时间小于3秒
        """
        if config is None:
            config = ChatConfig()
        
        # 获取或创建记忆
        memory = self.get_or_create_memory(conversation_id, history)
        
        # 获取流式LLM实例
        llm = self._get_llm(config, streaming=True)
        
        # 构建提示
        prompt = self._build_prompt(message, memory)
        
        logger.debug(f"对话 {conversation_id}: 开始流式对话，prompt长度={len(prompt)}")
        
        full_response = ""
        
        try:
            # 流式调用LLM
            async for chunk in llm.llm.astream(prompt):
                full_response += chunk
                yield {
                    "type": "token",
                    "content": chunk
                }
            
            # 更新记忆
            memory.chat_memory.add_user_message(message)
            memory.chat_memory.add_ai_message(full_response)
            
            # 估算token数量
            estimated_tokens = self._estimate_tokens(prompt + full_response)
            
            logger.debug(f"对话 {conversation_id}: 流式对话完成，总长度={len(full_response)}, tokens≈{estimated_tokens}")
            
            yield {
                "type": "done",
                "content": full_response,
                "tokens_used": estimated_tokens
            }
            
        except Exception as e:
            logger.error(f"对话 {conversation_id}: 流式LLM调用失败 - {str(e)}")
            yield {
                "type": "error",
                "error": str(e)
            }
    
    def _estimate_tokens(self, text: str) -> int:
        """
        估算文本的token数量
        
        简单估算方法：
        - 中文字符约2字符/token
        - 英文字符约4字符/token
        
        Args:
            text: 文本内容
        
        Returns:
            int: 估算的token数量
        """
        # 统计中文字符数
        chinese_chars = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
        # 统计其他字符数
        other_chars = len(text) - chinese_chars
        
        # 估算token数
        estimated = (chinese_chars / 2) + (other_chars / 4)
        return int(estimated)
    
    def get_memory_messages(
        self,
        conversation_id: int
    ) -> List[Dict[str, str]]:
        """
        获取对话记忆中的消息
        
        Args:
            conversation_id: 对话ID
        
        Returns:
            List[Dict[str, str]]: 消息列表
        """
        if conversation_id not in self._memories:
            return []
        
        memory = self._memories[conversation_id]
        history = memory.load_memory_variables({})
        
        messages = []
        if "history" in history:
            for msg in history["history"]:
                if isinstance(msg, HumanMessage):
                    messages.append({"role": "USER", "content": msg.content})
                elif isinstance(msg, AIMessage):
                    messages.append({"role": "ASSISTANT", "content": msg.content})
        
        return messages


# 全局对话管理器实例
_conversation_manager: Optional[ConversationManager] = None


def get_conversation_manager() -> ConversationManager:
    """
    获取全局对话管理器实例
    
    Returns:
        ConversationManager: 对话管理器实例
    """
    global _conversation_manager
    if _conversation_manager is None:
        _conversation_manager = ConversationManager()
    return _conversation_manager


def clear_conversation_manager() -> None:
    """
    清除全局对话管理器实例
    
    用于测试或重置状态
    """
    global _conversation_manager
    _conversation_manager = None


# 导出
__all__ = [
    'ConversationManager',
    'ChatConfig',
    'get_conversation_manager',
    'clear_conversation_manager',
    'DEFAULT_CONVERSATION_TEMPLATE',
]
