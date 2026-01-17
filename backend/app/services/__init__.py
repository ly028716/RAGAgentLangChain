"""
服务层模块

提供业务逻辑处理服务。
"""

from app.services.auth_service import (
    AuthService,
    AuthServiceError,
    UserAlreadyExistsError,
    InvalidCredentialsError,
    AccountLockedError,
    UserNotFoundError,
    PasswordMismatchError,
)

from app.services.conversation_service import (
    ConversationService,
    ConversationServiceError,
    ConversationNotFoundError,
    ConversationAccessDeniedError,
)

from app.services.quota_service import (
    QuotaService,
    QuotaServiceError,
    QuotaNotFoundError,
    InsufficientQuotaError,
    InvalidQuotaValueError,
)

from app.services.file_service import FileService, file_service
from app.services.system_prompt_service import SystemPromptService
from app.services.knowledge_base_permission_service import (
    KnowledgeBasePermissionService,
    PERMISSION_LEVELS,
)


__all__ = [
    # 认证服务
    'AuthService',
    'AuthServiceError',
    'UserAlreadyExistsError',
    'InvalidCredentialsError',
    'AccountLockedError',
    'UserNotFoundError',
    'PasswordMismatchError',
    # 对话服务
    'ConversationService',
    'ConversationServiceError',
    'ConversationNotFoundError',
    'ConversationAccessDeniedError',
    # 配额服务
    'QuotaService',
    'QuotaServiceError',
    'QuotaNotFoundError',
    'InsufficientQuotaError',
    'InvalidQuotaValueError',
    # 文件服务
    'FileService',
    'file_service',
    # 系统提示词服务
    'SystemPromptService',
    # 知识库权限服务
    'KnowledgeBasePermissionService',
    'PERMISSION_LEVELS',
]
