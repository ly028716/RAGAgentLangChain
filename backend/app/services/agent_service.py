"""
Agent服务层

提供Agent工具管理和任务执行的业务逻辑。
协调AgentManager和Repository，实现完整的Agent功能。

需求引用:
    - 需求5.2: 用户创建自定义工具且提供工具名称、描述和配置参数
    - 需求6.1: 用户提交Agent任务，Agent服务使用ReAct模式分析任务并生成执行计划
    - 需求6.5: Agent任务执行完成，更新执行记录状态为"已完成"并记录最终结果和完成时间
    - 需求6.6: Agent任务执行失败，更新执行记录状态为"失败"并记录错误信息
"""

from typing import List, Dict, Any, Optional, AsyncGenerator
from datetime import datetime
import logging

from sqlalchemy.orm import Session

from app.repositories.agent_repository import AgentToolRepository, AgentExecutionRepository
from app.models.agent_tool import AgentTool, ToolType
from app.models.agent_execution import AgentExecution, ExecutionStatus
from app.langchain_integration.agent_executor import AgentManager
from app.websocket.connection_manager import connection_manager


logger = logging.getLogger(__name__)


class AgentService:
    """
    Agent服务类
    
    提供Agent工具管理和任务执行的业务逻辑。
    
    使用方式:
        service = AgentService(db)
        tools = service.get_tools(user_id=1)
        execution = await service.execute_task(user_id=1, task="计算 2+2")
    """
    
    def __init__(self, db: Session):
        """
        初始化Agent服务
        
        Args:
            db: 数据库会话
        """
        self.db = db
        self.tool_repo = AgentToolRepository(db)
        self.execution_repo = AgentExecutionRepository(db)
        self.agent_manager = AgentManager()
    
    # ==================== 工具管理 ====================
    
    def get_tools(
        self,
        user_id: int,
        skip: int = 0,
        limit: int = 100,
        tool_type: Optional[str] = None,
        is_enabled: Optional[bool] = None
    ) -> List[Dict[str, Any]]:
        """
        获取可用工具列表
        
        Args:
            user_id: 用户ID（用于权限验证）
            skip: 跳过的记录数
            limit: 返回的最大记录数
            tool_type: 工具类型过滤（builtin/custom）
            is_enabled: 启用状态过滤
            
        Returns:
            工具信息列表
        """
        # 转换tool_type字符串为枚举
        tool_type_enum = None
        if tool_type:
            try:
                tool_type_enum = ToolType(tool_type)
            except ValueError:
                logger.warning(f"无效的工具类型: {tool_type}")
        
        # 从数据库获取工具
        tools = self.tool_repo.get_all(
            skip=skip,
            limit=limit,
            tool_type=tool_type_enum,
            is_enabled=is_enabled
        )
        
        # 转换为字典格式
        tools_list = []
        for tool in tools:
            tools_list.append({
                "id": tool.id,
                "name": tool.name,
                "description": tool.description,
                "tool_type": tool.tool_type.value,
                "config": tool.config,
                "is_enabled": tool.is_enabled,
                "created_at": tool.created_at.isoformat()
            })
        
        return tools_list
    
    def get_tool(self, tool_id: int, user_id: int) -> Optional[Dict[str, Any]]:
        """
        获取单个工具信息
        
        Args:
            tool_id: 工具ID
            user_id: 用户ID（用于权限验证）
            
        Returns:
            工具信息字典，不存在则返回None
        """
        tool = self.tool_repo.get_by_id(tool_id)
        if not tool:
            return None
        
        return {
            "id": tool.id,
            "name": tool.name,
            "description": tool.description,
            "tool_type": tool.tool_type.value,
            "config": tool.config,
            "is_enabled": tool.is_enabled,
            "created_at": tool.created_at.isoformat()
        }
    
    def create_tool(
        self,
        user_id: int,
        name: str,
        description: str,
        config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        创建自定义工具
        
        Args:
            user_id: 用户ID
            name: 工具名称
            description: 工具描述
            config: 工具配置参数
            
        Returns:
            创建的工具信息字典
            
        Raises:
            ValueError: 工具名称已存在时抛出
        """
        # 检查工具名称是否已存在
        if self.tool_repo.name_exists(name):
            raise ValueError(f"工具名称 '{name}' 已存在")
        
        # 创建工具
        tool = self.tool_repo.create(
            name=name,
            description=description,
            tool_type=ToolType.CUSTOM,
            config=config,
            is_enabled=True
        )
        
        logger.info(f"用户 {user_id} 创建了自定义工具: {name}")
        
        return {
            "id": tool.id,
            "name": tool.name,
            "description": tool.description,
            "tool_type": tool.tool_type.value,
            "config": tool.config,
            "is_enabled": tool.is_enabled,
            "created_at": tool.created_at.isoformat()
        }
    
    def update_tool(
        self,
        tool_id: int,
        user_id: int,
        name: Optional[str] = None,
        description: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
        is_enabled: Optional[bool] = None
    ) -> Optional[Dict[str, Any]]:
        """
        更新工具配置
        
        Args:
            tool_id: 工具ID
            user_id: 用户ID
            name: 新工具名称
            description: 新描述
            config: 新配置参数
            is_enabled: 是否启用
            
        Returns:
            更新后的工具信息字典，工具不存在则返回None
            
        Raises:
            ValueError: 工具名称已被其他工具使用时抛出
        """
        # 检查工具是否存在
        tool = self.tool_repo.get_by_id(tool_id)
        if not tool:
            return None
        
        # 如果更新名称，检查新名称是否已存在
        if name and name != tool.name:
            if self.tool_repo.name_exists(name, exclude_tool_id=tool_id):
                raise ValueError(f"工具名称 '{name}' 已存在")
        
        # 更新工具
        updated_tool = self.tool_repo.update(
            tool_id=tool_id,
            name=name,
            description=description,
            config=config,
            is_enabled=is_enabled
        )
        
        if updated_tool:
            logger.info(f"用户 {user_id} 更新了工具 {tool_id}")
            return {
                "id": updated_tool.id,
                "name": updated_tool.name,
                "description": updated_tool.description,
                "tool_type": updated_tool.tool_type.value,
                "config": updated_tool.config,
                "is_enabled": updated_tool.is_enabled,
                "created_at": updated_tool.created_at.isoformat()
            }
        
        return None
    
    def delete_tool(self, tool_id: int, user_id: int) -> bool:
        """
        删除工具
        
        Args:
            tool_id: 工具ID
            user_id: 用户ID
            
        Returns:
            删除成功返回True，工具不存在返回False
        """
        # 检查工具是否存在
        tool = self.tool_repo.get_by_id(tool_id)
        if not tool:
            return False
        
        # 只允许删除自定义工具
        if tool.tool_type == ToolType.BUILTIN:
            raise ValueError("不能删除内置工具")
        
        # 删除工具
        success = self.tool_repo.delete(tool_id)
        
        if success:
            logger.info(f"用户 {user_id} 删除了工具 {tool_id}")
        
        return success
    
    # ==================== 任务执行 ====================
    
    async def execute_task(
        self,
        user_id: int,
        task: str,
        tool_ids: Optional[List[int]] = None,
        max_iterations: int = 10
    ) -> Dict[str, Any]:
        """
        执行Agent任务
        
        Args:
            user_id: 用户ID
            task: 任务描述
            tool_ids: 要使用的工具ID列表（可选，默认使用所有启用的工具）
            max_iterations: 最大迭代次数
            
        Returns:
            执行结果字典，包含:
                - execution_id: 执行记录ID
                - task: 任务描述
                - result: 执行结果
                - steps: 执行步骤列表
                - status: 执行状态
                - created_at: 创建时间
                - completed_at: 完成时间
        """
        try:
            logger.info(f"用户 {user_id} 开始执行Agent任务: {task}")
            
            # 创建执行记录
            execution = self.execution_repo.create(
                user_id=user_id,
                task=task,
                status=ExecutionStatus.PENDING
            )
            
            # 通过WebSocket通知任务创建
            try:
                await connection_manager.send_personal_message(user_id, {
                    "type": "agent_task_created",
                    "data": {
                        "execution_id": execution.id,
                        "task": task,
                        "status": ExecutionStatus.PENDING.value,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                })
            except Exception as e:
                logger.warning(f"WebSocket通知失败: {str(e)}")
            
            # 设置状态为执行中
            self.execution_repo.set_running(execution.id)
            
            # 通过WebSocket通知任务开始执行
            try:
                await connection_manager.send_personal_message(user_id, {
                    "type": "agent_task_started",
                    "data": {
                        "execution_id": execution.id,
                        "status": ExecutionStatus.RUNNING.value,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                })
            except Exception as e:
                logger.warning(f"WebSocket通知失败: {str(e)}")
            
            # 执行任务
            result = await self.agent_manager.execute_task(
                task=task,
                tool_ids=tool_ids,
                max_iterations=max_iterations
            )
            
            # 更新执行记录
            if result["status"] == "completed":
                self.execution_repo.set_completed(
                    execution.id,
                    result=result["result"]
                )
                # 更新步骤
                self.execution_repo.update(
                    execution.id,
                    steps=result["steps"]
                )
                
                # 通过WebSocket通知任务完成
                try:
                    await connection_manager.send_personal_message(user_id, {
                        "type": "agent_task_completed",
                        "data": {
                            "execution_id": execution.id,
                            "result": result["result"],
                            "status": ExecutionStatus.COMPLETED.value,
                            "step_count": len(result["steps"]),
                            "timestamp": datetime.utcnow().isoformat()
                        }
                    })
                except Exception as e:
                    logger.warning(f"WebSocket通知失败: {str(e)}")
            else:
                self.execution_repo.set_failed(
                    execution.id,
                    error_message=result.get("error", "未知错误")
                )
                # 更新步骤（即使失败也记录已执行的步骤）
                self.execution_repo.update(
                    execution.id,
                    steps=result["steps"]
                )
                
                # 通过WebSocket通知任务失败
                try:
                    await connection_manager.send_personal_message(user_id, {
                        "type": "agent_task_failed",
                        "data": {
                            "execution_id": execution.id,
                            "error": result.get("error", "未知错误"),
                            "status": ExecutionStatus.FAILED.value,
                            "timestamp": datetime.utcnow().isoformat()
                        }
                    })
                except Exception as e:
                    logger.warning(f"WebSocket通知失败: {str(e)}")
            
            # 获取更新后的执行记录
            updated_execution = self.execution_repo.get_by_id(execution.id)
            
            logger.info(f"Agent任务执行完成: execution_id={execution.id}, status={result['status']}")
            
            return {
                "execution_id": updated_execution.id,
                "task": updated_execution.task,
                "result": updated_execution.result,
                "steps": updated_execution.steps or [],
                "status": updated_execution.status.value,
                "error_message": updated_execution.error_message,
                "created_at": updated_execution.created_at.isoformat(),
                "completed_at": updated_execution.completed_at.isoformat() if updated_execution.completed_at else None
            }
            
        except Exception as e:
            logger.error(f"Agent任务执行失败: {str(e)}", exc_info=True)
            
            # 如果执行记录已创建，更新为失败状态
            if 'execution' in locals():
                self.execution_repo.set_failed(
                    execution.id,
                    error_message=str(e)
                )
            
            raise
    
    async def stream_execute_task(
        self,
        user_id: int,
        task: str,
        tool_ids: Optional[List[int]] = None,
        max_iterations: int = 10
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        流式执行Agent任务
        
        Args:
            user_id: 用户ID
            task: 任务描述
            tool_ids: 要使用的工具ID列表
            max_iterations: 最大迭代次数
            
        Yields:
            执行过程中的事件字典
        """
        try:
            logger.info(f"用户 {user_id} 开始流式执行Agent任务: {task}")
            
            # 创建执行记录
            execution = self.execution_repo.create(
                user_id=user_id,
                task=task,
                status=ExecutionStatus.PENDING
            )
            
            # 发送执行记录创建事件
            yield {
                "type": "created",
                "data": {
                    "execution_id": execution.id,
                    "task": task,
                    "status": ExecutionStatus.PENDING.value
                }
            }
            
            # 设置状态为执行中
            self.execution_repo.set_running(execution.id)
            
            yield {
                "type": "status",
                "data": {
                    "execution_id": execution.id,
                    "status": ExecutionStatus.RUNNING.value
                }
            }
            
            # 流式执行任务
            async for event in self.agent_manager.stream_execute_task(
                task=task,
                tool_ids=tool_ids,
                max_iterations=max_iterations
            ):
                # 如果是步骤事件，更新数据库
                if event["type"] == "step":
                    self.execution_repo.add_step(execution.id, event["data"])
                    
                    # 通过WebSocket通知步骤更新
                    try:
                        await connection_manager.send_personal_message(user_id, {
                            "type": "agent_step",
                            "data": {
                                "execution_id": execution.id,
                                "step": event["data"],
                                "timestamp": datetime.utcnow().isoformat()
                            }
                        })
                    except Exception as e:
                        logger.warning(f"WebSocket步骤通知失败: {str(e)}")
                
                # 转发事件给客户端
                yield event
            
            # 获取最终执行记录
            final_execution = self.execution_repo.get_by_id(execution.id)
            
            logger.info(f"Agent流式任务执行完成: execution_id={execution.id}")
            
        except Exception as e:
            logger.error(f"Agent流式任务执行失败: {str(e)}", exc_info=True)
            
            # 如果执行记录已创建，更新为失败状态
            if 'execution' in locals():
                self.execution_repo.set_failed(
                    execution.id,
                    error_message=str(e)
                )
            
            yield {
                "type": "error",
                "data": {
                    "execution_id": execution.id if 'execution' in locals() else None,
                    "message": str(e)
                }
            }
    
    def get_execution(
        self,
        execution_id: int,
        user_id: int
    ) -> Optional[Dict[str, Any]]:
        """
        获取执行记录
        
        Args:
            execution_id: 执行记录ID
            user_id: 用户ID（用于权限验证）
            
        Returns:
            执行记录字典，不存在或无权限则返回None
        """
        execution = self.execution_repo.get_by_id_and_user(execution_id, user_id)
        if not execution:
            return None
        
        return {
            "execution_id": execution.id,
            "task": execution.task,
            "result": execution.result,
            "steps": execution.steps or [],
            "status": execution.status.value,
            "error_message": execution.error_message,
            "created_at": execution.created_at.isoformat(),
            "completed_at": execution.completed_at.isoformat() if execution.completed_at else None
        }
    
    def get_user_executions(
        self,
        user_id: int,
        skip: int = 0,
        limit: int = 20,
        status: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        获取用户的执行历史
        
        Args:
            user_id: 用户ID
            skip: 跳过的记录数
            limit: 返回的最大记录数
            status: 状态过滤（pending/running/completed/failed）
            
        Returns:
            包含执行记录列表和总数的字典
        """
        # 转换status字符串为枚举
        status_enum = None
        if status:
            try:
                status_enum = ExecutionStatus(status)
            except ValueError:
                logger.warning(f"无效的执行状态: {status}")
        
        # 获取执行记录
        executions, total = self.execution_repo.get_user_executions(
            user_id=user_id,
            skip=skip,
            limit=limit,
            status=status_enum
        )
        
        # 转换为字典格式
        executions_list = []
        for execution in executions:
            executions_list.append({
                "execution_id": execution.id,
                "task": execution.task,
                "result": execution.result,
                "status": execution.status.value,
                "error_message": execution.error_message,
                "step_count": len(execution.steps) if execution.steps else 0,
                "created_at": execution.created_at.isoformat(),
                "completed_at": execution.completed_at.isoformat() if execution.completed_at else None
            })
        
        return {
            "total": total,
            "items": executions_list
        }


# 导出
__all__ = ['AgentService']
