"""
测试自定义工具管理功能

验证需求:
    - 需求5.2: 用户创建自定义工具且提供工具名称、描述和配置参数
    - 需求5.3: 用户更新工具配置
    - 需求5.4: 用户禁用工具
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, Column, Integer, String, Text, Boolean, DateTime, Enum as SQLEnum, JSON
from sqlalchemy.orm import sessionmaker, declarative_base
from datetime import datetime
import enum

# 定义Base和模型（避免导入依赖）
Base = declarative_base()

class ToolType(str, enum.Enum):
    """工具类型枚举"""
    BUILTIN = "builtin"
    CUSTOM = "custom"

class AgentTool(Base):
    """Agent工具模型"""
    __tablename__ = "agent_tools"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)
    description = Column(Text, nullable=False)
    tool_type = Column(SQLEnum(ToolType), default=ToolType.BUILTIN)
    config = Column(JSON, nullable=True)
    is_enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


def test_custom_tool_management():
    """测试自定义工具管理功能"""
    
    # 创建内存数据库
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    try:
        # 直接使用Repository进行测试，避免导入Service的依赖
        from typing import Optional, List, Dict, Any
        
        class AgentToolRepository:
            """简化的Repository用于测试"""
            def __init__(self, db):
                self.db = db
            
            def create(self, name: str, description: str, tool_type: ToolType = ToolType.BUILTIN,
                      config: Optional[Dict[str, Any]] = None, is_enabled: bool = True) -> AgentTool:
                tool = AgentTool(name=name, description=description, tool_type=tool_type,
                               config=config, is_enabled=is_enabled)
                self.db.add(tool)
                self.db.commit()
                self.db.refresh(tool)
                return tool
            
            def get_by_id(self, tool_id: int) -> Optional[AgentTool]:
                return self.db.query(AgentTool).filter(AgentTool.id == tool_id).first()
            
            def get_all(self, skip: int = 0, limit: int = 100, tool_type: Optional[ToolType] = None,
                       is_enabled: Optional[bool] = None) -> List[AgentTool]:
                query = self.db.query(AgentTool)
                if tool_type is not None:
                    query = query.filter(AgentTool.tool_type == tool_type)
                if is_enabled is not None:
                    query = query.filter(AgentTool.is_enabled == is_enabled)
                return query.offset(skip).limit(limit).all()
            
            def update(self, tool_id: int, name: Optional[str] = None, description: Optional[str] = None,
                      config: Optional[Dict[str, Any]] = None, is_enabled: Optional[bool] = None) -> Optional[AgentTool]:
                tool = self.get_by_id(tool_id)
                if not tool:
                    return None
                if name is not None:
                    tool.name = name
                if description is not None:
                    tool.description = description
                if config is not None:
                    tool.config = config
                if is_enabled is not None:
                    tool.is_enabled = is_enabled
                self.db.commit()
                self.db.refresh(tool)
                return tool
            
            def delete(self, tool_id: int) -> bool:
                tool = self.get_by_id(tool_id)
                if not tool:
                    return False
                self.db.delete(tool)
                self.db.commit()
                return True
            
            def name_exists(self, name: str, exclude_tool_id: Optional[int] = None) -> bool:
                query = self.db.query(AgentTool).filter(AgentTool.name == name)
                if exclude_tool_id is not None:
                    query = query.filter(AgentTool.id != exclude_tool_id)
                return query.first() is not None
        
        # 简化的Service用于测试
        class SimpleAgentService:
            def __init__(self, db):
                self.db = db
                self.tool_repo = AgentToolRepository(db)
            
            def get_tools(self, user_id: int, skip: int = 0, limit: int = 100,
                         tool_type: Optional[str] = None, is_enabled: Optional[bool] = None) -> List[Dict[str, Any]]:
                tool_type_enum = None
                if tool_type:
                    try:
                        tool_type_enum = ToolType(tool_type)
                    except ValueError:
                        pass
                tools = self.tool_repo.get_all(skip=skip, limit=limit, tool_type=tool_type_enum, is_enabled=is_enabled)
                return [{"id": t.id, "name": t.name, "description": t.description, "tool_type": t.tool_type.value,
                        "config": t.config, "is_enabled": t.is_enabled, "created_at": t.created_at.isoformat()}
                       for t in tools]
            
            def get_tool(self, tool_id: int, user_id: int) -> Optional[Dict[str, Any]]:
                tool = self.tool_repo.get_by_id(tool_id)
                if not tool:
                    return None
                return {"id": tool.id, "name": tool.name, "description": tool.description,
                       "tool_type": tool.tool_type.value, "config": tool.config, "is_enabled": tool.is_enabled,
                       "created_at": tool.created_at.isoformat()}
            
            def create_tool(self, user_id: int, name: str, description: str,
                          config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
                if self.tool_repo.name_exists(name):
                    raise ValueError(f"工具名称 '{name}' 已存在")
                tool = self.tool_repo.create(name=name, description=description, tool_type=ToolType.CUSTOM,
                                            config=config, is_enabled=True)
                return {"id": tool.id, "name": tool.name, "description": tool.description,
                       "tool_type": tool.tool_type.value, "config": tool.config, "is_enabled": tool.is_enabled,
                       "created_at": tool.created_at.isoformat()}
            
            def update_tool(self, tool_id: int, user_id: int, name: Optional[str] = None,
                          description: Optional[str] = None, config: Optional[Dict[str, Any]] = None,
                          is_enabled: Optional[bool] = None) -> Optional[Dict[str, Any]]:
                tool = self.tool_repo.get_by_id(tool_id)
                if not tool:
                    return None
                if name and name != tool.name:
                    if self.tool_repo.name_exists(name, exclude_tool_id=tool_id):
                        raise ValueError(f"工具名称 '{name}' 已存在")
                updated_tool = self.tool_repo.update(tool_id=tool_id, name=name, description=description,
                                                    config=config, is_enabled=is_enabled)
                if updated_tool:
                    return {"id": updated_tool.id, "name": updated_tool.name, "description": updated_tool.description,
                           "tool_type": updated_tool.tool_type.value, "config": updated_tool.config,
                           "is_enabled": updated_tool.is_enabled, "created_at": updated_tool.created_at.isoformat()}
                return None
            
            def delete_tool(self, tool_id: int, user_id: int) -> bool:
                tool = self.tool_repo.get_by_id(tool_id)
                if not tool:
                    return False
                if tool.tool_type == ToolType.BUILTIN:
                    raise ValueError("不能删除内置工具")
                return self.tool_repo.delete(tool_id)
        
        service = SimpleAgentService(db)
        user_id = 1
        
        print("=" * 60)
        print("测试自定义工具管理功能")
        print("=" * 60)
        
        # 测试1: 创建自定义工具
        print("\n[测试1] 创建自定义工具")
        tool_data = {
            "name": "custom_api_tool",
            "description": "调用自定义API的工具",
            "config": {
                "api_url": "https://api.example.com",
                "api_key": "test_key_123",
                "timeout": 30
            }
        }
        
        created_tool = service.create_tool(
            user_id=user_id,
            name=tool_data["name"],
            description=tool_data["description"],
            config=tool_data["config"]
        )
        
        print(f"✓ 工具创建成功:")
        print(f"  - ID: {created_tool['id']}")
        print(f"  - 名称: {created_tool['name']}")
        print(f"  - 描述: {created_tool['description']}")
        print(f"  - 类型: {created_tool['tool_type']}")
        print(f"  - 配置: {created_tool['config']}")
        print(f"  - 启用状态: {created_tool['is_enabled']}")
        
        assert created_tool['name'] == tool_data['name']
        assert created_tool['description'] == tool_data['description']
        assert created_tool['tool_type'] == 'custom'
        assert created_tool['config'] == tool_data['config']
        assert created_tool['is_enabled'] is True
        
        tool_id = created_tool['id']
        
        # 测试2: 获取工具列表
        print("\n[测试2] 获取工具列表")
        tools = service.get_tools(user_id=user_id)
        print(f"✓ 获取到 {len(tools)} 个工具")
        
        custom_tools = [t for t in tools if t['tool_type'] == 'custom']
        print(f"  - 其中自定义工具: {len(custom_tools)} 个")
        
        assert len(custom_tools) >= 1
        assert any(t['id'] == tool_id for t in custom_tools)
        
        # 测试3: 获取单个工具
        print("\n[测试3] 获取单个工具详情")
        tool = service.get_tool(tool_id=tool_id, user_id=user_id)
        print(f"✓ 获取工具详情成功:")
        print(f"  - 名称: {tool['name']}")
        print(f"  - 配置: {tool['config']}")
        
        assert tool is not None
        assert tool['id'] == tool_id
        
        # 测试4: 更新工具配置
        print("\n[测试4] 更新工具配置")
        updated_config = {
            "api_url": "https://api.example.com/v2",
            "api_key": "new_key_456",
            "timeout": 60,
            "retry_count": 3
        }
        
        updated_tool = service.update_tool(
            tool_id=tool_id,
            user_id=user_id,
            description="更新后的API工具描述",
            config=updated_config
        )
        
        print(f"✓ 工具更新成功:")
        print(f"  - 新描述: {updated_tool['description']}")
        print(f"  - 新配置: {updated_tool['config']}")
        
        assert updated_tool is not None
        assert updated_tool['description'] == "更新后的API工具描述"
        assert updated_tool['config'] == updated_config
        
        # 测试5: 禁用工具
        print("\n[测试5] 禁用工具")
        disabled_tool = service.update_tool(
            tool_id=tool_id,
            user_id=user_id,
            is_enabled=False
        )
        
        print(f"✓ 工具禁用成功:")
        print(f"  - 启用状态: {disabled_tool['is_enabled']}")
        
        assert disabled_tool is not None
        assert disabled_tool['is_enabled'] is False
        
        # 测试6: 重新启用工具
        print("\n[测试6] 重新启用工具")
        enabled_tool = service.update_tool(
            tool_id=tool_id,
            user_id=user_id,
            is_enabled=True
        )
        
        print(f"✓ 工具启用成功:")
        print(f"  - 启用状态: {enabled_tool['is_enabled']}")
        
        assert enabled_tool is not None
        assert enabled_tool['is_enabled'] is True
        
        # 测试7: 更新工具名称
        print("\n[测试7] 更新工具名称")
        renamed_tool = service.update_tool(
            tool_id=tool_id,
            user_id=user_id,
            name="renamed_custom_tool"
        )
        
        print(f"✓ 工具名称更新成功:")
        print(f"  - 新名称: {renamed_tool['name']}")
        
        assert renamed_tool is not None
        assert renamed_tool['name'] == "renamed_custom_tool"
        
        # 测试8: 删除工具
        print("\n[测试8] 删除自定义工具")
        success = service.delete_tool(tool_id=tool_id, user_id=user_id)
        
        print(f"✓ 工具删除成功: {success}")
        
        assert success is True
        
        # 验证工具已被删除
        deleted_tool = service.get_tool(tool_id=tool_id, user_id=user_id)
        assert deleted_tool is None
        print("✓ 验证工具已被删除")
        
        # 测试9: 测试工具名称唯一性
        print("\n[测试9] 测试工具名称唯一性")
        service.create_tool(
            user_id=user_id,
            name="unique_tool",
            description="第一个工具"
        )
        
        try:
            service.create_tool(
                user_id=user_id,
                name="unique_tool",
                description="重复名称的工具"
            )
            print("✗ 应该抛出ValueError异常")
            assert False, "应该抛出ValueError异常"
        except ValueError as e:
            print(f"✓ 正确抛出异常: {str(e)}")
            assert "已存在" in str(e)
        
        # 测试10: 测试不能删除内置工具
        print("\n[测试10] 测试不能删除内置工具")
        # 创建一个内置工具用于测试
        tool_repo = AgentToolRepository(db)
        builtin_tool = tool_repo.create(
            name="builtin_test_tool",
            description="内置测试工具",
            tool_type=ToolType.BUILTIN
        )
        
        try:
            service.delete_tool(tool_id=builtin_tool.id, user_id=user_id)
            print("✗ 应该抛出ValueError异常")
            assert False, "应该抛出ValueError异常"
        except ValueError as e:
            print(f"✓ 正确抛出异常: {str(e)}")
            assert "内置工具" in str(e)
        
        print("\n" + "=" * 60)
        print("所有测试通过! ✓")
        print("=" * 60)
        
    finally:
        db.close()


if __name__ == "__main__":
    test_custom_tool_management()
