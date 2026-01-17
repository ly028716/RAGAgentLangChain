"""
速率限制中间件简单测试

测试速率限制功能的基本实现和配置（不依赖pytest）
"""
import sys
import os
from unittest.mock import Mock

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.middleware.rate_limiter import (
    limiter,
    rate_limit_login,
    rate_limit_api,
    rate_limit_llm,
    rate_limit_custom,
    get_rate_limit_string,
)
from app.config import settings


def test_get_rate_limit_string():
    """测试获取速率限制字符串"""
    print("测试速率限制字符串获取...")
    
    # 测试登录限制
    login_limit = get_rate_limit_string("login")
    expected_login = f"{settings.rate_limit.rate_limit_login_per_minute}/minute"
    assert login_limit == expected_login, f"登录限制不匹配: {login_limit} != {expected_login}"
    print(f"  ✓ 登录限制: {login_limit}")
    
    # 测试LLM限制
    llm_limit = get_rate_limit_string("llm")
    expected_llm = f"{settings.rate_limit.rate_limit_llm_per_minute}/minute"
    assert llm_limit == expected_llm, f"LLM限制不匹配: {llm_limit} != {expected_llm}"
    print(f"  ✓ LLM限制: {llm_limit}")
    
    # 测试默认API限制
    api_limit = get_rate_limit_string("api")
    expected_api = f"{settings.rate_limit.rate_limit_per_minute}/minute"
    assert api_limit == expected_api, f"API限制不匹配: {api_limit} != {expected_api}"
    print(f"  ✓ API限制: {api_limit}")
    
    # 测试未知类型返回默认限制
    default_limit = get_rate_limit_string("unknown")
    assert default_limit == expected_api, f"默认限制不匹配: {default_limit} != {expected_api}"
    print(f"  ✓ 默认限制: {default_limit}")


def test_limiter_instance():
    """测试Limiter实例配置"""
    print("\n测试Limiter实例...")
    
    assert limiter is not None, "Limiter实例不存在"
    print(f"  ✓ Limiter实例已创建")
    
    assert limiter.enabled is True, "Limiter未启用"
    print(f"  ✓ Limiter已启用")
    
    # 验证默认限制
    default_limits = limiter._default_limits
    assert len(default_limits) > 0, "默认限制未设置"
    print(f"  ✓ 默认限制已设置: {default_limits}")


def test_rate_limit_decorators():
    """测试速率限制装饰器"""
    print("\n测试速率限制装饰器...")
    
    # 验证装饰器函数存在
    assert callable(rate_limit_login), "rate_limit_login不可调用"
    print(f"  ✓ rate_limit_login装饰器存在")
    
    assert callable(rate_limit_api), "rate_limit_api不可调用"
    print(f"  ✓ rate_limit_api装饰器存在")
    
    assert callable(rate_limit_llm), "rate_limit_llm不可调用"
    print(f"  ✓ rate_limit_llm装饰器存在")
    
    assert callable(rate_limit_custom), "rate_limit_custom不可调用"
    print(f"  ✓ rate_limit_custom装饰器存在")


def test_rate_limit_configuration():
    """测试速率限制配置"""
    print("\n测试速率限制配置...")
    
    # 验证配置值存在且合理
    assert settings.rate_limit.rate_limit_per_minute > 0, "API限制必须大于0"
    print(f"  ✓ API限制: {settings.rate_limit.rate_limit_per_minute}/分钟")
    
    assert settings.rate_limit.rate_limit_login_per_minute > 0, "登录限制必须大于0"
    print(f"  ✓ 登录限制: {settings.rate_limit.rate_limit_login_per_minute}/分钟")
    
    assert settings.rate_limit.rate_limit_llm_per_minute > 0, "LLM限制必须大于0"
    print(f"  ✓ LLM限制: {settings.rate_limit.rate_limit_llm_per_minute}/分钟")
    
    # 验证登录限制应该最严格
    assert settings.rate_limit.rate_limit_login_per_minute <= settings.rate_limit.rate_limit_per_minute, \
        "登录限制应该比普通API限制更严格"
    print(f"  ✓ 登录限制比普通API限制更严格")


def test_module_imports():
    """测试模块导入"""
    print("\n测试模块导入...")
    
    try:
        from app.middleware import (
            limiter,
            rate_limit_login,
            rate_limit_api,
            rate_limit_llm,
            rate_limit_custom,
            register_rate_limiter,
        )
        print(f"  ✓ 所有速率限制功能可从middleware模块导入")
    except ImportError as e:
        raise AssertionError(f"导入失败: {e}")


if __name__ == "__main__":
    print("=" * 60)
    print("速率限制中间件测试")
    print("=" * 60)
    
    try:
        test_get_rate_limit_string()
        test_limiter_instance()
        test_rate_limit_decorators()
        test_rate_limit_configuration()
        test_module_imports()
        
        print("\n" + "=" * 60)
        print("✓ 所有测试通过！")
        print("=" * 60)
        
    except AssertionError as e:
        print(f"\n✗ 测试失败: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ 测试错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
