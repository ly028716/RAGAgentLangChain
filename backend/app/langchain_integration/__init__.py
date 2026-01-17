"""
LangChain集成模块

提供LangChain相关功能，包括对话链、RAG链、Agent执行器等。
"""

from app.langchain_integration.chains import (
    ConversationManager,
    ChatConfig,
    get_conversation_manager,
    clear_conversation_manager,
    DEFAULT_CONVERSATION_TEMPLATE,
)

from app.langchain_integration.document_loaders import (
    DocumentLoaderFactory,
    DocumentProcessingError,
    UnsupportedFileTypeError,
)

from app.langchain_integration.rag_chain import (
    RAGManager,
    RAGResponse,
    DocumentChunk,
    get_rag_manager,
    clear_rag_manager,
    RAG_PROMPT_TEMPLATE,
    RAG_CONVERSATION_TEMPLATE,
)


__all__ = [
    # 对话链
    'ConversationManager',
    'ChatConfig',
    'get_conversation_manager',
    'clear_conversation_manager',
    'DEFAULT_CONVERSATION_TEMPLATE',
    # 文档加载器
    'DocumentLoaderFactory',
    'DocumentProcessingError',
    'UnsupportedFileTypeError',
    # RAG链
    'RAGManager',
    'RAGResponse',
    'DocumentChunk',
    'get_rag_manager',
    'clear_rag_manager',
    'RAG_PROMPT_TEMPLATE',
    'RAG_CONVERSATION_TEMPLATE',
]
