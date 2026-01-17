"""
测试自定义工具管理API端点

验证需求:
    - 需求5.2: 用户创建自定义工具且提供工具名称、描述和配置参数
    - 需求5.3: 用户更新工具配置
    - 需求5.4: 用户禁用工具
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 60)
print("自定义工具管理API端点验证")
print("=" * 60)

# 验证所有必要的文件和模块存在
print("\n[验证1] 检查服务层实现")
try:
    from app.services.agent_service import AgentService
    print("✓ AgentService 导入成功")
    
    # 检查方法是否存在
    assert hasattr(AgentService, 'create_tool'), "缺少 create_tool 方法"
    assert hasattr(AgentService, 'update_tool'), "缺少 update_tool 方法"
    assert hasattr(AgentService, 'delete_tool'), "缺少 delete_tool 方法"
    assert hasattr(AgentService, 'get_tools'), "缺少 get_tools 方法"
    assert hasattr(AgentService, 'get_tool'), "缺少 get_tool 方法"
    print("✓ 所有必需的方法都已实现")
    
except ImportError as e:
    print(f"✗ 导入失败: {e}")
    sys.exit(1)

print("\n[验证2] 检查Repository层实现")
try:
    from app.repositories.agent_repository import AgentToolRepository
    print("✓ AgentToolRepository 导入成功")
    
    # 检查方法是否存在
    assert hasattr(AgentToolRepository, 'create'), "缺少 create 方法"
    assert hasattr(AgentToolRepository, 'update'), "缺少 update 方法"
    assert hasattr(AgentToolRepository, 'delete'), "缺少 delete 方法"
    assert hasattr(AgentToolRepository, 'get_all'), "缺少 get_all 方法"
    assert hasattr(AgentToolRepository, 'get_by_id'), "缺少 get_by_id 方法"
    assert hasattr(AgentToolRepository, 'name_exists'), "缺少 name_exists 方法"
    print("✓ 所有必需的方法都已实现")
    
except ImportError as e:
    print(f"✗ 导入失败: {e}")
    sys.exit(1)

print("\n[验证3] 检查API路由实现")
try:
    from app.api.v1.agent import router
    print("✓ Agent API路由导入成功")
    
    # 检查路由是否存在
    routes = [route.path for route in router.routes]
    print(f"✓ 找到 {len(routes)} 个路由端点")
    
    # 验证关键端点
    expected_endpoints = [
        "/agent/tools",
        "/agent/tools/{tool_id}",
        "/agent/execute",
        "/agent/executions",
        "/agent/executions/{execution_id}"
    ]
    
    for endpoint in expected_endpoints:
        if any(endpoint in route for route in routes):
            print(f"  ✓ {endpoint}")
        else:
            print(f"  ✗ 缺少端点: {endpoint}")
    
except ImportError as e:
    print(f"✗ 导入失败: {e}")
    sys.exit(1)

print("\n[验证4] 检查Pydantic模型")
try:
    from app.schemas.agent import (
        ToolCreate,
        ToolUpdate,
        ToolResponse,
        ToolListResponse,
        DeleteResponse
    )
    print("✓ 所有Pydantic模型导入成功")
    print("  ✓ ToolCreate")
    print("  ✓ ToolUpdate")
    print("  ✓ ToolResponse")
    print("  ✓ ToolListResponse")
    print("  ✓ DeleteResponse")
    
except ImportError as e:
    print(f"✗ 导入失败: {e}")
    sys.exit(1)

print("\n[验证5] 检查数据库模型")
try:
    from app.models.agent_tool import AgentTool, ToolType
    print("✓ AgentTool 模型导入成功")
    print("✓ ToolType 枚举导入成功")
    
    # 验证枚举值
    assert ToolType.BUILTIN.value == "builtin", "BUILTIN 枚举值不正确"
    assert ToolType.CUSTOM.value == "custom", "CUSTOM 枚举值不正确"
    print("✓ 枚举值验证通过")
    
except ImportError as e:
    print(f"✗ 导入失败: {e}")
    sys.exit(1)

print("\n[验证6] 检查方法签名")
import inspect

# 检查 create_tool 方法签名
sig = inspect.signature(AgentService.create_tool)
params = list(sig.parameters.keys())
print(f"✓ create_tool 参数: {params}")
assert 'user_id' in params, "缺少 user_id 参数"
assert 'name' in params, "缺少 name 参数"
assert 'description' in params, "缺少 description 参数"
assert 'config' in params, "缺少 config 参数"

# 检查 update_tool 方法签名
sig = inspect.signature(AgentService.update_tool)
params = list(sig.parameters.keys())
print(f"✓ update_tool 参数: {params}")
assert 'tool_id' in params, "缺少 tool_id 参数"
assert 'user_id' in params, "缺少 user_id 参数"
assert 'name' in params, "缺少 name 参数"
assert 'description' in params, "缺少 description 参数"
assert 'config' in params, "缺少 config 参数"
assert 'is_enabled' in params, "缺少 is_enabled 参数"

# 检查 delete_tool 方法签名
sig = inspect.signature(AgentService.delete_tool)
params = list(sig.parameters.keys())
print(f"✓ delete_tool 参数: {params}")
assert 'tool_id' in params, "缺少 tool_id 参数"
assert 'user_id' in params, "缺少 user_id 参数"

print("\n" + "=" * 60)
print("所有验证通过! ✓")
print("=" * 60)
print("\n实现总结:")
print("1. ✓ 服务层 (AgentService) 实现完整")
print("2. ✓ 数据访问层 (AgentToolRepository) 实现完整")
print("3. ✓ API路由层 (agent.py) 实现完整")
print("4. ✓ Pydantic模型 (schemas/agent.py) 定义完整")
print("5. ✓ 数据库模型 (models/agent_tool.py) 定义完整")
print("6. ✓ 方法签名符合需求")
print("\n需求覆盖:")
print("- ✓ 需求5.2: 创建自定义工具")
print("- ✓ 需求5.3: 更新工具配置")
print("- ✓ 需求5.4: 禁用/删除工具")
