# 前后端 API 接口设计文档

**项目**：AI 智能助手系统（Vue 3 + FastAPI + LangChain）  
**版本**：v1.0  
**日期**：2026-01-17  
**依据**：`docs/产品需求文档.md`（PRD）、`docs/软件架构设计文档.md`（SAD）  

## 1. 文档目标与范围

本文件用于统一前后端接口契约，覆盖：

- 后端 REST/SSE API 的路径、鉴权、参数、请求/响应结构、错误格式、分页规范
- 前端 API 封装（Axios Client）调用约定与模块映射

> 说明：PRD 的示例路径多为 `/api/*`；SAD 明确要求版本化为 `/api/v1`。本项目以 `/api/v1` 为唯一稳定前缀。

## 2. 统一约定（全局契约）

### 2.1 Base URL 与版本化

- 默认 API 前缀：`/api/v1`
- 版本化策略：新增字段保持向后兼容；新增接口优先新增 path；破坏性变更通过新版本 `/api/v2` 引入

前端默认 Base URL：

- `VITE_API_BASE_URL` 存在则使用其值
- 否则使用 `/api/v1`

### 2.2 鉴权（JWT）

除显式标注“无需鉴权”的端点外，均需要携带 Access Token：

```
Authorization: Bearer <access_token>
```

- Access/Refresh 获取：`POST /api/v1/auth/login`
- Access 过期：`POST /api/v1/auth/refresh` 刷新并重试

### 2.3 Request ID

- 后端为每个请求生成或透传请求 ID，并在响应头返回：
  - `X-Request-ID: <uuid>`
- 错误响应中也会包含 `request_id` 字段（便于排障与日志追踪）

### 2.4 Content-Type

- JSON 请求：`Content-Type: application/json`
- 文件上传：`multipart/form-data`
- SSE 流式：响应 `Content-Type: text/event-stream`

### 2.5 错误响应格式（统一 Envelope）

后端对异常做统一封装，错误响应格式固定为：

