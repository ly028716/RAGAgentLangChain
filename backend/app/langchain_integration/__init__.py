"""
LangChain集成模块

提供LangChain相关功能，包括对话链、RAG链、Agent执行器等。
"""

from app.langchain_integration.chains import (DEFAULT_CONVERSATION_TEMPLATE,
                                              ChatConfig, ConversationManager,
                                              clear_conversation_manager,
                                              get_conversation_manager)
from app.langchain_integration.document_loaders import (
    DocumentLoaderFactory, DocumentProcessingError, UnsupportedFileTypeError)
from app.langchain_integration.rag_chain import (RAG_CONVERSATION_TEMPLATE,
                                                 RAG_PROMPT_TEMPLATE,
                                                 DocumentChunk, RAGManager,
                                                 RAGResponse,
                                                 clear_rag_manager,
                                                 get_rag_manager)

__all__ = [
    # 对话链
    "ConversationManager",
    "ChatConfig",
    "get_conversation_manager",
    "clear_conversation_manager",
    "DEFAULT_CONVERSATION_TEMPLATE",
    # 文档加载器
    "DocumentLoaderFactory",
    "DocumentProcessingError",
    "UnsupportedFileTypeError",
    # RAG链
    "RAGManager",
    "RAGResponse",
    "DocumentChunk",
    "get_rag_manager",
    "clear_rag_manager",
    "RAG_PROMPT_TEMPLATE",
    "RAG_CONVERSATION_TEMPLATE",
]
