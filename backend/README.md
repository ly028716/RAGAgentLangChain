# AI智能助手系统 - 后端

[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)
[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![LangChain](https://img.shields.io/badge/LangChain-1.0-orange.svg)](https://www.langchain.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

基于FastAPI和LangChain 1.0的企业级AI智能助手系统后端服务，集成阿里云通义千问大模型，提供智能对话、RAG知识库问答和Agent智能代理等核心功能。

## 📋 目录

- [功能特性](#功能特性)
- [技术栈](#技术栈)
- [系统架构](#系统架构)
- [快速开始](#快速开始)
- [安装部署](#安装部署)
- [配置说明](#配置说明)
- [API文档](#api文档)
- [开发指南](#开发指南)
- [测试](#测试)
- [性能优化](#性能优化)
- [故障排查](#故障排查)
- [贡献指南](#贡献指南)
- [许可证](#许可证)

## ✨ 功能特性

### 核心功能

- 🔐 **用户认证与授权**
  - JWT令牌认证（访问令牌7天，刷新令牌30天）
  - Bcrypt密码加密（工作因子12）
  - 登录失败锁定机制（5次失败锁定15分钟）
  - 密码强度验证

- 💬 **智能对话管理**
  - 多轮对话上下文维护
  - SSE流式响应（首字响应<3秒）
  - 对话历史管理和分页查询
  - 自动生成对话标题
  - 对话导出（Markdown/JSON格式）

- 📚 **RAG知识库问答**
  - 支持PDF、Word、TXT、Markdown文档
  - 自动文档分块和向量化
  - 多知识库联合检索
  - 相似度评分和来源追溯
  - 异步文档处理（<30秒/MB）

- 🤖 **Agent智能代理**
  - ReAct推理模式
  - 内置工具：搜索、计算器、天气查询
  - 自定义工具管理
  - 执行步骤可视化
  - 任务执行历史记录

- 📊 **配额管理**
  - 用户月度Token配额
  - 实时配额检查和扣除
  - 配额不足警告
  - 自动月度重置
  - 管理员配额调整

- 📈 **系统监控与统计**
  - Prometheus指标导出
  - API使用统计
  - Token消耗追踪
  - 健康检查接口
  - 慢查询日志

- 🔔 **实时通知**
  - WebSocket连接管理
  - 文档处理进度推送
  - Agent执行步骤推送
  - 配额警告通知

### 安全特性

- SQL注入防护（ORM参数化查询）
- XSS防护（输入验证和清理）
- CSRF令牌验证
- API速率限制
- 敏感数据加密存储（AES-256）
- 请求追踪ID
- 详细的审计日志

## 🛠 技术栈

### 核心框架

- **Web框架**: FastAPI 0.104+ - 高性能异步Web框架
- **AI框架**: LangChain 1.0 - LLM应用开发框架
- **ORM**: SQLAlchemy 2.0 - Python SQL工具包和ORM

### 数据存储

- **关系数据库**: MySQL 8.0 - 业务数据存储
- **缓存数据库**: Redis 7.0 - 缓存和会话管理
- **向量数据库**: Chroma - 文档向量存储

### AI服务

- **LLM**: 通义千问（DashScope） - 阿里云大语言模型
- **Embeddings**: DashScopeEmbeddings - 文本向量化

### 文档处理

- **PDF**: PyPDF - PDF文档解析
- **Word**: python-docx, docx2txt - Word文档解析
- **Markdown**: unstructured - Markdown文档解析

### 安全认证

- **JWT**: python-jose - JSON Web Token
- **密码加密**: passlib with bcrypt - 密码哈希
- **加密**: cryptography - 敏感数据加密

### 其他工具

- **数据验证**: Pydantic 2.5+ - 数据模型和验证
- **数据库迁移**: Alembic - 数据库版本管理
- **定时任务**: APScheduler - 后台定时任务
- **速率限制**: slowapi - API速率限制
- **监控**: prometheus-client - 指标收集

## 🏗 系统架构

### 分层架构

系统采用经典的四层架构模式，确保代码的可维护性和可扩展性：

```
┌─────────────────────────────────────────────────────────┐
│                      API层 (API Layer)                   │
│  处理HTTP请求、参数验证、路由分发、响应序列化              │
└─────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────┐
│                   服务层 (Service Layer)                 │
│  实现业务逻辑、协调多个Repository、事务管理               │
└─────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────┐
│              数据访问层 (Repository Layer)                │
│  封装数据库操作、提供统一的数据访问接口                    │
└─────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────┐
│              基础设施层 (Infrastructure Layer)            │
│  数据库、缓存、向量存储、外部API、消息队列                 │
└─────────────────────────────────────────────────────────┘
```

### 项目目录结构

```
backend/
├── app/                          # 应用主目录
│   ├── main.py                   # FastAPI应用入口
│   ├── config.py                 # 配置管理
│   ├── dependencies.py           # 依赖注入
│   │
│   ├── api/                      # API路由层
│   │   └── v1/                   # API版本1
│   │       ├── auth.py           # 认证相关路由
│   │       ├── conversations.py  # 对话管理路由
│   │       ├── chat.py           # 聊天交互路由
│   │       ├── knowledge_bases.py # 知识库路由
│   │       ├── documents.py      # 文档管理路由
│   │       ├── rag.py            # RAG问答路由
│   │       ├── agent.py          # Agent相关路由
│   │       ├── quota.py          # 配额管理路由
│   │       └── system.py         # 系统管理路由
│   │
│   ├── services/                 # 服务层（业务逻辑）
│   │   ├── auth_service.py       # 认证服务
│   │   ├── conversation_service.py # 对话服务
│   │   ├── rag_service.py        # RAG服务
│   │   ├── agent_service.py      # Agent服务
│   │   ├── quota_service.py      # 配额服务
│   │   └── system_service.py     # 系统服务
│   │
│   ├── repositories/             # 数据访问层
│   │   ├── user_repository.py
│   │   ├── conversation_repository.py
│   │   ├── knowledge_base_repository.py
│   │   ├── agent_repository.py
│   │   └── quota_repository.py
│   │
│   ├── models/                   # 数据库模型（SQLAlchemy）
│   │   ├── user.py
│   │   ├── conversation.py
│   │   ├── message.py
│   │   ├── knowledge_base.py
│   │   ├── document.py
│   │   ├── agent_tool.py
│   │   ├── agent_execution.py
│   │   ├── api_usage.py
│   │   ├── user_quota.py
│   │   └── login_attempt.py
│   │
│   ├── schemas/                  # Pydantic模型（数据验证）
│   │   ├── auth.py
│   │   ├── conversation.py
│   │   ├── knowledge_base.py
│   │   ├── agent.py
│   │   ├── quota.py
│   │   └── system.py
│   │
│   ├── core/                     # 核心功能模块
│   │   ├── database.py           # 数据库连接
│   │   ├── redis.py              # Redis连接
│   │   ├── security.py           # 安全相关（JWT、密码加密）
│   │   ├── vector_store.py       # 向量数据库
│   │   └── llm.py                # LLM配置
│   │
│   ├── langchain_integration/    # LangChain集成
│   │   ├── chains.py             # 对话链
│   │   ├── rag_chain.py          # RAG链
│   │   ├── agent_executor.py     # Agent执行器
│   │   ├── document_loaders.py   # 文档加载器
│   │   └── tools/                # Agent工具
│   │       ├── calculator_tool.py
│   │       ├── search_tool.py
│   │       └── weather_tool.py
│   │
│   ├── tasks/                    # 后台任务
│   │   ├── document_tasks.py     # 文档处理任务
│   │   ├── quota_tasks.py        # 配额重置任务
│   │   └── cleanup_tasks.py      # 清理任务
│   │
│   ├── middleware/               # 中间件
│   │   ├── error_handler.py      # 错误处理
│   │   ├── rate_limiter.py       # 速率限制
│   │   ├── request_id.py         # 请求ID生成
│   │   └── prometheus_middleware.py # Prometheus监控
│   │
│   ├── websocket/                # WebSocket
│   │   ├── connection_manager.py # 连接管理
│   │   └── handlers.py           # WebSocket处理器
│   │
│   └── utils/                    # 工具函数
│       └── logger.py             # 日志配置
│
├── alembic/                      # 数据库迁移
│   ├── versions/                 # 迁移版本
│   │   ├── 001_initial_schema.py
│   │   └── ...
│   ├── env.py                    # Alembic环境配置
│   └── script.py.mako            # 迁移脚本模板
│
├── tests/                        # 测试
│   ├── conftest.py               # 测试配置
│   ├── test_auth.py
│   ├── test_conversation.py
│   ├── test_rag.py
│   └── test_agent.py
│
├── scripts/                      # 脚本
│   ├── init_db.py                # 初始化数据库
│   ├── seed_data.py              # 种子数据
│   ├── deploy.sh                 # 部署脚本
│   └── start.sh                  # 启动脚本
│
├── logs/                         # 日志文件
├── uploads/                      # 上传文件
├── vector_db/                    # 向量数据库
│
├── requirements.txt              # 生产依赖
├── requirements-dev.txt          # 开发依赖
├── .env.example                  # 环境变量模板
├── .env.docker                   # Docker环境变量
├── .gitignore
├── Dockerfile                    # Docker镜像
├── docker-compose.yml            # Docker Compose配置
├── alembic.ini                   # Alembic配置
└── README.md                     # 本文档
```

## 🚀 快速开始

### 前置要求

- Python 3.10+
- MySQL 8.0+
- Redis 7.0+
- 通义千问API密钥（[申请地址](https://dashscope.console.aliyun.com/)）

### 方式一：使用Docker Compose（推荐）

这是最快速的部署方式，适合开发和测试环境。

```bash
# 1. 克隆项目
git clone <repository-url>
cd backend

# 2. 配置环境变量
cp .env.docker .env
nano .env  # 编辑配置文件，至少填写 DASHSCOPE_API_KEY 和 SECRET_KEY

# 3. 启动所有服务（MySQL, Redis, Backend）
docker-compose up -d

# 4. 初始化数据库
docker-compose exec backend alembic upgrade head

# 5. 创建测试数据（可选）
docker-compose exec backend python scripts/seed_data.py

# 6. 访问服务
# API文档: http://localhost:8000/docs
# 健康检查: http://localhost:8000/api/v1/system/health
```

**测试账户**（使用种子数据后）：
- 管理员: `admin` / `Admin123456`
- 普通用户: `testuser` / `Test123456`

### 方式二：本地开发环境

适合需要修改代码的开发场景。

```bash
# 1. 创建虚拟环境
python -m venv venv

# 2. 激活虚拟环境
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate

# 3. 安装依赖
pip install -r requirements.txt
pip install -r requirements-dev.txt  # 开发依赖

# 4. 配置环境变量
cp .env.example .env
nano .env  # 编辑配置文件

# 5. 启动MySQL和Redis（使用Docker或本地安装）
docker run -d --name mysql -p 3306:3306 \
  -e MYSQL_ROOT_PASSWORD=rootpassword \
  -e MYSQL_DATABASE=ai_assistant \
  mysql:8.0

docker run -d --name redis -p 6379:6379 redis:7.0

# 6. 初始化数据库
alembic upgrade head

# 7. 创建测试数据（可选）
python scripts/seed_data.py

# 8. 启动开发服务器（支持热重载）
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 验证安装

```bash
# 1. 检查健康状态
curl http://localhost:8000/api/v1/system/health

# 2. 测试登录
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "Admin123456"}'

# 3. 访问API文档
# 浏览器打开: http://localhost:8000/docs
```

## 📦 安装部署

### 生产环境部署

#### 1. 使用部署脚本

```bash
# 赋予执行权限
chmod +x scripts/deploy.sh

# 初始化数据库
./scripts/deploy.sh init

# 启动服务
./scripts/deploy.sh start

# 查看日志
./scripts/deploy.sh logs

# 停止服务
./scripts/deploy.sh stop

# 重启服务
./scripts/deploy.sh restart

# 备份数据库
./scripts/deploy.sh backup

# 清理所有容器和数据（危险操作）
./scripts/deploy.sh clean
```

#### 2. 使用Gunicorn（生产环境）

```bash
# 安装Gunicorn
pip install gunicorn

# 启动服务（4个工作进程）
gunicorn app.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --timeout 120 \
  --access-logfile logs/access.log \
  --error-logfile logs/error.log \
  --log-level info
```

#### 3. 使用Systemd服务

创建 `/etc/systemd/system/ai-assistant.service`:

```ini
[Unit]
Description=AI Assistant Backend Service
After=network.target mysql.service redis.service

[Service]
Type=notify
User=www-data
Group=www-data
WorkingDirectory=/opt/ai-assistant/backend
Environment="PATH=/opt/ai-assistant/backend/venv/bin"
ExecStart=/opt/ai-assistant/backend/venv/bin/gunicorn app.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000
Restart=always

[Install]
WantedBy=multi-user.target
```

启动服务：

```bash
sudo systemctl daemon-reload
sudo systemctl enable ai-assistant
sudo systemctl start ai-assistant
sudo systemctl status ai-assistant
```

#### 4. Nginx反向代理

创建 `/etc/nginx/sites-available/ai-assistant`:

```nginx
upstream ai_assistant {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name api.example.com;

    # 重定向到HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name api.example.com;

    ssl_certificate /etc/ssl/certs/example.com.crt;
    ssl_certificate_key /etc/ssl/private/example.com.key;

    client_max_body_size 10M;

    location / {
        proxy_pass http://ai_assistant;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # WebSocket支持
    location /ws {
        proxy_pass http://ai_assistant;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # SSE流式响应
    location /api/v1/chat/stream {
        proxy_pass http://ai_assistant;
        proxy_set_header Connection '';
        proxy_http_version 1.1;
        chunked_transfer_encoding off;
        proxy_buffering off;
        proxy_cache off;
    }
}
```

启用配置：

```bash
sudo ln -s /etc/nginx/sites-available/ai-assistant /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

## ⚙️ 配置说明

### 环境变量

创建 `.env` 文件并配置以下变量：

#### 必需配置

```bash
# 通义千问API密钥（必填）
DASHSCOPE_API_KEY=sk-your-api-key-here

# JWT密钥（必填，建议使用强随机字符串）
SECRET_KEY=your-secret-key-here-at-least-32-characters

# MySQL配置
MYSQL_ROOT_PASSWORD=rootpassword
MYSQL_PASSWORD=ai_password
MYSQL_DATABASE=ai_assistant
MYSQL_USER=ai_user
```

#### 可选配置

```bash
# 应用配置
APP_NAME=AI智能助手系统
APP_VERSION=1.0.0
DEBUG=False
API_V1_PREFIX=/api/v1

# 数据库配置
DATABASE_URL=mysql+pymysql://ai_user:ai_password@localhost:3306/ai_assistant
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20
DB_POOL_RECYCLE=3600

# Redis配置
REDIS_URL=redis://localhost:6379/0
REDIS_PASSWORD=
REDIS_MAX_CONNECTIONS=50

# 向量数据库配置
VECTOR_DB_TYPE=chroma
VECTOR_DB_PATH=./vector_db

# LLM配置
DASHSCOPE_MODEL=qwen-turbo
DASHSCOPE_EMBEDDING_MODEL=text-embedding-v1
LLM_TEMPERATURE=0.7
LLM_MAX_TOKENS=2000

# JWT配置
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_DAYS=7
JWT_REFRESH_TOKEN_EXPIRE_DAYS=30

# 文件上传配置
UPLOAD_DIR=./uploads
MAX_UPLOAD_SIZE_MB=10
ALLOWED_FILE_TYPES=pdf,docx,doc,txt,md

# 配额配置
DEFAULT_MONTHLY_QUOTA=100000
QUOTA_WARNING_THRESHOLD=0.1

# 速率限制
RATE_LIMIT_LOGIN=5/minute
RATE_LIMIT_API=100/minute
RATE_LIMIT_LLM=20/minute

# 日志配置
LOG_LEVEL=INFO
LOG_FILE=./logs/app.log
LOG_MAX_SIZE=10485760
LOG_BACKUP_COUNT=10

# CORS配置
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
CORS_ALLOW_CREDENTIALS=True

# WebSocket配置
WS_HEARTBEAT_INTERVAL=30
WS_MAX_CONNECTIONS_PER_USER=3

# 安全配置
ACCOUNT_LOCKOUT_THRESHOLD=5
ACCOUNT_LOCKOUT_DURATION=900
PASSWORD_MIN_LENGTH=8

# 性能配置
WORKER_COUNT=4
WORKER_TIMEOUT=120
```

### 配置文件说明

完整的配置说明请参考：
- [CONFIG_USAGE.md](CONFIG_USAGE.md) - 配置使用指南
- [.env.example](.env.example) - 环境变量模板
- [.env.docker](.env.docker) - Docker环境变量模板

## 📚 API文档

### 访问文档

启动服务后，可以通过以下方式访问API文档：

- **Swagger UI（交互式）**: http://localhost:8000/docs
  - 提供交互式API测试界面
  - 可直接在浏览器中测试API
  - 包含请求/响应示例

- **ReDoc（美观）**: http://localhost:8000/redoc
  - 更美观的文档展示
  - 适合阅读和分享
  - 完整的API规范

- **OpenAPI JSON**: http://localhost:8000/openapi.json
  - 原始OpenAPI规范
  - 可用于生成客户端SDK
  - 可导入到Postman/Insomnia

### API概览

#### 认证相关

- `POST /api/v1/auth/register` - 用户注册
- `POST /api/v1/auth/login` - 用户登录
- `POST /api/v1/auth/refresh` - 刷新令牌
- `PUT /api/v1/auth/password` - 修改密码

#### 对话管理

- `POST /api/v1/conversations` - 创建对话
- `GET /api/v1/conversations` - 获取对话列表
- `GET /api/v1/conversations/{id}` - 获取对话详情
- `PUT /api/v1/conversations/{id}` - 更新对话
- `DELETE /api/v1/conversations/{id}` - 删除对话
- `GET /api/v1/conversations/{id}/messages` - 获取消息列表
- `GET /api/v1/conversations/{id}/export` - 导出对话

#### 聊天交互

- `POST /api/v1/chat/stream` - 流式对话（SSE）

#### 配额管理

- `GET /api/v1/quota` - 获取配额信息
- `PUT /api/v1/quota` - 更新配额（管理员）

#### 知识库管理

- `POST /api/v1/knowledge-bases` - 创建知识库
- `GET /api/v1/knowledge-bases` - 获取知识库列表
- `GET /api/v1/knowledge-bases/{id}` - 获取知识库详情
- `PUT /api/v1/knowledge-bases/{id}` - 更新知识库
- `DELETE /api/v1/knowledge-bases/{id}` - 删除知识库

#### 文档管理

- `POST /api/v1/documents/upload` - 上传文档
- `POST /api/v1/documents/upload-batch` - 批量上传文档
- `GET /api/v1/documents/{id}/status` - 获取文档处理状态
- `GET /api/v1/documents/{id}/preview` - 预览文档
- `DELETE /api/v1/documents/{id}` - 删除文档

#### RAG问答

- `POST /api/v1/rag/query` - RAG查询

#### Agent管理

- `GET /api/v1/agent/tools` - 获取工具列表
- `POST /api/v1/agent/tools` - 创建自定义工具
- `PUT /api/v1/agent/tools/{id}` - 更新工具
- `DELETE /api/v1/agent/tools/{id}` - 删除工具
- `POST /api/v1/agent/execute` - 执行任务
- `GET /api/v1/agent/executions/{id}` - 获取执行详情

#### 系统管理

- `GET /api/v1/system/health` - 健康检查
- `GET /api/v1/system/config` - 获取系统配置（管理员）
- `PUT /api/v1/system/config` - 更新系统配置（管理员）
- `GET /api/v1/system/stats` - 获取使用统计（管理员）

#### 监控

- `GET /metrics` - Prometheus指标

### 使用示例

详细的API使用示例请参考：
- [API_DOCUMENTATION.md](API_DOCUMENTATION.md) - 完整API文档
- [API_DOCS_QUICK_START.md](API_DOCS_QUICK_START.md) - API快速开始指南

#### 认证流程示例

```bash
# 1. 注册用户
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "Password123",
    "email": "test@example.com"
  }'

# 2. 登录获取令牌
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "Password123"
  }'

# 响应示例
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer",
  "expires_in": 604800
}

# 3. 使用令牌访问受保护的API
curl -X GET "http://localhost:8000/api/v1/conversations" \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc..."
```

#### 对话流程示例

```bash
# 1. 创建对话
curl -X POST "http://localhost:8000/api/v1/conversations" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"title": "Python学习"}'

# 2. 发送消息（流式响应）
curl -X POST "http://localhost:8000/api/v1/chat/stream" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "conversation_id": 1,
    "content": "什么是Python？",
    "config": {
      "temperature": 0.7,
      "max_tokens": 2000
    }
  }'
```

## 💻 开发指南

### 开发环境设置

```bash
# 1. 安装开发依赖
pip install -r requirements-dev.txt

# 2. 配置pre-commit钩子（可选）
pre-commit install

# 3. 启动开发服务器（支持热重载）
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 代码规范

项目遵循PEP 8规范，使用以下工具确保代码质量：

```bash
# 代码格式化（Black）
black app/

# 导入排序（isort）
isort app/

# 代码检查（Flake8）
flake8 app/ --max-line-length=100

# 类型检查（MyPy）
mypy app/

# 一键格式化和检查
black app/ && isort app/ && flake8 app/ && mypy app/
```

### 数据库迁移

使用Alembic管理数据库版本：

```bash
# 创建新迁移（自动生成）
alembic revision --autogenerate -m "描述变更内容"

# 创建空迁移（手动编写）
alembic revision -m "描述变更内容"

# 应用迁移
alembic upgrade head

# 回滚迁移
alembic downgrade -1

# 查看当前版本
alembic current

# 查看迁移历史
alembic history

# 回滚到特定版本
alembic downgrade <revision_id>
```

### 添加新功能

#### 1. 创建数据模型

```python
# app/models/example.py
from sqlalchemy import Column, Integer, String
from app.core.database import Base

class Example(Base):
    __tablename__ = "examples"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
```

#### 2. 创建Pydantic Schema

```python
# app/schemas/example.py
from pydantic import BaseModel

class ExampleCreate(BaseModel):
    name: str

class ExampleResponse(BaseModel):
    id: int
    name: str
    
    class Config:
        from_attributes = True
```

#### 3. 创建Repository

```python
# app/repositories/example_repository.py
from sqlalchemy.orm import Session
from app.models.example import Example

class ExampleRepository:
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, name: str) -> Example:
        example = Example(name=name)
        self.db.add(example)
        self.db.commit()
        self.db.refresh(example)
        return example
```

#### 4. 创建Service

```python
# app/services/example_service.py
from app.repositories.example_repository import ExampleRepository

class ExampleService:
    def __init__(self, repository: ExampleRepository):
        self.repository = repository
    
    async def create_example(self, name: str):
        return self.repository.create(name)
```

#### 5. 创建API路由

```python
# app/api/v1/example.py
from fastapi import APIRouter, Depends
from app.schemas.example import ExampleCreate, ExampleResponse
from app.services.example_service import ExampleService

router = APIRouter(prefix="/examples", tags=["examples"])

@router.post("/", response_model=ExampleResponse)
async def create_example(
    data: ExampleCreate,
    service: ExampleService = Depends()
):
    return await service.create_example(data.name)
```

### Git提交规范

遵循Conventional Commits规范：

```bash
# 格式
<type>(<scope>): <subject>

# 类型
feat:     新功能
fix:      修复bug
docs:     文档更新
style:    代码格式调整（不影响功能）
refactor: 代码重构
test:     测试相关
chore:    构建/工具链相关
perf:     性能优化

# 示例
feat(auth): 添加邮箱验证码功能
fix(rag): 修复文档处理失败的问题
docs(api): 更新API文档
refactor(service): 重构对话服务代码
test(auth): 添加登录测试用例
```

### 调试技巧

#### 1. 使用Python调试器

```python
# 在代码中添加断点
import pdb; pdb.set_trace()

# 或使用ipdb（更友好）
import ipdb; ipdb.set_trace()
```

#### 2. 查看日志

```bash
# 实时查看日志
tail -f logs/app.log

# 查看最近100行
tail -n 100 logs/app.log

# 搜索错误日志
grep "ERROR" logs/app.log
```

#### 3. 数据库调试

```bash
# 连接到MySQL
docker-compose exec mysql mysql -u root -p ai_assistant

# 查看表结构
DESCRIBE users;

# 查看数据
SELECT * FROM users LIMIT 10;
```

#### 4. Redis调试

```bash
# 连接到Redis
docker-compose exec redis redis-cli

# 查看所有键
KEYS *

# 查看键值
GET user:1

# 查看键的TTL
TTL user:1
```

## 🧪 测试

### 运行测试

```bash
# 运行所有测试
pytest

# 运行特定测试文件
pytest tests/test_auth.py

# 运行特定测试函数
pytest tests/test_auth.py::test_register

# 显示详细输出
pytest -v

# 显示print输出
pytest -s

# 并行运行测试
pytest -n auto

# 生成覆盖率报告
pytest --cov=app --cov-report=html

# 查看覆盖率报告
# 浏览器打开 htmlcov/index.html
```

### 测试结构

```python
# tests/conftest.py - 测试配置和fixtures
import pytest
from fastapi.testclient import TestClient
from app.main import app

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def test_user():
    return {
        "username": "testuser",
        "password": "Password123"
    }

# tests/test_auth.py - 认证测试
def test_register(client):
    response = client.post("/api/v1/auth/register", json={
        "username": "newuser",
        "password": "Password123"
    })
    assert response.status_code == 200
    assert "id" in response.json()

def test_login(client, test_user):
    response = client.post("/api/v1/auth/login", json=test_user)
    assert response.status_code == 200
    assert "access_token" in response.json()
```

### 测试覆盖率目标

- 整体覆盖率：> 80%
- 核心业务逻辑：> 90%
- API端点：100%

### 性能测试

使用Locust进行负载测试：

```python
# locustfile.py
from locust import HttpUser, task, between

class AIAssistantUser(HttpUser):
    wait_time = between(1, 3)
    
    def on_start(self):
        # 登录获取令牌
        response = self.client.post("/api/v1/auth/login", json={
            "username": "testuser",
            "password": "Password123"
        })
        self.token = response.json()["access_token"]
    
    @task(3)
    def get_conversations(self):
        self.client.get(
            "/api/v1/conversations",
            headers={"Authorization": f"Bearer {self.token}"}
        )
    
    @task(1)
    def create_conversation(self):
        self.client.post(
            "/api/v1/conversations",
            json={"title": "Test Conversation"},
            headers={"Authorization": f"Bearer {self.token}"}
        )
```

运行性能测试：

```bash
# 安装Locust
pip install locust

# 启动Locust
locust -f locustfile.py

# 访问Web界面
# http://localhost:8089
```

## ⚡ 性能优化

### 数据库优化

1. **索引优化**
   - 为常用查询字段添加索引
   - 使用复合索引优化多字段查询
   - 定期分析慢查询日志

2. **连接池配置**
   ```python
   # 根据负载调整连接池大小
   DB_POOL_SIZE=10
   DB_MAX_OVERFLOW=20
   DB_POOL_RECYCLE=3600
   ```

3. **查询优化**
   - 使用分页查询避免大量数据加载
   - 使用joinedload预加载关联数据
   - 避免N+1查询问题

### 缓存策略

1. **Redis缓存**
   ```python
   # 用户信息缓存（1小时）
   await redis.setex(f"user:{user_id}", 3600, user_json)
   
   # 对话列表缓存（10分钟）
   await redis.setex(f"conversations:{user_id}", 600, conversations_json)
   ```

2. **缓存更新策略**
   - Write-Through: 写入时更新缓存
   - Cache-Aside: 读取时检查缓存
   - 删除时清除相关缓存

### LLM调用优化

1. **流式输出**
   - 使用SSE实现流式响应
   - 减少首字响应时间
   - 提升用户体验

2. **批量处理**
   - 批量文档向量化
   - 减少API调用次数

3. **结果缓存**（可选）
   - 缓存常见问题的回答
   - 使用问题hash作为缓存键

### 异步处理

1. **文档处理异步化**
   - 使用BackgroundTasks处理文档
   - 通过WebSocket推送进度

2. **Agent执行异步化**
   - 长时间任务异步执行
   - 支持任务取消

## 🔧 故障排查

### 常见问题

#### 1. 服务无法启动

```bash
# 查看服务状态
docker-compose ps

# 查看服务日志
docker-compose logs backend

# 检查端口占用
netstat -tulpn | grep 8000
```

#### 2. 数据库连接失败

```bash
# 测试MySQL连接
docker-compose exec mysql mysql -u root -p -e "SELECT 1"

# 检查数据库配置
echo $DATABASE_URL

# 查看MySQL日志
docker-compose logs mysql
```

#### 3. Redis连接失败

```bash
# 测试Redis连接
docker-compose exec redis redis-cli ping

# 检查Redis配置
echo $REDIS_URL

# 查看Redis日志
docker-compose logs redis
```

#### 4. LLM API调用失败

```bash
# 检查API密钥
echo $DASHSCOPE_API_KEY

# 测试API连接
curl -X POST https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation \
  -H "Authorization: Bearer $DASHSCOPE_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"qwen-turbo","input":{"prompt":"你好"}}'
```

#### 5. 文档处理失败

```bash
# 查看文档处理日志
grep "document_id" logs/app.log

# 检查文件权限
ls -la uploads/

# 检查向量数据库
ls -la vector_db/
```

### 日志分析

```bash
# 查看错误日志
grep "ERROR" logs/app.log | tail -n 50

# 查看特定用户的日志
grep "user_id=1" logs/app.log

# 查看API调用日志
grep "POST /api/v1" logs/app.log

# 统计错误类型
grep "ERROR" logs/app.log | awk '{print $NF}' | sort | uniq -c
```

### 性能分析

```bash
# 查看慢查询
grep "slow query" logs/app.log

# 查看API响应时间
grep "duration" logs/app.log | awk '{print $NF}' | sort -n

# 查看内存使用
docker stats ai_assistant_backend
```

## 📖 相关文档

### 项目文档

- [QUICK_START.md](QUICK_START.md) - 快速开始指南
- [DEPLOYMENT.md](DEPLOYMENT.md) - 详细部署指南
- [API_DOCUMENTATION.md](API_DOCUMENTATION.md) - 完整API文档
- [API_DOCS_QUICK_START.md](API_DOCS_QUICK_START.md) - API快速开始
- [CONFIG_USAGE.md](CONFIG_USAGE.md) - 配置使用指南
- [DATABASE_SETUP.md](DATABASE_SETUP.md) - 数据库设置指南

### 功能实现文档

- [AGENT_IMPLEMENTATION_SUMMARY.md](AGENT_IMPLEMENTATION_SUMMARY.md) - Agent实现总结
- [CUSTOM_TOOLS_IMPLEMENTATION.md](CUSTOM_TOOLS_IMPLEMENTATION.md) - 自定义工具实现
- [WEBSOCKET_IMPLEMENTATION.md](WEBSOCKET_IMPLEMENTATION.md) - WebSocket实现
- [PROMETHEUS_IMPLEMENTATION.md](PROMETHEUS_IMPLEMENTATION.md) - Prometheus监控实现
- [RATE_LIMITER_IMPLEMENTATION.md](RATE_LIMITER_IMPLEMENTATION.md) - 速率限制实现
- [ERROR_HANDLER_IMPLEMENTATION.md](ERROR_HANDLER_IMPLEMENTATION.md) - 错误处理实现
- [LOGGER_IMPLEMENTATION.md](LOGGER_IMPLEMENTATION.md) - 日志实现
- [SCHEDULED_TASKS_IMPLEMENTATION.md](SCHEDULED_TASKS_IMPLEMENTATION.md) - 定时任务实现

### 外部资源

- [FastAPI官方文档](https://fastapi.tiangolo.com/)
- [LangChain官方文档](https://python.langchain.com/)
- [通义千问API文档](https://help.aliyun.com/zh/dashscope/)
- [SQLAlchemy文档](https://docs.sqlalchemy.org/)
- [Pydantic文档](https://docs.pydantic.dev/)

## 🤝 贡献指南

我们欢迎所有形式的贡献！

### 如何贡献

1. **Fork项目**
   ```bash
   # 在GitHub上Fork项目
   # 克隆你的Fork
   git clone https://github.com/your-username/ai-assistant.git
   cd ai-assistant/backend
   ```

2. **创建分支**
   ```bash
   git checkout -b feature/your-feature-name
   # 或
   git checkout -b fix/your-bug-fix
   ```

3. **开发和测试**
   ```bash
   # 安装开发依赖
   pip install -r requirements-dev.txt
   
   # 进行开发
   # ...
   
   # 运行测试
   pytest
   
   # 代码格式化
   black app/
   isort app/
   ```

4. **提交代码**
   ```bash
   git add .
   git commit -m "feat: 添加新功能"
   git push origin feature/your-feature-name
   ```

5. **创建Pull Request**
   - 在GitHub上创建Pull Request
   - 描述你的更改
   - 等待代码审查

### 代码审查标准

- 代码符合PEP 8规范
- 所有测试通过
- 测试覆盖率不降低
- 有适当的文档和注释
- 提交信息符合Conventional Commits规范

### 报告问题

如果你发现bug或有功能建议：

1. 检查是否已有相关Issue
2. 创建新Issue，包含：
   - 问题描述
   - 复现步骤
   - 期望行为
   - 实际行为
   - 环境信息（Python版本、操作系统等）

## 📄 许可证

本项目采用 MIT 许可证。详见 [LICENSE](LICENSE) 文件。

```
MIT License

Copyright (c) 2025 AI Assistant Team

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

## 👥 团队

- **项目负责人**: [Your Name]
- **核心开发者**: [Developer Names]
- **贡献者**: 查看 [CONTRIBUTORS.md](CONTRIBUTORS.md)

## 🙏 致谢

感谢以下开源项目：

- [FastAPI](https://fastapi.tiangolo.com/) - 现代化的Python Web框架
- [LangChain](https://www.langchain.com/) - LLM应用开发框架
- [SQLAlchemy](https://www.sqlalchemy.org/) - Python SQL工具包
- [Pydantic](https://pydantic.dev/) - 数据验证库
- [Alembic](https://alembic.sqlalchemy.org/) - 数据库迁移工具
- [通义千问](https://tongyi.aliyun.com/) - 阿里云大语言模型

## 📞 联系方式

- **项目主页**: https://github.com/your-org/ai-assistant
- **问题反馈**: https://github.com/your-org/ai-assistant/issues
- **邮箱**: support@example.com
- **文档**: https://docs.example.com

## 🗺 路线图

### v1.0.0（当前版本）
- ✅ 用户认证与授权
- ✅ 智能对话管理
- ✅ RAG知识库问答
- ✅ Agent智能代理
- ✅ 配额管理
- ✅ 系统监控

### v1.1.0（计划中）
- ⏳ 多模态支持（图片、音频）
- ⏳ 对话分享功能
- ⏳ 知识库协作
- ⏳ 更多内置工具
- ⏳ 性能优化

### v2.0.0（未来）
- 📋 多租户支持
- 📋 企业级权限管理
- 📋 高级分析和报表
- 📋 插件市场
- 📋 移动端支持

## 📊 项目状态

![Build Status](https://img.shields.io/badge/build-passing-brightgreen)
![Test Coverage](https://img.shields.io/badge/coverage-85%25-green)
![Python Version](https://img.shields.io/badge/python-3.10%2B-blue)
![License](https://img.shields.io/badge/license-MIT-yellow)

### 最近更新

- **2025-01-09**: 完成任务19.2 - API文档配置
- **2025-01-09**: 完成任务18 - Docker和部署配置
- **2025-01-09**: 完成任务17 - FastAPI应用配置
- **2025-01-09**: 完成任务16 - 日志和监控
- **2025-01-09**: 完成任务15 - 定时任务

查看完整的更新日志：[CHANGELOG.md](CHANGELOG.md)

## 🎯 快速链接

- [快速开始](#快速开始) - 5分钟快速部署
- [API文档](#api文档) - 完整的API参考
- [开发指南](#开发指南) - 开发者指南
- [部署指南](DEPLOYMENT.md) - 生产环境部署
- [故障排查](#故障排查) - 常见问题解决

---

<div align="center">

**[⬆ 回到顶部](#ai智能助手系统---后端)**

Made with ❤️ by AI Assistant Team

</div>
