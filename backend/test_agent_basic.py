"""
基础Agent功能测试

测试Agent工具和执行器的基本功能。
"""

import asyncio
from app.langchain_integration.tools.calculator_tool import CalculatorTool


async def test_calculator_tool():
    """测试计算器工具"""
    print("=" * 50)
    print("测试计算器工具")
    print("=" * 50)
    
    tool = CalculatorTool()
    
    # 测试基本运算
    test_cases = [
        ("2 + 2", "4"),
        ("10 * 5", "50"),
        ("100 / 4", "25"),
        ("2 ** 3", "8"),
        ("sqrt(16)", "4"),
        ("sin(0)", "0"),
        ("pi", "3.141592653589793"),
    ]
    
    print("\n测试用例:")
    for expression, expected in test_cases:
        result = tool._run(expression)
        status = "✓" if result == expected or result.startswith(expected[:5]) else "✗"
        print(f"{status} {expression} = {result} (期望: {expected})")
    
    print("\n测试错误处理:")
    error_cases = [
        ("1 / 0", "除数不能为零"),
        ("invalid", "语法错误"),
        ("", "表达式不能为空"),
    ]
    
    for expression, expected_error in error_cases:
        result = tool._run(expression)
        status = "✓" if expected_error in result else "✗"
        print(f"{status} {expression} -> {result}")


async def test_agent_manager():
    """测试Agent管理器"""
    print("\n" + "=" * 50)
    print("测试Agent管理器")
    print("=" * 50)
    
    try:
        from app.langchain_integration.agent_executor import AgentManager
        
        # 注意：这需要有效的API密钥才能运行
        print("\n创建AgentManager实例...")
        manager = AgentManager()
        
        print(f"✓ AgentManager创建成功")
        print(f"✓ 加载了 {len(manager.builtin_tools)} 个内置工具")
        
        # 获取可用工具
        tools = manager.get_available_tools()
        print("\n可用工具:")
        for tool in tools:
            print(f"  - {tool['name']}: {tool['description'][:50]}...")
        
        print("\n注意: 完整的Agent执行测试需要有效的DashScope API密钥")
        
    except Exception as e:
        print(f"✗ AgentManager测试失败: {str(e)}")
        print("  这可能是因为缺少API密钥或其他配置")


async def main():
    """主测试函数"""
    print("\n开始Agent基础功能测试\n")
    
    # 测试计算器工具
    await test_calculator_tool()
    
    # 测试Agent管理器
    await test_agent_manager()
    
    print("\n" + "=" * 50)
    print("测试完成")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(main())
