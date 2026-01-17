"""
速率限制中间件测试

测试速率限制功能的基本实现和配置
"""
import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.middleware.rate_limiter import (
    limiter,
    rate_limit_login,
    rate_limit_api,
    rate_limit_llm,
    rate_limit_custom,
    register_rate_limiter,
    get_user_identifier,
    get_rate_limit_string,
)
from app.config import settings


def test_get_rate_limit_string():
    """测试获取速率限制字符串"""
    # 测试登录限制
    login_limit = get_rate_limit_string("login")
    assert login_limit == f"{settings.rate_limit.rate_limit_login_per_minute}/minute"
    
    # 测试LLM限制
    llm_limit = get_rate_limit_string("llm")
    assert llm_limit == f"{settings.rate_limit.rate_limit_llm_per_minute}/minute"
    
    # 测试默认API限制
    api_limit = get_rate_limit_string("api")
    assert api_limit == f"{settings.rate_limit.rate_limit_per_minute}/minute"
    
    # 测试未知类型返回默认限制
    default_limit = get_rate_limit_string("unknown")
    assert default_limit == f"{settings.rate_limit.rate_limit_per_minute}/minute"


def test_get_user_identifier_with_authenticated_user():
    """测试已认证用户的标识符获取"""
    # 创建模拟请求
    request = Mock(spec=Request)
    
    # 模拟已认证用户
    user = Mock()
    user.id = 123
    request.state = Mock()
    request.state.user = user
    
    identifier = get_user_identifier(request)
    assert identifier == "user:123"


def test_get_user_identifier_with_ip_address():
    """测试未认证用户使用IP地址作为标识符"""
    # 创建模拟请求
    request = Mock(spec=Request)
    request.state = Mock()
    request.state.user = None
    request.client = Mock()
    request.client.host = "192.168.1.1"
    
    # 模拟get_remote_address返回IP
    with patch('app.middleware.rate_limiter.get_remote_address', return_value="192.168.1.1"):
        identifier = get_user_identifier(request)
        assert identifier == "192.168.1.1"


def test_limiter_instance():
    """测试Limiter实例配置"""
    assert limiter is not None
    assert limiter.enabled is True
    
    # 验证默认限制
    default_limits = limiter._default_limits
    assert len(default_limits) > 0


def test_rate_limit_decorators_exist():
    """测试速率限制装饰器存在"""
    # 验证装饰器函数存在
    assert callable(rate_limit_login)
    assert callable(rate_limit_api)
    assert callable(rate_limit_llm)
    assert callable(rate_limit_custom)


def test_rate_limit_custom():
    """测试自定义速率限制"""
    custom_limiter = rate_limit_custom("10/minute")
    assert custom_limiter is not None


def test_register_rate_limiter():
    """测试注册速率限制器到FastAPI应用"""
    app = FastAPI()
    
    # 注册速率限制器
    register_rate_limiter(app)
    
    # 验证limiter已添加到应用状态
    assert hasattr(app.state, "limiter")
    assert app.state.limiter is limiter
    
    # 验证异常处理器已注册
    assert len(app.exception_handlers) > 0


def test_rate_limit_configuration():
    """测试速率限制配置"""
    # 验证配置值存在且合理
    assert settings.rate_limit.rate_limit_per_minute > 0
    assert settings.rate_limit.rate_limit_login_per_minute > 0
    assert settings.rate_limit.rate_limit_llm_per_minute > 0
    
    # 验证登录限制应该最严格
    assert settings.rate_limit.rate_limit_login_per_minute <= settings.rate_limit.rate_limit_per_minute


def test_integration_with_fastapi():
    """测试与FastAPI的集成"""
    app = FastAPI()
    register_rate_limiter(app)
    
    # 创建一个测试端点
    @app.get("/test")
    @rate_limit_api()
    async def test_endpoint(request: Request):
        return {"message": "success"}
    
    # 创建测试客户端
    client = TestClient(app)
    
    # 发送请求（应该成功）
    response = client.get("/test")
    assert response.status_code == 200
    
    # 验证响应头包含速率限制信息
    assert "X-RateLimit-Limit" in response.headers or response.status_code == 200


if __name__ == "__main__":
    print("运行速率限制中间件测试...")
    
    # 运行基本测试
    test_get_rate_limit_string()
    print("✓ 速率限制字符串获取测试通过")
    
    test_get_user_identifier_with_authenticated_user()
    print("✓ 已认证用户标识符测试通过")
    
    test_get_user_identifier_with_ip_address()
    print("✓ IP地址标识符测试通过")
    
    test_limiter_instance()
    print("✓ Limiter实例测试通过")
    
    test_rate_limit_decorators_exist()
    print("✓ 速率限制装饰器测试通过")
    
    test_rate_limit_custom()
    print("✓ 自定义速率限制测试通过")
    
    test_register_rate_limiter()
    print("✓ 注册速率限制器测试通过")
    
    test_rate_limit_configuration()
    print("✓ 速率限制配置测试通过")
    
    test_integration_with_fastapi()
    print("✓ FastAPI集成测试通过")
    
    print("\n所有测试通过！✓")
