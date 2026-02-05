"""
Agent数据访问层（Repository）

封装Agent工具和执行记录相关的数据库操作，提供统一的数据访问接口。
实现工具和执行记录的CRUD操作。

需求引用:
    - 需求5.2: 用户创建自定义工具且提供工具名称、描述和配置参数
    - 需求6.2: Agent执行计划生成完成后创建执行记录并设置状态为"执行中"
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.models.agent_execution import AgentExecution, ExecutionStatus
from app.models.agent_tool import AgentTool, ToolType


class AgentToolRepository:
    """
    Agent工具Repository类

    提供Agent工具数据的CRUD操作和查询功能。

    使用方式:
        repo = AgentToolRepository(db)
        tool = repo.create(name="calculator", description="数学计算工具")
        tool = repo.get_by_id(1)
    """

    def __init__(self, db: Session):
        """
        初始化Repository

        Args:
            db: SQLAlchemy数据库会话
        """
        self.db = db

    def create(
        self,
        name: str,
        description: str,
        tool_type: ToolType = ToolType.BUILTIN,
        config: Optional[Dict[str, Any]] = None,
        is_enabled: bool = True,
    ) -> AgentTool:
        """
        创建新工具

        Args:
            name: 工具名称（必须唯一）
            description: 工具描述
            tool_type: 工具类型（builtin/custom）
            config: 工具配置参数（可选）
            is_enabled: 是否启用（默认True）

        Returns:
            AgentTool: 创建的工具对象

        Raises:
            IntegrityError: 工具名称已存在时抛出
        """
        tool = AgentTool(
            name=name,
            description=description,
            tool_type=tool_type,
            config=config,
            is_enabled=is_enabled,
        )
        self.db.add(tool)
        self.db.commit()
        self.db.refresh(tool)
        return tool

    def get_by_id(self, tool_id: int) -> Optional[AgentTool]:
        """
        根据ID获取工具

        Args:
            tool_id: 工具ID

        Returns:
            Optional[AgentTool]: 工具对象，不存在则返回None
        """
        return self.db.query(AgentTool).filter(AgentTool.id == tool_id).first()

    def get_by_name(self, name: str) -> Optional[AgentTool]:
        """
        根据名称获取工具

        Args:
            name: 工具名称

        Returns:
            Optional[AgentTool]: 工具对象，不存在则返回None
        """
        return self.db.query(AgentTool).filter(AgentTool.name == name).first()

    def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        tool_type: Optional[ToolType] = None,
        is_enabled: Optional[bool] = None,
    ) -> List[AgentTool]:
        """
        获取所有工具（分页，支持过滤）

        Args:
            skip: 跳过的记录数
            limit: 返回的最大记录数
            tool_type: 工具类型过滤（可选）
            is_enabled: 启用状态过滤（可选）

        Returns:
            List[AgentTool]: 工具列表
        """
        query = self.db.query(AgentTool)

        if tool_type is not None:
            query = query.filter(AgentTool.tool_type == tool_type)
        if is_enabled is not None:
            query = query.filter(AgentTool.is_enabled == is_enabled)

        return query.order_by(AgentTool.id.asc()).offset(skip).limit(limit).all()

    def get_enabled_tools(self) -> List[AgentTool]:
        """
        获取所有启用的工具

        Returns:
            List[AgentTool]: 启用的工具列表
        """
        return self.db.query(AgentTool).filter(AgentTool.is_enabled == True).all()

    def update(
        self,
        tool_id: int,
        name: Optional[str] = None,
        description: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
        is_enabled: Optional[bool] = None,
    ) -> Optional[AgentTool]:
        """
        更新工具信息

        Args:
            tool_id: 工具ID
            name: 新工具名称（可选）
            description: 新描述（可选）
            config: 新配置参数（可选）
            is_enabled: 是否启用（可选）

        Returns:
            Optional[AgentTool]: 更新后的工具对象，工具不存在则返回None

        Raises:
            IntegrityError: 工具名称已被其他工具使用时抛出
        """
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
        """
        删除工具

        Args:
            tool_id: 工具ID

        Returns:
            bool: 删除成功返回True，工具不存在返回False
        """
        tool = self.get_by_id(tool_id)
        if not tool:
            return False

        self.db.delete(tool)
        self.db.commit()
        return True

    def enable(self, tool_id: int) -> Optional[AgentTool]:
        """
        启用工具

        Args:
            tool_id: 工具ID

        Returns:
            Optional[AgentTool]: 更新后的工具对象，工具不存在则返回None
        """
        return self.update(tool_id, is_enabled=True)

    def disable(self, tool_id: int) -> Optional[AgentTool]:
        """
        禁用工具

        Args:
            tool_id: 工具ID

        Returns:
            Optional[AgentTool]: 更新后的工具对象，工具不存在则返回None
        """
        return self.update(tool_id, is_enabled=False)

    def name_exists(self, name: str, exclude_tool_id: Optional[int] = None) -> bool:
        """
        检查工具名称是否已存在

        Args:
            name: 要检查的工具名称
            exclude_tool_id: 排除的工具ID（用于更新时排除自己）

        Returns:
            bool: 工具名称已存在返回True，否则返回False
        """
        query = self.db.query(AgentTool).filter(AgentTool.name == name)
        if exclude_tool_id is not None:
            query = query.filter(AgentTool.id != exclude_tool_id)
        return query.first() is not None

    def count(
        self, tool_type: Optional[ToolType] = None, is_enabled: Optional[bool] = None
    ) -> int:
        """
        获取工具总数

        Args:
            tool_type: 工具类型过滤（可选）
            is_enabled: 启用状态过滤（可选）

        Returns:
            int: 工具总数
        """
        query = self.db.query(AgentTool)
        if tool_type is not None:
            query = query.filter(AgentTool.tool_type == tool_type)
        if is_enabled is not None:
            query = query.filter(AgentTool.is_enabled == is_enabled)
        return query.count()


class AgentExecutionRepository:
    """
    Agent执行记录Repository类

    提供Agent执行记录数据的CRUD操作和查询功能。

    使用方式:
        repo = AgentExecutionRepository(db)
        execution = repo.create(user_id=1, task="搜索Python教程")
        execution = repo.get_by_id(1)
    """

    def __init__(self, db: Session):
        """
        初始化Repository

        Args:
            db: SQLAlchemy数据库会话
        """
        self.db = db

    def create(
        self,
        user_id: int,
        task: str,
        status: ExecutionStatus = ExecutionStatus.PENDING,
        steps: Optional[List[Dict[str, Any]]] = None,
    ) -> AgentExecution:
        """
        创建新执行记录

        Args:
            user_id: 用户ID
            task: 任务描述
            status: 执行状态（默认pending）
            steps: 执行步骤（可选）

        Returns:
            AgentExecution: 创建的执行记录对象
        """
        execution = AgentExecution(
            user_id=user_id, task=task, status=status, steps=steps
        )
        self.db.add(execution)
        self.db.commit()
        self.db.refresh(execution)
        return execution

    def get_by_id(self, execution_id: int) -> Optional[AgentExecution]:
        """
        根据ID获取执行记录

        Args:
            execution_id: 执行记录ID

        Returns:
            Optional[AgentExecution]: 执行记录对象，不存在则返回None
        """
        return (
            self.db.query(AgentExecution)
            .filter(AgentExecution.id == execution_id)
            .first()
        )

    def get_by_id_and_user(
        self, execution_id: int, user_id: int
    ) -> Optional[AgentExecution]:
        """
        根据ID和用户ID获取执行记录（用于权限验证）

        Args:
            execution_id: 执行记录ID
            user_id: 用户ID

        Returns:
            Optional[AgentExecution]: 执行记录对象，不存在或不属于该用户则返回None
        """
        return (
            self.db.query(AgentExecution)
            .filter(
                AgentExecution.id == execution_id, AgentExecution.user_id == user_id
            )
            .first()
        )

    def get_user_executions(
        self,
        user_id: int,
        skip: int = 0,
        limit: int = 20,
        status: Optional[ExecutionStatus] = None,
    ) -> Tuple[List[AgentExecution], int]:
        """
        获取用户的执行记录（分页）

        Args:
            user_id: 用户ID
            skip: 跳过的记录数
            limit: 返回的最大记录数
            status: 状态过滤（可选）

        Returns:
            Tuple[List[AgentExecution], int]: (执行记录列表, 总数)
        """
        query = self.db.query(AgentExecution).filter(AgentExecution.user_id == user_id)

        if status is not None:
            query = query.filter(AgentExecution.status == status)

        total = query.count()
        executions = (
            query.order_by(desc(AgentExecution.created_at))
            .offset(skip)
            .limit(limit)
            .all()
        )

        return executions, total

    def update(
        self,
        execution_id: int,
        status: Optional[ExecutionStatus] = None,
        steps: Optional[List[Dict[str, Any]]] = None,
        result: Optional[str] = None,
        error_message: Optional[str] = None,
        completed_at: Optional[datetime] = None,
    ) -> Optional[AgentExecution]:
        """
        更新执行记录

        Args:
            execution_id: 执行记录ID
            status: 新状态（可选）
            steps: 新执行步骤（可选）
            result: 执行结果（可选）
            error_message: 错误信息（可选）
            completed_at: 完成时间（可选）

        Returns:
            Optional[AgentExecution]: 更新后的执行记录对象，不存在则返回None
        """
        execution = self.get_by_id(execution_id)
        if not execution:
            return None

        if status is not None:
            execution.status = status
        if steps is not None:
            execution.steps = steps
        if result is not None:
            execution.result = result
        if error_message is not None:
            execution.error_message = error_message
        if completed_at is not None:
            execution.completed_at = completed_at

        self.db.commit()
        self.db.refresh(execution)
        return execution

    def add_step(
        self, execution_id: int, step: Dict[str, Any]
    ) -> Optional[AgentExecution]:
        """
        添加执行步骤

        Args:
            execution_id: 执行记录ID
            step: 步骤信息字典，包含step_number, thought, action, action_input, observation

        Returns:
            Optional[AgentExecution]: 更新后的执行记录对象，不存在则返回None
        """
        execution = self.get_by_id(execution_id)
        if not execution:
            return None

        current_steps = execution.steps or []
        step_number = step.get("step_number")
        if step_number is not None and any(
            existing.get("step_number") == step_number for existing in current_steps
        ):
            return execution
        current_steps.append(step)
        execution.steps = current_steps

        self.db.commit()
        self.db.refresh(execution)
        return execution

    def set_running(self, execution_id: int) -> Optional[AgentExecution]:
        """
        设置执行记录状态为执行中

        Args:
            execution_id: 执行记录ID

        Returns:
            Optional[AgentExecution]: 更新后的执行记录对象，不存在则返回None
        """
        return self.update(execution_id, status=ExecutionStatus.RUNNING)

    def set_completed(self, execution_id: int, result: str) -> Optional[AgentExecution]:
        """
        设置执行记录状态为已完成

        Args:
            execution_id: 执行记录ID
            result: 执行结果

        Returns:
            Optional[AgentExecution]: 更新后的执行记录对象，不存在则返回None
        """
        return self.update(
            execution_id,
            status=ExecutionStatus.COMPLETED,
            result=result,
            completed_at=datetime.utcnow(),
        )

    def set_failed(
        self, execution_id: int, error_message: str
    ) -> Optional[AgentExecution]:
        """
        设置执行记录状态为失败

        Args:
            execution_id: 执行记录ID
            error_message: 错误信息

        Returns:
            Optional[AgentExecution]: 更新后的执行记录对象，不存在则返回None
        """
        return self.update(
            execution_id,
            status=ExecutionStatus.FAILED,
            error_message=error_message,
            completed_at=datetime.utcnow(),
        )

    def delete(self, execution_id: int) -> bool:
        """
        删除执行记录

        Args:
            execution_id: 执行记录ID

        Returns:
            bool: 删除成功返回True，执行记录不存在返回False
        """
        execution = self.get_by_id(execution_id)
        if not execution:
            return False

        self.db.delete(execution)
        self.db.commit()
        return True

    def count_by_user(
        self, user_id: int, status: Optional[ExecutionStatus] = None
    ) -> int:
        """
        获取用户的执行记录总数

        Args:
            user_id: 用户ID
            status: 状态过滤（可选）

        Returns:
            int: 执行记录总数
        """
        query = self.db.query(AgentExecution).filter(AgentExecution.user_id == user_id)
        if status is not None:
            query = query.filter(AgentExecution.status == status)
        return query.count()


# 导出
__all__ = ["AgentToolRepository", "AgentExecutionRepository"]
