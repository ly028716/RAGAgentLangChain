"""
直接测试工具文件 - 不依赖langchain包
"""
import sys
import os

# 添加backend目录到路径
sys.path.insert(0, os.path.dirname(__file__))

def test_search_tool_structure():
    """测试搜索工具的结构"""
    print("=" * 60)
    print("测试 SearchTool 结构")
    print("=" * 60)
    
    try:
        # 直接读取文件内容
        with open('app/langchain_integration/tools/search_tool.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查关键组件
        checks = [
            ('SearchInput类定义', 'class SearchInput(BaseModel):'),
            ('SearchTool类定义', 'class SearchTool(BaseTool):'),
            ('工具名称', 'name: str = "search"'),
            ('_run方法', 'def _run('),
            ('_arun方法', 'async def _arun('),
            ('_mock_search方法', 'def _mock_search('),
            ('_real_search方法', 'async def _real_search('),
            ('_format_results方法', 'def _format_results('),
        ]
        
        all_passed = True
        for check_name, check_str in checks:
            if check_str in content:
                print(f"✓ {check_name}")
            else:
                print(f"✗ {check_name} - 未找到")
                all_passed = False
        
        # 检查文档字符串
        if '"""搜索工具 - 用于网络搜索"""' in content:
            print("✓ 模块文档字符串")
        
        if all_passed:
            print("\n✓ SearchTool 结构测试通过!")
            return True
        else:
            print("\n✗ SearchTool 结构测试失败!")
            return False
        
    except Exception as e:
        print(f"\n✗ SearchTool 结构测试失败: {e}")
        return False


def test_weather_tool_structure():
    """测试天气工具的结构"""
    print("\n" + "=" * 60)
    print("测试 WeatherTool 结构")
    print("=" * 60)
    
    try:
        # 直接读取文件内容
        with open('app/langchain_integration/tools/weather_tool.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查关键组件
        checks = [
            ('WeatherInput类定义', 'class WeatherInput(BaseModel):'),
            ('WeatherTool类定义', 'class WeatherTool(BaseTool):'),
            ('工具名称', 'name: str = "weather"'),
            ('_run方法', 'def _run('),
            ('_arun方法', 'async def _arun('),
            ('_mock_weather方法', 'def _mock_weather('),
            ('_real_weather方法', 'async def _real_weather('),
            ('_format_weather方法', 'def _format_weather('),
            ('_validate_location方法', 'def _validate_location('),
        ]
        
        all_passed = True
        for check_name, check_str in checks:
            if check_str in content:
                print(f"✓ {check_name}")
            else:
                print(f"✗ {check_name} - 未找到")
                all_passed = False
        
        # 检查文档字符串
        if '"""天气查询工具 - 用于查询天气信息"""' in content:
            print("✓ 模块文档字符串")
        
        if all_passed:
            print("\n✓ WeatherTool 结构测试通过!")
            return True
        else:
            print("\n✗ WeatherTool 结构测试失败!")
            return False
        
    except Exception as e:
        print(f"\n✗ WeatherTool 结构测试失败: {e}")
        return False


def test_init_file():
    """测试__init__.py文件"""
    print("\n" + "=" * 60)
    print("测试 __init__.py 文件")
    print("=" * 60)
    
    try:
        with open('app/langchain_integration/tools/__init__.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        checks = [
            ('导入CalculatorTool', 'from .calculator_tool import CalculatorTool'),
            ('导入SearchTool', 'from .search_tool import SearchTool'),
            ('导入WeatherTool', 'from .weather_tool import WeatherTool'),
            ('__all__定义', '__all__ = ["CalculatorTool", "SearchTool", "WeatherTool"]'),
        ]
        
        all_passed = True
        for check_name, check_str in checks:
            if check_str in content:
                print(f"✓ {check_name}")
            else:
                print(f"✗ {check_name} - 未找到")
                all_passed = False
        
        if all_passed:
            print("\n✓ __init__.py 测试通过!")
            return True
        else:
            print("\n✗ __init__.py 测试失败!")
            return False
        
    except Exception as e:
        print(f"\n✗ __init__.py 测试失败: {e}")
        return False


def test_agent_executor_integration():
    """测试AgentExecutor集成"""
    print("\n" + "=" * 60)
    print("测试 AgentExecutor 集成")
    print("=" * 60)
    
    try:
        with open('app/langchain_integration/agent_executor.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        checks = [
            ('导入SearchTool', 'from app.langchain_integration.tools import CalculatorTool, SearchTool, WeatherTool'),
            ('SearchTool实例化', 'SearchTool()'),
            ('WeatherTool实例化', 'WeatherTool()'),
        ]
        
        all_passed = True
        for check_name, check_str in checks:
            if check_str in content:
                print(f"✓ {check_name}")
            else:
                print(f"✗ {check_name} - 未找到")
                all_passed = False
        
        if all_passed:
            print("\n✓ AgentExecutor 集成测试通过!")
            return True
        else:
            print("\n✗ AgentExecutor 集成测试失败!")
            return False
        
    except Exception as e:
        print(f"\n✗ AgentExecutor 集成测试失败: {e}")
        return False


def test_syntax():
    """测试Python语法"""
    print("\n" + "=" * 60)
    print("测试 Python 语法")
    print("=" * 60)
    
    import py_compile
    
    files = [
        'app/langchain_integration/tools/search_tool.py',
        'app/langchain_integration/tools/weather_tool.py',
        'app/langchain_integration/tools/__init__.py',
    ]
    
    all_passed = True
    for file_path in files:
        try:
            py_compile.compile(file_path, doraise=True)
            print(f"✓ {file_path}")
        except py_compile.PyCompileError as e:
            print(f"✗ {file_path} - 语法错误: {e}")
            all_passed = False
    
    if all_passed:
        print("\n✓ Python 语法测试通过!")
        return True
    else:
        print("\n✗ Python 语法测试失败!")
        return False


if __name__ == "__main__":
    print("开始测试新增的Agent工具...\n")
    
    results = []
    results.append(("SearchTool结构", test_search_tool_structure()))
    results.append(("WeatherTool结构", test_weather_tool_structure()))
    results.append(("__init__.py", test_init_file()))
    results.append(("AgentExecutor集成", test_agent_executor_integration()))
    results.append(("Python语法", test_syntax()))
    
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    
    for name, passed in results:
        status = "✓ 通过" if passed else "✗ 失败"
        print(f"{name}: {status}")
    
    all_passed = all(result[1] for result in results)
    
    if all_passed:
        print("\n🎉 所有测试通过!")
        print("\n实现总结:")
        print("1. ✓ 创建了 SearchTool (网络搜索工具)")
        print("2. ✓ 创建了 WeatherTool (天气查询工具)")
        print("3. ✓ 更新了 __init__.py 导出新工具")
        print("4. ✓ 更新了 AgentExecutor 集成新工具")
        print("5. ✓ 所有文件语法正确")
        sys.exit(0)
    else:
        print("\n⚠️  部分测试失败")
        sys.exit(1)