```json
{
  "error_code": "5001",
  "message": "请求参数验证失败",
  "status_code": 422,
  "details": {
    "errors": [
      { "field": "body.username", "message": "Field required", "type": "missing" }
    ]
  },
  "request_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

说明：

- 当业务代码抛出 `HTTPException(detail=...)` 时，会被封装为：
  - `error_code`: HTTP 状态码字符串（例如 `"404"`）
  - `message`: `detail` 的原值（可能是字符串，也可能是对象）

### 2.6 分页规范

本项目后端主要使用 **skip/limit**：

- `skip`：跳过的记录数（>=0）
- `limit`：返回数量（一般 1~100）

统一响应（列表）结构：

```json
{
  "total": 123,
  "items": []
}
```

前端（如果按 page/pageSize）需转换：

- `skip = (page - 1) * pageSize`
- `limit = pageSize`

### 2.7 时间与时区

- 所有时间字段使用 ISO 8601 字符串或可 JSON 序列化时间类型（前端按字符串处理）
- 服务端时间建议按 UTC 存储与传输，前端展示时可本地化

### 2.8 SSE 事件格式（通用）

流式接口使用 SSE，每条事件均以 `data: <json>\n\n` 发送，json 内包含 `type` 字段：

- `type=token`：文本增量片段
- `type=done`：完成事件（通常带 tokens_used / message_id 等）
- `type=error`：错误事件

前端读取策略：

- 逐行解析以 `data: ` 开头的行
- 将 `data` 内容 `JSON.parse` 后按 `type` 分发

## 3. 后端 API 设计（按业务域分组）

> 记号：🔒 需要鉴权；🛡️ 需要管理员权限；🌊 SSE 流式；📦 multipart 上传；✅ 无需鉴权

### 3.1 认证（Auth）

#### 3.1.1 用户注册

- `POST /api/v1/auth/register` ✅
- Body：`UserRegister`
  - `username: string`（3-50，字母/数字/下划线）
  - `password: string`（>=8，含字母和数字）
  - `email?: string`
- Response 201：`UserResponse`

#### 3.1.2 用户登录

- `POST /api/v1/auth/login` ✅
- Body：`UserLogin`（username/password）
- Response 200：`TokenResponse`
  - `access_token`, `refresh_token`, `token_type`, `expires_in`
- 错误：
  - 401：凭证错误
  - 423：账户锁定（连续失败触发）

#### 3.1.3 刷新令牌

- `POST /api/v1/auth/refresh` ✅
- Body：`RefreshTokenRequest`（`refresh_token`）
- Response 200：`TokenResponse`

#### 3.1.4 获取当前用户信息（简版）

- `GET /api/v1/auth/profile` 🔒
- Response 200：`UserResponse`

#### 3.1.5 修改密码

- `PUT /api/v1/auth/password` 🔒
- Body：`PasswordChangeRequest`
  - `old_password`
  - `new_password`
- Response 200：`{ "message": "密码修改成功" }`

### 3.2 验证码（Verification）

#### 3.2.1 发送邮箱验证码

- `POST /api/v1/verification/send-email` ✅
- Body：`SendEmailCodeRequest`
  - `email`
  - `code_type`: `register|reset_password|bind_email`
- Response：`SendCodeResponse`（`success/message/expires_in`）

#### 3.2.2 发送短信验证码

- `POST /api/v1/verification/send-sms` ✅
- Body：`SendSMSCodeRequest`
  - `phone`（大陆手机号正则）
  - `code_type`: `register|reset_password|bind_phone`
- Response：`SendCodeResponse`

#### 3.2.3 验证验证码

- `POST /api/v1/verification/verify` ✅
- Body：`VerifyCodeRequest`
  - `target`（邮箱或手机号）
  - `code`（6 位数字）
  - `code_type`
- Response：`VerifyCodeResponse`

### 3.3 用户中心（User）

#### 3.3.1 获取当前用户信息（增强版）

- `GET /api/v1/user/profile` 🔒
- Response：`UserProfileResponse`
  - 包含 `is_admin`、注销时间字段等

#### 3.3.2 更新用户信息

- `PUT /api/v1/user/profile` 🔒
- Body：`UserProfileUpdate`
  - `nickname?: string`
  - `email?: string`
- Response：`UserProfileResponse`

#### 3.3.3 上传头像

- `POST /api/v1/user/avatar` 🔒 📦
- FormData：
  - `file`: 头像文件
- Response：`AvatarUploadResponse`

#### 3.3.4 删除头像

- `DELETE /api/v1/user/avatar` 🔒
- Response：`AvatarDeleteResponse`

#### 3.3.5 获取用户头像文件

- `GET /api/v1/user/avatar/{user_id}` ✅
- Response：二进制图片文件（`image/jpeg|png|gif|webp`）

#### 3.3.6 账号注销（冷静期）

- `POST /api/v1/user/deletion/request` 🔒
  - Body：`DeletionRequest`（password/reason?）
  - Response：`DeletionRequestResponse`
- `POST /api/v1/user/deletion/cancel` 🔒
  - Response：`DeletionCancelResponse`
- `GET /api/v1/user/deletion/status` 🔒
  - Response：`DeletionStatusResponse`

### 3.4 对话管理（Conversations）

#### 3.4.1 创建对话

- `POST /api/v1/conversations` 🔒
- Body：`ConversationCreate`
  - `title`（默认“新对话”）
- Response 201：`ConversationResponse`

#### 3.4.2 获取对话列表（分页）

- `GET /api/v1/conversations` 🔒
- Query：`skip, limit`
- Response：`ConversationListResponse`（`total/items[]`）

#### 3.4.3 获取对话详情（含消息）

- `GET /api/v1/conversations/{conversation_id}` 🔒
- Response：`ConversationDetailResponse`
  - `messages: MessageResponse[]`

#### 3.4.4 更新对话标题

- `PUT /api/v1/conversations/{conversation_id}` 🔒
- Body：`ConversationUpdate`（`title`）
- Response：`ConversationResponse`

#### 3.4.5 删除对话（软删除）

- `DELETE /api/v1/conversations/{conversation_id}` 🔒
- Response：`DeleteResponse`（`message`）

#### 3.4.6 获取对话消息（分页）

- `GET /api/v1/conversations/{conversation_id}/messages` 🔒
- Query：`skip, limit?`
- Response：`MessageResponse[]`

#### 3.4.7 导出对话

- `GET /api/v1/conversations/{conversation_id}/export` 🔒
- Query：
  - `format`: `markdown|json`（默认 markdown）
- Response：`ExportResponse`
  - `content`: string
  - `filename`: string

#### 3.4.8 生成对话标题

- `POST /api/v1/conversations/{conversation_id}/generate-title` 🔒
- Body：`TitleGenerateRequest`（`message`）
- Response：`TitleGenerateResponse`（`title`）

### 3.5 聊天（Chat）

#### 3.5.1 非流式聊天

- `POST /api/v1/chat` 🔒
- Body：`ChatRequest`
  - `conversation_id: number`（建议必传：该端点面向既有对话）
  - `content: string`
  - `config?: { temperature, max_tokens, mode }`
- Response：`ChatResponse`

#### 3.5.2 流式聊天（SSE）

- `POST /api/v1/chat/stream` 🔒 🌊
- Body：`ChatRequest`
  - `conversation_id` 可为 `null`：后端自动创建新对话并通过事件回传新 ID
- SSE 事件：
  - `type=conversation`：`{ "type": "conversation", "conversation_id": 123 }`
  - `type=token`：`{ "type": "token", "content": "..." }`
  - `type=done`：`{ "type": "done", "message_id": 456, "tokens_used": 789, "conversation_id": 123 }`
  - `type=error`：`{ "type": "error", "error": "..." }`

### 3.6 知识库管理（Knowledge Bases）

- `POST /api/v1/knowledge-bases` 🔒
  - Body：`KnowledgeBaseCreate`
  - Response 201：`KnowledgeBaseResponse`
- `GET /api/v1/knowledge-bases` 🔒
  - Query：`skip, limit`
  - Response：`KnowledgeBaseListResponse`
- `GET /api/v1/knowledge-bases/{kb_id}` 🔒
  - Response：`KnowledgeBaseResponse`
- `PUT /api/v1/knowledge-bases/{kb_id}` 🔒
  - Body：`KnowledgeBaseUpdate`
  - Response：`KnowledgeBaseResponse`
- `DELETE /api/v1/knowledge-bases/{kb_id}` 🔒
  - Response：`MessageResponse`（`message`）

### 3.7 知识库权限（Knowledge Base Permissions）

用于知识库分享与授权（SAD 权限模型落地的一部分）。

- `GET /api/v1/knowledge-bases/{kb_id}/permissions` 🔒
  - Response：`PermissionListResponse`（`items/total`）
- `POST /api/v1/knowledge-bases/{kb_id}/permissions` 🔒
  - Body：`PermissionCreate`（`user_id? / permission_type`）
  - Response 201：`PermissionResponse`
- `PUT /api/v1/knowledge-bases/{kb_id}/permissions/{permission_id}` 🔒
  - Body：`PermissionUpdate`
  - Response：`PermissionResponse`
- `DELETE /api/v1/knowledge-bases/{kb_id}/permissions/{permission_id}` 🔒
  - Response 204：无响应体
- `POST /api/v1/knowledge-bases/{kb_id}/share` 🔒
  - Body：`ShareKnowledgeBaseRequest`（username/permission_type）
  - Response 201：`PermissionResponse`

### 3.8 文档管理（Documents）

#### 3.8.1 上传单个文档

- `POST /api/v1/documents/upload` 🔒 📦
- Query：`knowledge_base_id`
- FormData：`file`
- Response 201：`DocumentUploadResponse`

#### 3.8.2 批量上传文档

- `POST /api/v1/documents/upload-batch` 🔒 📦
- Query：`knowledge_base_id`
- FormData：`files`（可重复字段）
- Response 201：`BatchUploadResponse`
  - `documents`: 成功列表
  - `errors`: 失败列表（filename/error）

#### 3.8.3 获取文档列表

- `GET /api/v1/documents` 🔒
- Query：`knowledge_base_id, skip, limit`
- Response：`DocumentListResponse`

#### 3.8.4 获取文档处理状态

- `GET /api/v1/documents/{document_id}/status` 🔒
- Response：`DocumentStatusResponse`（含 progress 0-100）

#### 3.8.5 获取文档预览

- `GET /api/v1/documents/{document_id}/preview` 🔒
- Query：`max_chars`（默认 1000）
- Response：`DocumentPreviewResponse`

#### 3.8.6 删除文档

- `DELETE /api/v1/documents/{document_id}` 🔒
- Response：`MessageResponse`

### 3.9 RAG 问答（RAG）

#### 3.9.1 非流式问答

- `POST /api/v1/rag/query` 🔒
- Body：`RAGQueryRequest`
  - `knowledge_base_ids: number[]`（至少 1 个）
  - `question: string`
  - `top_k?: number`（默认 5）
  - `conversation_id?: string`（用于上下文）
- Response：`RAGQueryResponse`
  - `answer`
  - `sources: DocumentChunkResponse[]`（含 similarity_score）
  - `tokens_used`

#### 3.9.2 流式问答（SSE）

- `POST /api/v1/rag/query/stream` 🔒 🌊
- SSE 事件：
  - `type=sources`：`{ "type": "sources", "sources": [...] }`
  - `type=token`：`{ "type": "token", "content": "..." }`
  - `type=done`：`{ "type": "done", "content": "<完整答案>", "tokens_used": 123 }`
  - `type=error`：`{ "type": "error", "error": "..." }`

### 3.10 Agent 智能代理（Agent）

#### 3.10.1 工具管理

- `GET /api/v1/agent/tools` 🔒
  - Query：`skip, limit, tool_type?, is_enabled?`
  - Response：`ToolListResponse`（`total/items[]`）
- `GET /api/v1/agent/tools/{tool_id}` 🔒
  - Response：`ToolResponse`
- `POST /api/v1/agent/tools` 🔒
  - Body：`ToolCreate`
  - Response 201：`ToolResponse`
- `PUT /api/v1/agent/tools/{tool_id}` 🔒
  - Body：`ToolUpdate`
  - Response：`ToolResponse`
- `DELETE /api/v1/agent/tools/{tool_id}` 🔒
  - Response：`DeleteResponse`

#### 3.10.2 执行任务（非流式）

- `POST /api/v1/agent/execute` 🔒
- Body：`TaskExecuteRequest`
  - `task`
  - `tool_ids?: number[]`
  - `max_iterations?: number`
- Response 201：`ExecutionResponse`

#### 3.10.3 执行任务（流式 SSE）

- `POST /api/v1/agent/execute/stream` 🔒 🌊
- SSE 事件：后端透传 `service.stream_execute_task(...)` 的事件对象
  - 推荐前端按 `{ type, data }` 或 `{ type, ... }` 兼容解析

#### 3.10.4 执行历史

- `GET /api/v1/agent/executions` 🔒
  - Query：`skip, limit, status?`
  - Response：`ExecutionListResponse`（`total/items[]`）
- `GET /api/v1/agent/executions/{execution_id}` 🔒
  - Response：`ExecutionResponse`

### 3.11 系统提示词（Prompts）

- `GET /api/v1/prompts` 🔒
  - Query：`category?, skip, limit`
  - Response：`SystemPromptListResponse`
- `POST /api/v1/prompts` 🔒
  - Body：`SystemPromptCreate`
  - Response 201：`SystemPromptResponse`
- `GET /api/v1/prompts/{prompt_id}` 🔒
  - Response：`SystemPromptResponse`
- `PUT /api/v1/prompts/{prompt_id}` 🔒
  - Body：`SystemPromptUpdate`
  - Response：`SystemPromptResponse`
- `DELETE /api/v1/prompts/{prompt_id}` 🔒
  - Response 204：无响应体
- `PUT /api/v1/prompts/{prompt_id}/default` 🔒
  - Response：`SetDefaultPromptResponse`

### 3.12 配额管理（Quota）

- `GET /api/v1/quota` 🔒
  - Response：`QuotaResponse`
- `PUT /api/v1/quota` 🛡️
  - Body：`QuotaUpdateRequest`
  - Response：`QuotaUpdateResponse`
- `POST /api/v1/quota/reset` 🛡️
  - Query：`user_id`
  - Response：`QuotaResponse`

### 3.13 系统管理（System）

- `GET /api/v1/system/config` 🛡️
  - Response：`SystemConfigResponse`（敏感字段已脱敏）
- `PUT /api/v1/system/config` 🛡️
  - Body：`SystemConfigUpdateRequest`
  - Response：`SystemConfigResponse`
- `GET /api/v1/system/stats` 🔒
  - Query：`user_id?, start_date?, end_date?`
  - 说明：管理员可查询全量或指定用户；普通用户仅能查询自己
  - Response：`UsageStatsResponse`
- `GET /api/v1/system/stats/all` 🛡️
  - Query：`start_date?, end_date?`
  - Response：`UsageStatsResponse`
- `GET /api/v1/system/health` ✅
  - Response：`HealthCheckResponse`
- `GET /api/v1/system/info` 🔒
  - Response：`SystemInfoResponse`

### 3.14 监控与运维（Observability）

#### 3.14.1 根路径信息

- `GET /` ✅
- 返回包含 docs/health/metrics 等链接

#### 3.14.2 简易健康检查

- `GET /health` ✅
- 返回应用状态与调度器状态（用于 LB 探活）

#### 3.14.3 定时任务列表

- `GET /scheduler/jobs` ✅
- 返回调度器任务列表（是否启用/运行中/下次执行时间）

#### 3.14.4 Prometheus 指标

- `GET /metrics` ✅
- 返回 Prometheus 文本格式指标

## 4. 前端 API 设计（模块映射与调用约定）

### 4.1 Axios Client 统一封装

前端请求封装位于：`frontend/src/api/index.ts`，约定：

- 自动注入 `Authorization: Bearer <token>`
- 401 自动刷新 token（并发刷新做了竞态保护）
- 通用错误提示（Element Plus Message）

### 4.2 API 模块映射表

| 前端模块 | 主要方法 | 对应后端路由前缀 |
|---|---|---|
| `src/api/auth.ts` | login/register/refreshToken/changePassword/getCurrentUser | `/auth/*` |
| `src/api/user.ts` | getProfile/updateProfile/uploadAvatar/deleteAvatar/deletion* | `/user/*` |
| `src/api/conversation.ts` | getList/create/getDetail/update/delete/getMessages/export | `/conversations/*` |
| `src/composables/useChat.ts` | sendMessage（流式） | `/chat/stream` |
| `src/api/knowledge.ts` | knowledge-bases/documents/rag | `/knowledge-bases/*` `/documents/*` `/rag/*` |
| `src/api/kb-permissions.ts` | permissions/share | `/knowledge-bases/{kbId}/permissions` `/knowledge-bases/{kbId}/share` |
| `src/api/agent.ts` | tools/execute/executions（含流式） | `/agent/*` |
| `src/api/prompts.ts` | prompts CRUD / default | `/prompts/*` |

### 4.3 前端类型（TypeScript）与后端 Schema 对齐

前端类型定义：`frontend/src/types/index.ts`。推荐以“后端 Pydantic Schema”为准，保持以下一致性：

- `skip/limit` 分页字段名与响应结构（`total/items`）
- SSE 事件结构：必须包含 `type`
- 文档状态：`pending|processing|completed|failed`（前端展示可映射为中文）
- 权限类型：`owner|editor|viewer`

## 5. 附录：核心数据结构摘要（用于联调）

### 5.1 TokenResponse

```json
{
  "access_token": "xxx",
  "refresh_token": "xxx",
  "token_type": "bearer",
  "expires_in": 604800
}
```

### 5.2 列表响应（通用）

```json
{
  "total": 2,
  "items": []
}
```

### 5.3 ChatRequest（示例）

```json
{
  "conversation_id": null,
  "content": "你好，帮我总结一下这份文档",
  "config": {
    "temperature": 0.7,
    "max_tokens": 2000,
    "mode": "normal"
  }
}
```

### 5.4 RAGQueryRequest（示例）

```json
{
  "knowledge_base_ids": [1, 2],
  "question": "这套系统的鉴权方式是什么？",
  "top_k": 5,
  "conversation_id": "optional"
}
```

