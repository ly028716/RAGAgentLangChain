# 配置管理模块使用说明

## 概述

配置管理模块 (`app/config.py`) 使用 `pydantic-settings` 从环境变量加载配置，提供类型验证和默认值。

## 配置类结构

配置模块包含以下配置类：

- **AppSettings**: 应用基本配置（名称、版本、环境等）
- **DatabaseSettings**: 数据库连接配置
- **RedisSettings**: Redis缓存配置
- **JWTSettings**: JWT认证配置
- **SecuritySettings**: 安全相关配置
- **TongyiSettings**: 通义千问API配置
- **VectorDBSettings**: 向量数据库配置
- **FileStorageSettings**: 文件存储配置
- **DocumentProcessingSettings**: 文档处理配置
- **RAGSettings**: RAG问答配置
- **QuotaSettings**: 用户配额配置
- **RateLimitSettings**: 速率限制配置
- **LoggingSettings**: 日志配置
- **CORSSettings**: CORS跨域配置
- **MonitoringSettings**: 监控配置
- **BackgroundTaskSettings**: 后台任务配置
- **WebSocketSettings**: WebSocket配置

## 使用方法

### 1. 基本使用

```python
from app.config import settings

# 访问数据库配置
db_url = settings.database.database_url
pool_size = settings.database.db_pool_size

# 访问Redis配置
redis_url = settings.redis.redis_url

# 访问JWT配置
secret_key = settings.jwt.secret_key
expire_days = settings.jwt.access_token_expire_days

# 访问通义千问配置
api_key = settings.tongyi.dashscope_api_key
model_name = settings.tongyi.tongyi_model_name
```

### 2. 环境变量配置

在项目根目录创建 `.env` 文件（参考 `.env.example`）：

```bash
# 应用配置
APP_NAME=AI智能助手系统
DEBUG=False
ENVIRONMENT=production

# 数据库配置
DATABASE_URL=mysql+pymysql://user:password@localhost:3306/ai_assistant
DB_POOL_SIZE=10

# Redis配置
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=your_password

# JWT配置
SECRET_KEY=your-very-long-secret-key-at-least-32-characters
ACCESS_TOKEN_EXPIRE_DAYS=7

# 通义千问API
DASHSCOPE_API_KEY=your-api-key-here
```

### 3. 配置验证

```python
from app.config import settings

# 验证所有配置
if settings.validate_all():
    print("配置验证通过")
else:
    print("配置验证失败")

# 获取配置摘要
summary = settings.get_config_summary()
print(summary)
```

### 4. 在FastAPI中使用

```python
from fastapi import FastAPI, Depends
from app.config import settings

app = FastAPI(
    title=settings.app.app_name,
    version=settings.app.app_version,
    debug=settings.app.debug
)

# 配置CORS
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors.origins_list,
    allow_credentials=settings.cors.cors_allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 5. 在数据库连接中使用

```python
from sqlalchemy import create_engine
from app.config import settings

engine = create_engine(
    settings.database.database_url,
    pool_size=settings.database.db_pool_size,
    max_overflow=settings.database.db_max_overflow,
    pool_recycle=settings.database.db_pool_recycle,
)
```

### 6. 在Redis连接中使用

```python
import redis
from app.config import settings

redis_client = redis.from_url(
    settings.redis.redis_url,
    decode_responses=True
)
```

## 配置验证规则

### 数据库配置
- `database_url`: 必须以 mysql、postgresql 或 sqlite 开头
- `db_pool_size`: 1-50 之间
- `db_max_overflow`: 0-100 之间

### JWT配置
- `secret_key`: 至少32个字符
- `access_token_expire_days`: 1-365天
- `refresh_token_expire_days`: 1-365天

### 通义千问配置
- `dashscope_api_key`: 不能是默认值
- `tongyi_temperature`: 0.0-2.0 之间
- `tongyi_max_tokens`: 1-4000 之间

### 文件存储配置
- `max_upload_size_mb`: 1-100 MB

### 日志配置
- `log_level`: 必须是 DEBUG、INFO、WARNING、ERROR、CRITICAL 之一

## 配置优先级

1. 环境变量（最高优先级）
2. `.env` 文件
3. 代码中的默认值（最低优先级）

## 注意事项

1. **生产环境**: 务必修改默认的 `SECRET_KEY` 和 `DASHSCOPE_API_KEY`
2. **敏感信息**: 不要将 `.env` 文件提交到版本控制系统
3. **配置验证**: 应用启动时应调用 `settings.validate_all()` 验证配置
4. **类型安全**: 所有配置都有类型注解，IDE会提供自动完成和类型检查

## 扩展配置

如需添加新的配置项：

1. 创建新的配置类继承 `BaseSettings`
2. 在 `Settings` 类中添加该配置类的实例
3. 在 `.env.example` 中添加相应的环境变量说明

示例：

```python
class NewFeatureSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix='', case_sensitive=False)
    
    feature_enabled: bool = Field(default=True, description="功能开关")
    feature_param: str = Field(default="default", description="功能参数")

# 在Settings类中添加
class Settings:
    def __init__(self):
        # ... 其他配置
        self.new_feature = NewFeatureSettings()
```

## 测试

运行配置测试脚本：

```bash
cd backend
python test_config.py
```

这将显示所有配置的当前值和验证结果。
