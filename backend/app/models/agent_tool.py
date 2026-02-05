"""
Agent工具模型

定义AgentTool数据库模型，用于存储Agent可用的工具配置信息。
"""

import enum
from datetime import datetime

from sqlalchemy import (JSON, Boolean, Column, DateTime, Enum, Integer, String,
                        Text)

from app.core.database import Base


class ToolType(str, enum.Enum):
    """
    工具类型枚举

    - builtin: 内置工具（系统预定义）
    - custom: 自定义工具（用户创建）
    """

    BUILTIN = "builtin"
    CUSTOM = "custom"


class AgentTool(Base):
    """
    Agent工具模型

    存储Agent可用的工具信息，包括内置工具和用户自定义工具。

    字段说明:
        id: 工具唯一标识
        name: 工具名称，唯一
        description: 工具描述，说明工具的功能和用途
        tool_type: 工具类型（builtin/custom）
        config: 工具配置参数（JSON格式）
        is_enabled: 工具是否启用
        created_at: 工具创建时间

    需求引用:
        - 需求5.2: 用户创建自定义工具且提供工具名称、描述和配置参数
    """

    __tablename__ = "agent_tools"

    # 主键
    id = Column(Integer, primary_key=True, index=True, comment="工具ID")

    # 基本信息
    name = Column(String(100), nullable=False, unique=True, index=True, comment="工具名称")
    description = Column(Text, nullable=False, comment="工具描述")

    # 工具类型
    tool_type = Column(
        Enum(ToolType, native_enum=False, values_callable=lambda x: [e.value for e in x]),
        default=ToolType.BUILTIN,
        nullable=False,
        comment="工具类型（builtin/custom）",
    )

    # 配置参数（JSON格式存储）
    config = Column(JSON, nullable=True, comment="工具配置参数")

    # 状态
    is_enabled = Column(Boolean, default=True, nullable=False, comment="是否启用")

    # 时间戳
    created_at = Column(
        DateTime, default=datetime.utcnow, nullable=False, comment="创建时间"
    )

    def __repr__(self) -> str:
        """字符串表示"""
        return f"<AgentTool(id={self.id}, name='{self.name}', type='{self.tool_type.value}')>"

    def __str__(self) -> str:
        """用户友好的字符串表示"""
        return f"AgentTool: {self.name}"
