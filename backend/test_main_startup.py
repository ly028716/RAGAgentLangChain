"""
测试FastAPI应用启动配置

验证:
1. 应用可以正常创建
2. 所有路由已注册
3. 中间件已配置
4. 生命周期事件正常工作
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def test_app_creation():
    """测试应用创建"""
    print("测试1: 应用创建...")
    try:
        from app.main import app
        assert app is not None
        assert app.title == "AI智能助手系统"
        print("✓ 应用创建成功")
        return True
    except Exception as e:
        print(f"✗ 应用创建失败: {e}")
        return False


def test_routes_registered():
    """测试路由注册"""
    print("\n测试2: 路由注册...")
    try:
        from app.main import app
        
        # 获取所有路由
        routes = [route.path for route in app.routes]
        
        # 检查关键路由是否存在
        expected_routes = [
            "/",
            "/health",
            "/metrics",
            "/scheduler/jobs",
        ]
        
        # 检查API路由前缀
        api_routes = [r for r in routes if r.startswith("/api/v1")]
        
        print(f"  总路由数: {len(routes)}")
        print(f"  API路由数: {len(api_routes)}")
        
        for route in expected_routes:
            if route in routes:
                print(f"  ✓ {route}")
            else:
                print(f"  ✗ {route} 未找到")
                return False
        
        # 检查是否有API v1路由
        if len(api_routes) > 0:
            print(f"  ✓ API v1路由已注册 ({len(api_routes)}个)")
        else:
            print("  ✗ API v1路由未注册")
            return False
        
        print("✓ 路由注册成功")
        return True
    except Exception as e:
        print(f"✗ 路由注册检查失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_middleware_configured():
    """测试中间件配置"""
    print("\n测试3: 中间件配置...")
    try:
        from app.main import app
        
        # 检查中间件
        middleware_count = len(app.user_middleware)
        print(f"  中间件数量: {middleware_count}")
        
        # 检查是否有CORS中间件
        has_cors = any("CORS" in str(m) for m in app.user_middleware)
        if has_cors:
            print("  ✓ CORS中间件已配置")
        else:
            print("  ✗ CORS中间件未配置")
            return False
        
        # 检查是否有自定义中间件
        has_custom = any("RequestID" in str(m) or "Prometheus" in str(m) for m in app.user_middleware)
        if has_custom:
            print("  ✓ 自定义中间件已配置")
        else:
            print("  ⚠ 自定义中间件可能未配置")
        
        print("✓ 中间件配置成功")
        return True
    except Exception as e:
        print(f"✗ 中间件配置检查失败: {e}")
        return False


def test_lifespan_events():
    """测试生命周期事件"""
    print("\n测试4: 生命周期事件...")
    try:
        from app.main import app
        
        # 检查是否配置了lifespan
        if app.router.lifespan_context:
            print("  ✓ Lifespan事件已配置")
        else:
            print("  ✗ Lifespan事件未配置")
            return False
        
        print("✓ 生命周期事件配置成功")
        return True
    except Exception as e:
        print(f"✗ 生命周期事件检查失败: {e}")
        return False


def test_api_endpoints():
    """测试API端点"""
    print("\n测试5: API端点...")
    try:
        from app.main import app
        
        # 获取所有API路由
        api_routes = [route for route in app.routes if route.path.startswith("/api/v1")]
        
        # 按前缀分组
        route_groups = {}
        for route in api_routes:
            parts = route.path.split("/")
            if len(parts) >= 4:
                prefix = parts[3]  # /api/v1/{prefix}/...
                if prefix not in route_groups:
                    route_groups[prefix] = []
                route_groups[prefix].append(route.path)
        
        print(f"  API模块数: {len(route_groups)}")
        for prefix, routes in route_groups.items():
            print(f"  ✓ {prefix}: {len(routes)}个端点")
        
        # 检查关键模块
        expected_modules = ["auth", "conversations", "chat", "quota", "knowledge-bases", "documents", "rag", "agent", "system"]
        missing_modules = [m for m in expected_modules if m not in route_groups]
        
        if missing_modules:
            print(f"  ⚠ 缺少模块: {', '.join(missing_modules)}")
        else:
            print("  ✓ 所有核心模块已注册")
        
        print("✓ API端点检查完成")
        return True
    except Exception as e:
        print(f"✗ API端点检查失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """运行所有测试"""
    print("=" * 60)
    print("FastAPI应用启动配置测试")
    print("=" * 60)
    
    tests = [
        test_app_creation,
        test_routes_registered,
        test_middleware_configured,
        test_lifespan_events,
        test_api_endpoints,
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"\n测试执行失败: {e}")
            import traceback
            traceback.print_exc()
            results.append(False)
    
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"通过: {passed}/{total}")
    
    if passed == total:
        print("\n✓ 所有测试通过！")
        return 0
    else:
        print(f"\n✗ {total - passed} 个测试失败")
        return 1


if __name__ == "__main__":
    exit(main())
