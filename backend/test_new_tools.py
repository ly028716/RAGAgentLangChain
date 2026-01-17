"""
简单测试脚本 - 验证新工具的基本功能
"""
import sys
import os

# 添加backend目录到路径
sys.path.insert(0, os.path.dirname(__file__))

def test_search_tool():
    """测试搜索工具"""
    print("=" * 60)
    print("测试 SearchTool")
    print("=" * 60)
    
    try:
        from app.langchain_integration.tools.search_tool import SearchTool
        
        tool = SearchTool()
        print(f"✓ 工具名称: {tool.name}")
        print(f"✓ 工具描述: {tool.description[:80]}...")
        
        # 测试同步执行
        result = tool._run("Python编程", max_results=3)
        print(f"\n搜索结果预览:")
        print(result[:200] + "..." if len(result) > 200 else result)
        
        print("\n✓ SearchTool 测试通过!")
        return True
        
    except Exception as e:
        print(f"\n✗ SearchTool 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_weather_tool():
    """测试天气工具"""
    print("\n" + "=" * 60)
    print("测试 WeatherTool")
    print("=" * 60)
    
    try:
        from app.langchain_integration.tools.weather_tool import WeatherTool
        
        tool = WeatherTool()
        print(f"✓ 工具名称: {tool.name}")
        print(f"✓ 工具描述: {tool.description[:80]}...")
        
        # 测试同步执行
        result = tool._run("北京", days=2)
        print(f"\n天气查询结果预览:")
        print(result[:300] + "..." if len(result) > 300 else result)
        
        print("\n✓ WeatherTool 测试通过!")
        return True
        
    except Exception as e:
        print(f"\n✗ WeatherTool 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_tools_integration():
    """测试工具集成"""
    print("\n" + "=" * 60)
    print("测试工具集成")
    print("=" * 60)
    
    try:
        from app.langchain_integration.tools import CalculatorTool, SearchTool, WeatherTool
        
        tools = [CalculatorTool(), SearchTool(), WeatherTool()]
        
        print(f"✓ 成功导入 {len(tools)} 个工具:")
        for tool in tools:
            print(f"  - {tool.name}: {tool.description[:60]}...")
        
        print("\n✓ 工具集成测试通过!")
        return True
        
    except Exception as e:
        print(f"\n✗ 工具集成测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("开始测试新增的Agent工具...\n")
    
    results = []
    results.append(("SearchTool", test_search_tool()))
    results.append(("WeatherTool", test_weather_tool()))
    results.append(("工具集成", test_tools_integration()))
    
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    
    for name, passed in results:
        status = "✓ 通过" if passed else "✗ 失败"
        print(f"{name}: {status}")
    
    all_passed = all(result[1] for result in results)
    
    if all_passed:
        print("\n🎉 所有测试通过!")
        sys.exit(0)
    else:
        print("\n⚠️  部分测试失败")
        sys.exit(1)
