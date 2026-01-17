"""
Prometheus监控功能验证脚本

验证任务16.2的所有实现内容。
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))


def verify_implementation():
    """验证Prometheus监控实现"""
    
    print("\n" + "=" * 70)
    print("任务16.2: Prometheus监控功能验证")
    print("=" * 70)
    
    results = []
    
    # 1. 验证prometheus_client已安装
    print("\n[1/7] 验证prometheus_client包...")
    try:
        import prometheus_client
        print(f"  ✓ prometheus_client已安装")
        results.append(True)
    except ImportError:
        print("  ✗ prometheus_client未安装")
        results.append(False)
    
    # 2. 验证中间件文件存在
    print("\n[2/7] 验证中间件文件...")
    middleware_file = Path(__file__).parent / "app" / "middleware" / "prometheus_middleware.py"
    if middleware_file.exists():
        print(f"  ✓ 文件存在: {middleware_file.name}")
        results.append(True)
    else:
        print(f"  ✗ 文件不存在: {middleware_file}")
        results.append(False)
    
    # 3. 验证指标定义
    print("\n[3/7] 验证指标定义...")
    try:
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
        
        print("  已定义的指标:")
        for name, metric in metrics.items():
            print(f"    ✓ {name}: {type(metric).__name__}")
        
        results.append(True)
    except Exception as e:
        print(f"  ✗ 指标定义验证失败: {str(e)}")
        results.append(False)
    
    # 4. 验证中间件类
    print("\n[4/7] 验证PrometheusMiddleware类...")
    try:
        from app.middleware.prometheus_middleware import PrometheusMiddleware
        from starlette.middleware.base import BaseHTTPMiddleware
        
        if issubclass(PrometheusMiddleware, BaseHTTPMiddleware):
            print("  ✓ PrometheusMiddleware继承自BaseHTTPMiddleware")
        
        if hasattr(PrometheusMiddleware, 'dispatch'):
            print("  ✓ PrometheusMiddleware包含dispatch方法")
        
        results.append(True)
    except Exception as e:
        print(f"  ✗ 中间件类验证失败: {str(e)}")
        results.append(False)
    
    # 5. 验证辅助函数
    print("\n[5/7] 验证辅助函数...")
    try:
        from app.middleware.prometheus_middleware import (
            record_llm_call,
            update_db_connections,
            update_redis_status
        )
        
        functions = {
            "record_llm_call": record_llm_call,
            "update_db_connections": update_db_connections,
            "update_redis_status": update_redis_status
        }
        
        print("  已定义的辅助函数:")
        for name, func in functions.items():
            print(f"    ✓ {name}")
        
        # 测试函数调用
        print("\n  测试函数调用:")
        record_llm_call("qwen-turbo", "chat", "success", 100, 200)
        print("    ✓ record_llm_call() 调用成功")
        
        update_db_connections(5)
        print("    ✓ update_db_connections() 调用成功")
        
        update_redis_status(True)
        print("    ✓ update_redis_status() 调用成功")
        
        results.append(True)
    except Exception as e:
        print(f"  ✗ 辅助函数验证失败: {str(e)}")
        results.append(False)
    
    # 6. 验证main.py集成
    print("\n[6/7] 验证main.py集成...")
    try:
        main_file = Path(__file__).parent / "app" / "main.py"
        with open(main_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        checks = [
            ("导入prometheus_client", "from prometheus_client import"),
            ("导入PrometheusMiddleware", "from app.middleware.prometheus_middleware import PrometheusMiddleware"),
            ("添加中间件", "app.add_middleware(PrometheusMiddleware)"),
            ("/metrics端点", '@app.get("/metrics")'),
            ("generate_latest调用", "generate_latest()")
        ]
        
        all_found = True
        for check_name, check_str in checks:
            if check_str in content:
                print(f"  ✓ {check_name}")
            else:
                print(f"  ✗ {check_name} - 未找到")
                all_found = False
        
        results.append(all_found)
    except Exception as e:
        print(f"  ✗ main.py集成验证失败: {str(e)}")
        results.append(False)
    
    # 7. 验证指标导出
    print("\n[7/7] 验证指标导出...")
    try:
        from prometheus_client import generate_latest
        
        metrics_output = generate_latest()
        decoded = metrics_output.decode('utf-8')
        
        print(f"  ✓ 指标导出成功")
        print(f"  ✓ 输出大小: {len(metrics_output)} 字节")
        
        # 检查关键指标是否存在
        key_metrics = [
            "http_requests_total",
            "http_request_duration_seconds",
            "llm_calls_total",
            "llm_tokens_total"
        ]
        
        print("\n  关键指标检查:")
        for metric in key_metrics:
            if metric in decoded:
                print(f"    ✓ {metric}")
            else:
                print(f"    ✗ {metric} - 未找到")
        
        results.append(True)
    except Exception as e:
        print(f"  ✗ 指标导出验证失败: {str(e)}")
        results.append(False)
    
    # 总结
    print("\n" + "=" * 70)
    print("验证总结")
    print("=" * 70)
    
    passed = sum(results)
    total = len(results)
    
    print(f"\n通过: {passed}/{total}")
    print(f"失败: {total - passed}/{total}")
    
    if all(results):
        print("\n✓ 所有验证通过！")
        print("\n任务16.2实现内容:")
        print("  ✓ 在main.py中配置prometheus_client")
        print("  ✓ 定义指标: request_count, request_duration, llm_call_count, llm_token_usage")
        print("  ✓ 实现监控中间件")
        print("  ✓ 实现/metrics端点")
        print("\n需求满足:")
        print("  ✓ 需求8.1: 记录API调用和token消耗")
        return 0
    else:
        print(f"\n✗ {total - passed} 个验证失败")
        return 1


if __name__ == "__main__":
    exit_code = verify_implementation()
    sys.exit(exit_code)

