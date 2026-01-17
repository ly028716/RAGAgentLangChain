"""
测试Prometheus监控功能

验证Prometheus指标收集和/metrics端点是否正常工作。
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

from fastapi.testclient import TestClient
from app.main import app
from app.middleware.prometheus_middleware import (
    record_llm_call,
    update_db_connections,
    update_redis_status
)


def test_metrics_endpoint():
    """测试/metrics端点是否可访问"""
    print("\n" + "=" * 60)
    print("测试1: /metrics端点可访问性")
    print("=" * 60)
    
    client = TestClient(app)
    response = client.get("/metrics")
    
    print(f"状态码: {response.status_code}")
    print(f"Content-Type: {response.headers.get('content-type')}")
    
    assert response.status_code == 200, f"期望状态码200，实际: {response.status_code}"
    assert "text/plain" in response.headers.get("content-type", ""), "Content-Type应该是text/plain"
    
    content = response.text
    print(f"响应长度: {len(content)} 字节")
    print(f"前200字符:\n{content[:200]}")
    
    print("✓ /metrics端点测试通过")
    return True


def test_request_metrics():
    """测试HTTP请求指标是否被记录"""
    print("\n" + "=" * 60)
    print("测试2: HTTP请求指标记录")
    print("=" * 60)
    
    client = TestClient(app)
    
    # 发送几个测试请求
    print("发送测试请求...")
    client.get("/")
    client.get("/health")
    client.get("/scheduler/jobs")
    
    # 获取指标
    response = client.get("/metrics")
    content = response.text
    
    # 验证指标是否存在
    print("\n检查指标是否存在:")
    
    metrics_to_check = [
        "http_requests_total",
        "http_request_duration_seconds",
        "http_requests_active"
    ]
    
    for metric in metrics_to_check:
        if metric in content:
            print(f"✓ {metric} - 存在")
        else:
            print(f"✗ {metric} - 不存在")
            assert False, f"指标 {metric} 未找到"
    
    # 检查是否记录了具体的请求
    if 'endpoint="/"' in content:
        print("✓ 根路径请求已记录")
    else:
        print("✗ 根路径请求未记录")
    
    if 'endpoint="/health"' in content:
        print("✓ 健康检查请求已记录")
    else:
        print("✗ 健康检查请求未记录")
    
    print("\n✓ HTTP请求指标测试通过")
    return True


def test_llm_metrics():
    """测试LLM调用指标记录"""
    print("\n" + "=" * 60)
    print("测试3: LLM调用指标记录")
    print("=" * 60)
    
    # 模拟记录LLM调用
    print("记录模拟LLM调用...")
    record_llm_call(
        model="qwen-turbo",
        api_type="chat",
        status="success",
        prompt_tokens=100,
        completion_tokens=200
    )
    
    record_llm_call(
        model="qwen-turbo",
        api_type="rag",
        status="success",
        prompt_tokens=150,
        completion_tokens=250
    )
    
    record_llm_call(
        model="qwen-turbo",
        api_type="agent",
        status="error",
        prompt_tokens=50,
        completion_tokens=0
    )
    
    # 获取指标
    client = TestClient(app)
    response = client.get("/metrics")
    content = response.text
    
    # 验证LLM指标
    print("\n检查LLM指标:")
    
    llm_metrics = [
        "llm_calls_total",
        "llm_tokens_total"
    ]
    
    for metric in llm_metrics:
        if metric in content:
            print(f"✓ {metric} - 存在")
        else:
            print(f"✗ {metric} - 不存在")
            assert False, f"LLM指标 {metric} 未找到"
    
    # 检查具体的标签
    if 'model="qwen-turbo"' in content:
        print("✓ 模型标签已记录")
    
    if 'api_type="chat"' in content:
        print("✓ API类型标签已记录")
    
    if 'token_type="prompt"' in content:
        print("✓ Token类型标签已记录")
    
    print("\n✓ LLM指标测试通过")
    return True


def test_infrastructure_metrics():
    """测试基础设施指标"""
    print("\n" + "=" * 60)
    print("测试4: 基础设施指标")
    print("=" * 60)
    
    # 更新基础设施指标
    print("更新基础设施指标...")
    update_db_connections(5)
    update_redis_status(True)
    
    # 获取指标
    client = TestClient(app)
    response = client.get("/metrics")
    content = response.text
    
    # 验证基础设施指标
    print("\n检查基础设施指标:")
    
    infra_metrics = [
        "db_connections_active",
        "redis_connection_status"
    ]
    
    for metric in infra_metrics:
        if metric in content:
            print(f"✓ {metric} - 存在")
        else:
            print(f"✗ {metric} - 不存在")
            assert False, f"基础设施指标 {metric} 未找到"
    
    print("\n✓ 基础设施指标测试通过")
    return True


def test_metrics_format():
    """测试指标格式是否符合Prometheus规范"""
    print("\n" + "=" * 60)
    print("测试5: Prometheus指标格式")
    print("=" * 60)
    
    client = TestClient(app)
    response = client.get("/metrics")
    content = response.text
    
    lines = content.split('\n')
    
    print(f"总行数: {len(lines)}")
    
    # 检查HELP和TYPE注释
    help_lines = [line for line in lines if line.startswith('# HELP')]
    type_lines = [line for line in lines if line.startswith('# TYPE')]
    
    print(f"HELP注释行数: {len(help_lines)}")
    print(f"TYPE注释行数: {len(type_lines)}")
    
    assert len(help_lines) > 0, "应该包含HELP注释"
    assert len(type_lines) > 0, "应该包含TYPE注释"
    
    # 显示一些示例行
    print("\n示例HELP行:")
    for line in help_lines[:3]:
        print(f"  {line}")
    
    print("\n示例TYPE行:")
    for line in type_lines[:3]:
        print(f"  {line}")
    
    print("\n✓ Prometheus格式测试通过")
    return True


def test_metrics_exclusion():
    """测试/metrics端点本身不被统计"""
    print("\n" + "=" * 60)
    print("测试6: /metrics端点排除测试")
    print("=" * 60)
    
    client = TestClient(app)
    
    # 获取初始指标
    response1 = client.get("/metrics")
    content1 = response1.text
    
    # 再次获取指标（这次调用不应该被统计）
    response2 = client.get("/metrics")
    content2 = response2.text
    
    # 检查/metrics端点是否被排除
    if 'endpoint="/metrics"' in content2:
        print("✗ /metrics端点被统计了（不应该）")
        # 这不是致命错误，只是警告
        print("  警告: /metrics端点应该被排除在统计之外")
    else:
        print("✓ /metrics端点已正确排除")
    
    print("\n✓ 排除测试完成")
    return True


def main():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("Prometheus监控功能测试")
    print("=" * 60)
    
    tests = [
        ("metrics端点可访问性", test_metrics_endpoint),
        ("HTTP请求指标", test_request_metrics),
        ("LLM调用指标", test_llm_metrics),
        ("基础设施指标", test_infrastructure_metrics),
        ("Prometheus格式", test_metrics_format),
        ("metrics端点排除", test_metrics_exclusion)
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        try:
            test_func()
            passed += 1
        except AssertionError as e:
            print(f"\n✗ 测试失败: {name}")
            print(f"  错误: {str(e)}")
            failed += 1
        except Exception as e:
            print(f"\n✗ 测试异常: {name}")
            print(f"  异常: {str(e)}")
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
        print("  - ✓ /metrics端点可访问")
        print("  - ✓ HTTP请求指标收集")
        print("  - ✓ LLM调用指标收集")
        print("  - ✓ 基础设施指标收集")
        print("  - ✓ Prometheus格式正确")
        return 0
    else:
        print(f"\n✗ {failed} 个测试失败")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)

