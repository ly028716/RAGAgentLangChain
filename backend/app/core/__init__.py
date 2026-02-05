"""
核心功能模块

包含数据库、安全、缓存、向量存储、LLM等核心功能。
"""

from app.core.database import (Base, SessionLocal, close_db, engine, get_db,
                               init_db)
from app.core.llm import (TongyiLLM, clear_llm_cache, create_retry_decorator,
                          get_llm, get_llm_config, get_streaming_llm,
                          invoke_llm, invoke_llm_sync, llm_retry, stream_llm)
from app.core.security import (ACCESS_TOKEN_TYPE, REFRESH_TOKEN_TYPE,
                               add_token_to_blacklist, create_access_token,
                               create_refresh_token, create_token_pair,
                               decode_token, get_token_expiry, hash_password,
                               is_token_blacklisted,
                               remove_token_from_blacklist,
                               verify_access_token, verify_password,
                               verify_refresh_token, verify_token)
from app.core.vector_store import (VectorStoreManager,
                                   add_documents_to_knowledge_base,
                                   get_embeddings, get_vector_store,
                                   get_vector_store_manager,
                                   reset_vector_store_manager,
                                   search_knowledge_base,
                                   search_multiple_knowledge_bases)

__all__ = [
    # Database
    "engine",
    "SessionLocal",
    "Base",
    "get_db",
    "init_db",
    "close_db",
    # Security - Password
    "hash_password",
    "verify_password",
    # Security - Token creation
    "create_access_token",
    "create_refresh_token",
    "create_token_pair",
    # Security - Token verification
    "verify_token",
    "verify_access_token",
    "verify_refresh_token",
    "decode_token",
    "get_token_expiry",
    # Security - Blacklist
    "add_token_to_blacklist",
    "is_token_blacklisted",
    "remove_token_from_blacklist",
    # Security - Constants
    "ACCESS_TOKEN_TYPE",
    "REFRESH_TOKEN_TYPE",
    # LLM
    "TongyiLLM",
    "get_llm",
    "get_streaming_llm",
    "invoke_llm",
    "invoke_llm_sync",
    "stream_llm",
    "clear_llm_cache",
    "get_llm_config",
    "llm_retry",
    "create_retry_decorator",
    # Vector Store
    "VectorStoreManager",
    "get_vector_store_manager",
    "get_vector_store",
    "get_embeddings",
    "add_documents_to_knowledge_base",
    "search_knowledge_base",
    "search_multiple_knowledge_bases",
    "reset_vector_store_manager",
]
