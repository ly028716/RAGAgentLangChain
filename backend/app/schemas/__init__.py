"""
Pydantic模型模块

导出所有API请求和响应的数据模型。
"""

from app.schemas.agent import AgentStep
from app.schemas.agent import DeleteResponse as AgentDeleteResponse
from app.schemas.agent import (ExecutionListItem, ExecutionListResponse,
                               ExecutionResponse, TaskExecuteRequest, ToolBase,
                               ToolCreate, ToolListResponse, ToolResponse,
                               ToolUpdate)
from app.schemas.auth import MessageResponse as AuthMessageResponse
from app.schemas.auth import (PasswordChangeRequest, RefreshTokenRequest,
                              TokenResponse, UserLogin, UserRegister,
                              UserResponse)
from app.schemas.conversation import (ChatConfig, ChatModeEnum, ChatRequest,
                                      ChatResponse, ConversationCreate,
                                      ConversationDetailResponse,
                                      ConversationListItem,
                                      ConversationListResponse,
                                      ConversationResponse, ConversationUpdate,
                                      DeleteResponse, MessageCreate,
                                      MessageResponse, MessageRoleEnum,
                                      StreamDoneEvent, StreamErrorEvent,
                                      StreamTokenEvent)
from app.schemas.knowledge_base import (BatchUploadResponse,
                                        DocumentChunkResponse,
                                        DocumentListResponse,
                                        DocumentPreviewResponse,
                                        DocumentResponse,
                                        DocumentStatusResponse,
                                        DocumentUploadResponse, ErrorResponse,
                                        KnowledgeBaseCreate,
                                        KnowledgeBaseListResponse,
                                        KnowledgeBaseResponse,
                                        KnowledgeBaseUpdate)
from app.schemas.knowledge_base import MessageResponse as KBMessageResponse
from app.schemas.knowledge_base import (RAGQueryRequest, RAGQueryResponse,
                                        RAGStreamDoneEvent,
                                        RAGStreamErrorEvent,
                                        RAGStreamSourcesEvent,
                                        RAGStreamTokenEvent)
from app.schemas.knowledge_base_permission import (PermissionCreate,
                                                   PermissionListResponse,
                                                   PermissionResponse,
                                                   PermissionUpdate,
                                                   ShareKnowledgeBaseRequest,
                                                   VisibilityResponse,
                                                   VisibilityUpdate)
from app.schemas.quota import (QuotaErrorResponse, QuotaResponse,
                               QuotaUpdateRequest, QuotaUpdateResponse)
from app.schemas.system_prompt import (SetDefaultPromptResponse,
                                       SystemPromptCreate,
                                       SystemPromptListResponse,
                                       SystemPromptResponse,
                                       SystemPromptUpdate)
from app.schemas.user import (AvatarDeleteResponse, AvatarUploadResponse,
                              UserProfileResponse, UserProfileUpdate)

__all__ = [
    # 认证相关
    "UserRegister",
    "UserLogin",
    "TokenResponse",
    "RefreshTokenRequest",
    "PasswordChangeRequest",
    "UserResponse",
    "AuthMessageResponse",
    # 对话相关
    "MessageRoleEnum",
    "ChatModeEnum",
    "ConversationCreate",
    "ConversationUpdate",
    "ChatConfig",
    "ChatRequest",
    "MessageCreate",
    "MessageResponse",
    "ConversationResponse",
    "ConversationListItem",
    "ConversationListResponse",
    "ConversationDetailResponse",
    "ChatResponse",
    "StreamTokenEvent",
    "StreamDoneEvent",
    "StreamErrorEvent",
    "DeleteResponse",
    # 配额相关
    "QuotaResponse",
    "QuotaUpdateRequest",
    "QuotaUpdateResponse",
    "QuotaErrorResponse",
    # 知识库相关
    "KnowledgeBaseCreate",
    "KnowledgeBaseUpdate",
    "KnowledgeBaseResponse",
    "KnowledgeBaseListResponse",
    # 文档相关
    "DocumentResponse",
    "DocumentListResponse",
    "DocumentStatusResponse",
    "DocumentPreviewResponse",
    "DocumentUploadResponse",
    "BatchUploadResponse",
    # RAG相关
    "RAGQueryRequest",
    "DocumentChunkResponse",
    "RAGQueryResponse",
    "RAGStreamSourcesEvent",
    "RAGStreamTokenEvent",
    "RAGStreamDoneEvent",
    "RAGStreamErrorEvent",
    # 通用
    "KBMessageResponse",
    "ErrorResponse",
    # Agent相关
    "ToolBase",
    "ToolCreate",
    "ToolUpdate",
    "ToolResponse",
    "ToolListResponse",
    "AgentStep",
    "TaskExecuteRequest",
    "ExecutionResponse",
    "ExecutionListItem",
    "ExecutionListResponse",
    "AgentDeleteResponse",
    # 系统提示词相关
    "SystemPromptCreate",
    "SystemPromptUpdate",
    "SystemPromptResponse",
    "SystemPromptListResponse",
    "SetDefaultPromptResponse",
    # 用户相关
    "UserProfileResponse",
    "UserProfileUpdate",
    "AvatarUploadResponse",
    "AvatarDeleteResponse",
    # 知识库权限相关
    "PermissionCreate",
    "PermissionUpdate",
    "PermissionResponse",
    "PermissionListResponse",
    "VisibilityUpdate",
    "VisibilityResponse",
    "ShareKnowledgeBaseRequest",
]
