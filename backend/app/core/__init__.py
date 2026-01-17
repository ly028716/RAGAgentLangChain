"""
核心功能模块

包含数据库、安全、缓存、向量存储、LLM等核心功能。
"""

from app.core.database import (
    engine,
    SessionLocal,
    Base,
    get_db,
    init_db,
    close_db,
)

from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    create_token_pair,
    verify_token,
    verify_access_token,
    verify_refresh_token,
    decode_token,
    get_token_expiry,
    add_token_to_blacklist,
    is_token_blacklisted,
    remove_token_from_blacklist,
    ACCESS_TOKEN_TYPE,
    REFRESH_TOKEN_TYPE,
)

from app.core.llm import (
    TongyiLLM,
    get_llm,
    get_streaming_llm,
    invoke_llm,
    invoke_llm_sync,
    stream_llm,
    clear_llm_cache,
    get_llm_config,
    llm_retry,
    create_retry_decorator,
)

from app.core.vector_store import (
    VectorStoreManager,
    get_vector_store_manager,
    get_vector_store,
    get_embeddings,
    add_documents_to_knowledge_base,
    search_knowledge_base,
    search_multiple_knowledge_bases,
    reset_vector_store_manager,
)

__all__ = [
    # Database
    'engine',
    'SessionLocal',
    'Base',
    'get_db',
    'init_db',
    'close_db',
    # Security - Password
    'hash_password',
    'verify_password',
    # Security - Token creation
    'create_access_token',
    'create_refresh_token',
    'create_token_pair',
    # Security - Token verification
    'verify_token',
    'verify_access_token',
    'verify_refresh_token',
    'decode_token',
    'get_token_expiry',
    # Security - Blacklist
    'add_token_to_blacklist',
    'is_token_blacklisted',
    'remove_token_from_blacklist',
    # Security - Constants
    'ACCESS_TOKEN_TYPE',
    'REFRESH_TOKEN_TYPE',
    # LLM
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
    # Vector Store
    'VectorStoreManager',
    'get_vector_store_manager',
    'get_vector_store',
    'get_embeddings',
    'add_documents_to_knowledge_base',
    'search_knowledge_base',
    'search_multiple_knowledge_bases',
    'reset_vector_store_manager',
]
