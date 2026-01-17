"""
速率限制集成示例

展示如何在实际的FastAPI应用中集成和使用速率限制中间件
"""
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional

# 导入速率限制功能
from app.middleware import (
    register_rate_limiter,
    rate_limit_login,
    rate_limit_api,
    rate_limit_llm,
    rate_limit_custom,
)

# 创建FastAPI应用
app = FastAPI(
    title="AI智能助手系统",
    description="带速率限制的API示例",
    version="1.0.0"
)

# 注册速率限制器
register_rate_limiter(app)


# ============================================================================
# 数据模型
# ============================================================================

class LoginRequest(BaseModel):
    username: str
    password: str


class ChatMessage(BaseModel):
    content: str
    conversation_id: Optional[int] = None


class DocumentUpload(BaseModel):
    filename: str
    content: str


# ============================================================================
# 认证相关接口 - 使用严格的速率限制
# ============================================================================

@app.post("/api/v1/auth/register")
@rate_limit_login()  # 5次/分钟
async def register(request: LoginRequest):
    """
    用户注册接口
    
    速率限制: 5次/分钟（防止批量注册）
    """
    # 注册逻辑
    return {
        "message": "注册成功",
        "user_id": 1
    }


@app.post("/api/v1/auth/login")
@rate_limit_login()  # 5次/分钟
async def login(request: LoginRequest):
    """
    用户登录接口
    
    速率限制: 5次/分钟（防止暴力破解）
    """
    # 登录逻辑
    if request.username == "admin" and request.password == "password":
        return {
            "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
            "token_type": "bearer"
        }
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="用户名或密码错误"
    )


# ============================================================================
# 普通API接口 - 使用标准速率限制
# ============================================================================

@app.get("/api/v1/conversations")
@rate_limit_api()  # 100次/分钟
async def get_conversations():
    """
    获取对话列表
    
    速率限制: 100次/分钟（标准API限制）
    """
    return {
        "total": 10,
        "conversations": [
            {"id": 1, "title": "Python编程问题"},
            {"id": 2, "title": "数据库设计"},
        ]
    }


@app.get("/api/v1/knowledge-bases")
@rate_limit_api()  # 100次/分钟
async def get_knowledge_bases():
    """
    获取知识库列表
    
    速率限制: 100次/分钟（标准API限制）
    """
    return {
        "knowledge_bases": [
            {"id": 1, "name": "技术文档库"},
            {"id": 2, "name": "产品手册"},
        ]
    }


# ============================================================================
# LLM调用接口 - 使用中等速率限制
# ============================================================================

@app.post("/api/v1/chat")
@rate_limit_llm()  # 20次/分钟
async def chat(message: ChatMessage):
    """
    对话接口
    
    速率限制: 20次/分钟（控制LLM API成本）
    """
    # LLM调用逻辑
    return {
        "response": f"收到您的消息: {message.content}",
        "tokens_used": 150
    }


@app.post("/api/v1/rag/query")
@rate_limit_llm()  # 20次/分钟
async def rag_query(question: str, kb_ids: list[int]):
    """
    RAG问答接口
    
    速率限制: 20次/分钟（控制LLM API成本）
    """
    # RAG查询逻辑
    return {
        "answer": "这是基于知识库的回答",
        "sources": [
            {"document": "doc1.pdf", "similarity": 0.95}
        ]
    }


# ============================================================================
# 自定义速率限制接口
# ============================================================================

@app.post("/api/v1/documents/upload")
@rate_limit_custom("10/minute")  # 自定义: 10次/分钟
async def upload_document(doc: DocumentUpload):
    """
    文档上传接口
    
    速率限制: 10次/分钟（防止存储滥用）
    """
    return {
        "document_id": 1,
        "filename": doc.filename,
        "status": "processing"
    }


@app.post("/api/v1/documents/batch-upload")
@rate_limit_custom("5/minute")  # 自定义: 5次/分钟
async def batch_upload_documents(docs: list[DocumentUpload]):
    """
    批量文档上传接口
    
    速率限制: 5次/分钟（更严格的限制）
    """
    return {
        "uploaded": len(docs),
        "status": "processing"
    }


@app.post("/api/v1/agent/execute")
@rate_limit_custom("15/minute")  # 自定义: 15次/分钟
async def execute_agent_task(task: str):
    """
    Agent任务执行接口
    
    速率限制: 15次/分钟（平衡性能和成本）
    """
    return {
        "execution_id": 1,
        "task": task,
        "status": "running"
    }


# ============================================================================
# 无速率限制的接口（健康检查等）
# ============================================================================

@app.get("/health")
async def health_check():
    """
    健康检查接口
    
    无速率限制（监控需要频繁访问）
    """
    return {
        "status": "healthy",
        "version": "1.0.0"
    }


@app.get("/")
async def root():
    """
    根路径
    
    无速率限制
    """
    return {
        "message": "欢迎使用AI智能助手系统API",
        "docs": "/docs",
        "version": "1.0.0"
    }


# ============================================================================
# 多重限制示例
# ============================================================================

@app.post("/api/v1/premium/feature")
@rate_limit_custom("10/minute")   # 每分钟10次
@rate_limit_custom("100/hour")    # 每小时100次
async def premium_feature():
    """
    高级功能接口
    
    多重速率限制:
    - 每分钟10次
    - 每小时100次
    """
    return {
        "message": "高级功能执行成功"
    }


# ============================================================================
# 错误处理示例
# ============================================================================

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """全局异常处理"""
    return JSONResponse(
        status_code=500,
        content={
            "error": "服务器内部错误",
            "detail": str(exc)
        }
    )


# ============================================================================
# 启动说明
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    
    print("=" * 60)
    print("速率限制集成示例")
    print("=" * 60)
    print("\n配置的速率限制:")
    print("  - 登录接口: 5次/分钟")
    print("  - 普通API: 100次/分钟")
    print("  - LLM调用: 20次/分钟")
    print("  - 文档上传: 10次/分钟")
    print("  - 批量上传: 5次/分钟")
    print("  - Agent执行: 15次/分钟")
    print("\n访问 http://localhost:8000/docs 查看API文档")
    print("=" * 60)
    
    uvicorn.run(app, host="0.0.0.0", port=8000)
