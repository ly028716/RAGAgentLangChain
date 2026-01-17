"""
验证Agent实现的代码结构

检查所有必需的文件和类是否存在。
"""

import os
import ast
import sys


def check_file_exists(filepath):
    """检查文件是否存在"""
    exists = os.path.exists(filepath)
    status = "✓" if exists else "✗"
    print(f"{status} {filepath}")
    return exists


def check_class_in_file(filepath, class_name):
    """检查文件中是否定义了指定的类"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            tree = ast.parse(f.read())
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name == class_name:
                print(f"  ✓ 找到类: {class_name}")
                return True
        
        print(f"  ✗ 未找到类: {class_name}")
        return False
    except Exception as e:
        print(f"  ✗ 解析文件失败: {str(e)}")
        return False


def check_function_in_file(filepath, function_name):
    """检查文件中是否定义了指定的函数（包括async函数）"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            tree = ast.parse(f.read())
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == function_name:
                func_type = "async函数" if isinstance(node, ast.AsyncFunctionDef) else "函数"
                print(f"  ✓ 找到{func_type}: {function_name}")
                return True
        
        print(f"  ✗ 未找到函数: {function_name}")
        return False
    except Exception as e:
        print(f"  ✗ 解析文件失败: {str(e)}")
        return False


def main():
    """主验证函数"""
    print("=" * 60)
    print("验证Agent功能实现")
    print("=" * 60)
    
    all_passed = True
    
    # 检查工具目录和文件
    print("\n1. 检查工具实现 (Task 11.1)")
    print("-" * 60)
    
    tools_dir = "app/langchain_integration/tools"
    if check_file_exists(tools_dir):
        if check_file_exists(f"{tools_dir}/__init__.py"):
            if check_file_exists(f"{tools_dir}/calculator_tool.py"):
                all_passed &= check_class_in_file(
                    f"{tools_dir}/calculator_tool.py",
                    "CalculatorTool"
                )
    else:
        all_passed = False
    
    # 检查Agent执行器
    print("\n2. 检查Agent执行器 (Task 11.2)")
    print("-" * 60)
    
    executor_file = "app/langchain_integration/agent_executor.py"
    if check_file_exists(executor_file):
        all_passed &= check_class_in_file(executor_file, "AgentManager")
        all_passed &= check_class_in_file(executor_file, "StepRecordingCallback")
    else:
        all_passed = False
    
    # 检查Agent服务
    print("\n3. 检查Agent服务 (Task 11.3)")
    print("-" * 60)
    
    service_file = "app/services/agent_service.py"
    if check_file_exists(service_file):
        all_passed &= check_class_in_file(service_file, "AgentService")
    else:
        all_passed = False
    
    # 检查Agent API路由
    print("\n4. 检查Agent API路由 (Task 11.4)")
    print("-" * 60)
    
    api_file = "app/api/v1/agent.py"
    if check_file_exists(api_file):
        # 检查关键端点函数
        all_passed &= check_function_in_file(api_file, "get_tools")
        all_passed &= check_function_in_file(api_file, "create_tool")
        all_passed &= check_function_in_file(api_file, "execute_task")
        all_passed &= check_function_in_file(api_file, "get_executions")
    else:
        all_passed = False
    
    # 检查Agent schemas
    print("\n5. 检查Agent Schemas")
    print("-" * 60)
    
    schema_file = "app/schemas/agent.py"
    if check_file_exists(schema_file):
        all_passed &= check_class_in_file(schema_file, "ToolCreate")
        all_passed &= check_class_in_file(schema_file, "TaskExecuteRequest")
        all_passed &= check_class_in_file(schema_file, "ExecutionResponse")
    else:
        all_passed = False
    
    # 检查路由注册
    print("\n6. 检查路由注册")
    print("-" * 60)
    
    init_file = "app/api/v1/__init__.py"
    if check_file_exists(init_file):
        with open(init_file, 'r', encoding='utf-8') as f:
            content = f.read()
            if "agent_router" in content:
                print("  ✓ agent_router 已导入")
                if "include_router(agent_router)" in content:
                    print("  ✓ agent_router 已注册")
                else:
                    print("  ✗ agent_router 未注册")
                    all_passed = False
            else:
                print("  ✗ agent_router 未导入")
                all_passed = False
    else:
        all_passed = False
    
    # 总结
    print("\n" + "=" * 60)
    if all_passed:
        print("✓ 所有检查通过！Agent功能实现完整。")
    else:
        print("✗ 部分检查未通过，请检查上述错误。")
    print("=" * 60)
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
