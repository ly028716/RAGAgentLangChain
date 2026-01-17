"""
Pydantic模型模块

导出所有API请求和响应的数据模型。
"""

from app.schemas.auth import (
    UserRegister,
    UserLogin,
    TokenResponse,
    RefreshTokenRequest,
    PasswordChangeRequest,
    UserResponse,
    MessageResponse as AuthMessageResponse,
)

from app.schemas.conversation import (
    MessageRoleEnum,
    ChatModeEnum,
    ConversationCreate,
    ConversationUpdate,
    ChatConfig,
    ChatRequest,
    MessageCreate,
    MessageResponse,
    ConversationResponse,
    ConversationListItem,
    ConversationListResponse,
    ConversationDetailResponse,
    ChatResponse,
    StreamTokenEvent,
    StreamDoneEvent,
    StreamErrorEvent,
    DeleteResponse,
)

from app.schemas.quota import (
    QuotaResponse,
    QuotaUpdateRequest,
    QuotaUpdateResponse,
    QuotaErrorResponse,
)

from app.schemas.knowledge_base import (
    KnowledgeBaseCreate,
    KnowledgeBaseUpdate,
    KnowledgeBaseResponse,
    KnowledgeBaseListResponse,
    DocumentResponse,
    DocumentListResponse,
    DocumentStatusResponse,
    DocumentPreviewResponse,
    DocumentUploadResponse,
    BatchUploadResponse,
    RAGQueryRequest,
    DocumentChunkResponse,
    RAGQueryResponse,
    RAGStreamSourcesEvent,
    RAGStreamTokenEvent,
    RAGStreamDoneEvent,
    RAGStreamErrorEvent,
    MessageResponse as KBMessageResponse,
    ErrorResponse,
)

from app.schemas.agent import (
    ToolBase,
    ToolCreate,
    ToolUpdate,
    ToolResponse,
    ToolListResponse,
    AgentStep,
    TaskExecuteRequest,
    ExecutionResponse,
    ExecutionListItem,
    ExecutionListResponse,
    DeleteResponse as AgentDeleteResponse,
)

from app.schemas.system_prompt import (
    SystemPromptCreate,
    SystemPromptUpdate,
    SystemPromptResponse,
    SystemPromptListResponse,
    SetDefaultPromptResponse,
)

from app.schemas.user import (
    UserProfileResponse,
    UserProfileUpdate,
    AvatarUploadResponse,
    AvatarDeleteResponse,
)

from app.schemas.knowledge_base_permission import (
    PermissionCreate,
    PermissionUpdate,
    PermissionResponse,
    PermissionListResponse,
    VisibilityUpdate,
    VisibilityResponse,
    ShareKnowledgeBaseRequest,
)

__all__ = [
    # 认证相关
    'UserRegister',
    'UserLogin',
    'TokenResponse',
    'RefreshTokenRequest',
    'PasswordChangeRequest',
    'UserResponse',
    'AuthMessageResponse',
    # 对话相关
    'MessageRoleEnum',
    'ChatModeEnum',
    'ConversationCreate',
    'ConversationUpdate',
    'ChatConfig',
    'ChatRequest',
    'MessageCreate',
    'MessageResponse',
    'ConversationResponse',
    'ConversationListItem',
    'ConversationListResponse',
    'ConversationDetailResponse',
    'ChatResponse',
    'StreamTokenEvent',
    'StreamDoneEvent',
    'StreamErrorEvent',
    'DeleteResponse',
    # 配额相关
    'QuotaResponse',
    'QuotaUpdateRequest',
    'QuotaUpdateResponse',
    'QuotaErrorResponse',
    # 知识库相关
    'KnowledgeBaseCreate',
    'KnowledgeBaseUpdate',
    'KnowledgeBaseResponse',
    'KnowledgeBaseListResponse',
    # 文档相关
    'DocumentResponse',
    'DocumentListResponse',
    'DocumentStatusResponse',
    'DocumentPreviewResponse',
    'DocumentUploadResponse',
    'BatchUploadResponse',
    # RAG相关
    'RAGQueryRequest',
    'DocumentChunkResponse',
    'RAGQueryResponse',
    'RAGStreamSourcesEvent',
    'RAGStreamTokenEvent',
    'RAGStreamDoneEvent',
    'RAGStreamErrorEvent',
    # 通用
    'KBMessageResponse',
    'ErrorResponse',
    # Agent相关
    'ToolBase',
    'ToolCreate',
    'ToolUpdate',
    'ToolResponse',
    'ToolListResponse',
    'AgentStep',
    'TaskExecuteRequest',
    'ExecutionResponse',
    'ExecutionListItem',
    'ExecutionListResponse',
    'AgentDeleteResponse',
    # 系统提示词相关
    'SystemPromptCreate',
    'SystemPromptUpdate',
    'SystemPromptResponse',
    'SystemPromptListResponse',
    'SetDefaultPromptResponse',
    # 用户相关
    'UserProfileResponse',
    'UserProfileUpdate',
    'AvatarUploadResponse',
    'AvatarDeleteResponse',
    # 知识库权限相关
    'PermissionCreate',
    'PermissionUpdate',
    'PermissionResponse',
    'PermissionListResponse',
    'VisibilityUpdate',
    'VisibilityResponse',
    'ShareKnowledgeBaseRequest',
]
