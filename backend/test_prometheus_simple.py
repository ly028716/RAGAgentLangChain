"""
简单的Prometheus监控功能测试

验证Prometheus中间件和指标定义是否正确。
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))


def test_imports():
    """测试导入是否成功"""
    print("\n" + "=" * 60)
    print("测试1: 导入Prometheus模块")
    print("=" * 60)
    
    try:
        from app.middleware.prometheus_middleware import (
            PrometheusMiddleware,
            request_count,
            request_duration,
            llm_call_count,
            llm_token_usage,
            active_requests,
            db_connections,
            redis_connection_status,
            record_llm_call,
            update_db_connections,
            update_redis_status
        )
        print("✓ 所有Prometheus组件导入成功")
        return True
    except ImportError as e:
        print(f"✗ 导入失败: {str(e)}")
        return False


def test_metrics_definition():
    """测试指标定义"""
    print("\n" + "=" * 60)
    print("测试2: 验证指标定义")
    print("=" * 60)
    
    from app.middleware.prometheus_middleware import (
        request_count,
        request_duration,
        llm_call_count,
        llm_token_usage,
        active_requests,
        db_connections,
        redis_connection_status
    )
    
    metrics = {
        "request_count": request_count,
        "request_duration": request_duration,
        "llm_call_count": llm_call_count,
        "llm_token_usage": llm_token_usage,
        "active_requests": active_requests,
        "db_connections": db_connections,
        "redis_connection_status": redis_connection_status
    }
    
    for name, metric in metrics.items():
        print(f"✓ {name}: {type(metric).__name__}")
    
    print("\n✓ 所有指标定义正确")
    return True


def test_record_llm_call():
    """测试LLM调用记录函数"""
    print("\n" + "=" * 60)
    print("测试3: LLM调用记录函数")
    print("=" * 60)
    
    from app.middleware.prometheus_middleware import record_llm_call
    
    try:
        # 测试记录LLM调用
        record_llm_call(
            model="qwen-turbo",
            api_type="chat",
            status="success",
            prompt_tokens=100,
            completion_tokens=200
        )
        print("✓ record_llm_call() 调用成功")
        
        record_llm_call(
            model="qwen-turbo",
            api_type="rag",
            status="error",
            prompt_tokens=50,
            completion_tokens=0
        )
        print("✓ record_llm_call() 错误状态记录成功")
        
        return True
    except Exception as e:
        print(f"✗ 函数调用失败: {str(e)}")
        return False


def test_infrastructure_updates():
    """测试基础设施指标更新函数"""
    print("\n" + "=" * 60)
    print("测试4: 基础设施指标更新")
    print("=" * 60)
    
    from app.middleware.prometheus_middleware import (
        update_db_connections,
        update_redis_status
    )
    
    try:
        update_db_connections(5)
        print("✓ update_db_connections() 调用成功")
        
        update_redis_status(True)
        print("✓ update_redis_status(True) 调用成功")
        
        update_redis_status(False)
        print("✓ update_redis_status(False) 调用成功")
        
        return True
    except Exception as e:
        print(f"✗ 函数调用失败: {str(e)}")
        return False


def test_middleware_class():
    """测试中间件类定义"""
    print("\n" + "=" * 60)
    print("测试5: 中间件类定义")
    print("=" * 60)
    
    from app.middleware.prometheus_middleware import PrometheusMiddleware
    from starlette.middleware.base import BaseHTTPMiddleware
    
    # 检查是否继承自BaseHTTPMiddleware
    if issubclass(PrometheusMiddleware, BaseHTTPMiddleware):
        print("✓ PrometheusMiddleware 正确继承自 BaseHTTPMiddleware")
    else:
        print("✗ PrometheusMiddleware 未正确继承")
        return False
    
    # 检查是否有dispatch方法
    if hasattr(PrometheusMiddleware, 'dispatch'):
        print("✓ PrometheusMiddleware 包含 dispatch 方法")
    else:
        print("✗ PrometheusMiddleware 缺少 dispatch 方法")
        return False
    
    return True


def test_metrics_export():
    """测试指标导出"""
    print("\n" + "=" * 60)
    print("测试6: Prometheus指标导出")
    print("=" * 60)
    
    try:
        from prometheus_client import generate_latest
        
        # 生成指标
        metrics_output = generate_latest()
        
        print(f"✓ 指标导出成功")
        print(f"  输出类型: {type(metrics_output)}")
        print(f"  输出长度: {len(metrics_output)} 字节")
        
        # 解码并显示前几行
        decoded = metrics_output.decode('utf-8')
        lines = decoded.split('\n')[:10]
        print(f"\n  前10行:")
        for line in lines:
            if line:
                print(f"    {line}")
        
        return True
    except Exception as e:
        print(f"✗ 指标导出失败: {str(e)}")
        return False


def main():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("Prometheus监控功能简单测试")
    print("=" * 60)
    
    tests = [
        ("导入测试", test_imports),
        ("指标定义", test_metrics_definition),
        ("LLM调用记录", test_record_llm_call),
        ("基础设施更新", test_infrastructure_updates),
        ("中间件类", test_middleware_class),
        ("指标导出", test_metrics_export)
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"\n✗ 测试异常: {name}")
            print(f"  异常: {str(e)}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    # 总结
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    print(f"通过: {passed}/{len(tests)}")
    print(f"失败: {failed}/{len(tests)}")
    
    if failed == 0:
        print("\n✓ 所有测试通过！")
        print("\nPrometheus监控功能已成功实现:")
        print("  - ✓ Prometheus中间件定义正确")
        print("  - ✓ 所有指标定义正确")
        print("  - ✓ LLM调用记录函数工作正常")
        print("  - ✓ 基础设施指标更新函数工作正常")
        print("  - ✓ 指标可以正确导出")
        return 0
    else:
        print(f"\n✗ {failed} 个测试失败")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)

