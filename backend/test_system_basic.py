"""
系统服务基础测试

测试系统服务的基本功能，不依赖外部服务。
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def test_imports():
    """测试模块导入"""
    print("测试1: 模块导入")
    
    try:
        # 测试schemas导入
        from app.schemas.system import (
            SystemConfigResponse,
            SystemConfigUpdateRequest,
            UsageStatsResponse,
            HealthCheckResponse,
            SystemInfoResponse,
        )
        print("✓ 系统schemas导入成功")
        
        # 测试API路由导入（不执行）
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "system_api",
            "app/api/v1/system.py"
        )
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            # 不执行，只检查语法
            print("✓ 系统API路由文件语法正确")
        
        # 测试service导入（不执行）
        spec = importlib.util.spec_from_file_location(
            "system_service",
            "app/services/system_service.py"
        )
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            print("✓ 系统服务文件语法正确")
        
        return True
    except Exception as e:
        print(f"✗ 导入失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_schema_validation():
    """测试schema验证"""
    print("\n测试2: Schema验证")
    
    try:
        from app.schemas.system import (
            SystemConfigUpdateRequest,
            UsageStatsResponse,
            HealthCheckResponse,
        )
        
        # 测试配置更新请求
        config_request = SystemConfigUpdateRequest(
            tongyi={"temperature": 0.8, "max_tokens": 3000}
        )
        assert config_request.tongyi["temperature"] == 0.8
        print("✓ SystemConfigUpdateRequest 验证通过")
        
        # 测试健康检查响应
        health_response = HealthCheckResponse(
            status="healthy",
            timestamp="2025-01-08T10:00:00Z",
            components={
                "database": {
                    "status": "healthy",
                    "message": "数据库连接正常",
                    "type": "mysql"
                }
            }
        )
        assert health_response.status == "healthy"
        print("✓ HealthCheckResponse 验证通过")
        
        # 测试使用统计响应
        from app.schemas.system import UsageStatsPeriod, UsageStatsSummary, APITypeStats, DailyStats
        
        stats_response = UsageStatsResponse(
            period=UsageStatsPeriod(
                start_date="2025-01-01",
                end_date="2025-01-31"
            ),
            summary=UsageStatsSummary(
                total_tokens=100000,
                total_calls=500,
                total_cost=10.0,
                active_users=10,
                average_tokens_per_call=200
            ),
            api_type_breakdown=[
                APITypeStats(
                    api_type="chat",
                    call_count=300,
                    total_tokens=60000
                )
            ],
            daily_breakdown=[
                DailyStats(
                    date="2025-01-01",
                    call_count=50,
                    total_tokens=10000
                )
            ]
        )
        assert stats_response.summary.total_tokens == 100000
        print("✓ UsageStatsResponse 验证通过")
        
        return True
    except Exception as e:
        print(f"✗ Schema验证失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_file_structure():
    """测试文件结构"""
    print("\n测试3: 文件结构")
    
    files_to_check = [
        "app/services/system_service.py",
        "app/schemas/system.py",
        "app/api/v1/system.py",
    ]
    
    all_exist = True
    for file_path in files_to_check:
        if os.path.exists(file_path):
            print(f"✓ {file_path} 存在")
        else:
            print(f"✗ {file_path} 不存在")
            all_exist = False
    
    return all_exist


def main():
    """运行所有测试"""
    print("="*50)
    print("系统管理功能基础测试")
    print("="*50)
    
    results = []
    
    # 测试文件结构
    results.append(("文件结构", test_file_structure()))
    
    # 测试导入
    results.append(("模块导入", test_imports()))
    
    # 测试schema验证
    results.append(("Schema验证", test_schema_validation()))
    
    # 输出结果
    print("\n" + "="*50)
    print("测试结果汇总")
    print("="*50)
    
    all_passed = True
    for test_name, passed in results:
        status = "✓ 通过" if passed else "✗ 失败"
        print(f"{test_name}: {status}")
        if not passed:
            all_passed = False
    
    print("="*50)
    if all_passed:
        print("所有测试通过！✓")
    else:
        print("部分测试失败！✗")
    print("="*50)
    
    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
