"""
系统提示词服务

提供系统提示词的CRUD操作和管理功能。
"""

import logging
from typing import List, Optional, Tuple

from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from app.models.system_prompt import SystemPrompt
from app.schemas.system_prompt import SystemPromptCreate, SystemPromptUpdate

logger = logging.getLogger(__name__)


class SystemPromptService:
    """系统提示词服务"""

    def __init__(self, db: Session):
        self.db = db

    def get_prompts(
        self,
        user_id: int,
        category: Optional[str] = None,
        skip: int = 0,
        limit: int = 20,
    ) -> Tuple[List[SystemPrompt], int]:
        """
        获取提示词列表（包含系统提示词和用户自定义提示词）

        Args:
            user_id: 用户ID
            category: 分类筛选
            skip: 跳过数量
            limit: 返回数量

        Returns:
            (提示词列表, 总数)
        """
        # 查询条件：系统提示词 OR 用户自己的提示词
        query = self.db.query(SystemPrompt).filter(
            or_(SystemPrompt.is_system == True, SystemPrompt.user_id == user_id)
        )

        if category:
            query = query.filter(SystemPrompt.category == category)

        total = query.count()

        prompts = (
            query.order_by(
                SystemPrompt.is_system.desc(),  # 系统提示词优先
                SystemPrompt.is_default.desc(),  # 默认提示词优先
                SystemPrompt.created_at.desc(),
            )
            .offset(skip)
            .limit(limit)
            .all()
        )

        return prompts, total

    def get_prompt_by_id(self, prompt_id: int, user_id: int) -> Optional[SystemPrompt]:
        """
        获取提示词详情

        Args:
            prompt_id: 提示词ID
            user_id: 用户ID

        Returns:
            提示词对象或None
        """
        return (
            self.db.query(SystemPrompt)
            .filter(
                SystemPrompt.id == prompt_id,
                or_(SystemPrompt.is_system == True, SystemPrompt.user_id == user_id),
            )
            .first()
        )

    def create_prompt(self, user_id: int, data: SystemPromptCreate) -> SystemPrompt:
        """
        创建用户自定义提示词

        Args:
            user_id: 用户ID
            data: 创建数据

        Returns:
            创建的提示词对象
        """
        prompt = SystemPrompt(
            user_id=user_id,
            name=data.name,
            content=data.content,
            category=data.category or "general",
            is_system=False,
            is_default=False,
        )

        self.db.add(prompt)
        self.db.commit()
        self.db.refresh(prompt)

        logger.info(f"创建提示词成功: user_id={user_id}, prompt_id={prompt.id}")
        return prompt

    def update_prompt(
        self, prompt_id: int, user_id: int, data: SystemPromptUpdate
    ) -> Optional[SystemPrompt]:
        """
        更新提示词

        Args:
            prompt_id: 提示词ID
            user_id: 用户ID
            data: 更新数据

        Returns:
            更新后的提示词对象或None
        """
        prompt = (
            self.db.query(SystemPrompt)
            .filter(
                SystemPrompt.id == prompt_id,
                SystemPrompt.user_id == user_id,  # 只能更新自己的提示词
                SystemPrompt.is_system == False,  # 不能更新系统提示词
            )
            .first()
        )

        if not prompt:
            return None

        # 更新字段
        if data.name is not None:
            prompt.name = data.name
        if data.content is not None:
            prompt.content = data.content
        if data.category is not None:
            prompt.category = data.category

        self.db.commit()
        self.db.refresh(prompt)

        logger.info(f"更新提示词成功: prompt_id={prompt_id}")
        return prompt

    def delete_prompt(self, prompt_id: int, user_id: int) -> bool:
        """
        删除提示词

        Args:
            prompt_id: 提示词ID
            user_id: 用户ID

        Returns:
            是否删除成功
        """
        prompt = (
            self.db.query(SystemPrompt)
            .filter(
                SystemPrompt.id == prompt_id,
                SystemPrompt.user_id == user_id,  # 只能删除自己的提示词
                SystemPrompt.is_system == False,  # 不能删除系统提示词
            )
            .first()
        )

        if not prompt:
            return False

        self.db.delete(prompt)
        self.db.commit()

        logger.info(f"删除提示词成功: prompt_id={prompt_id}")
        return True

    def set_default_prompt(self, prompt_id: int, user_id: int) -> bool:
        """
        设置默认提示词

        Args:
            prompt_id: 提示词ID
            user_id: 用户ID

        Returns:
            是否设置成功
        """
        # 检查提示词是否存在且用户有权限访问
        prompt = self.get_prompt_by_id(prompt_id, user_id)
        if not prompt:
            return False

        # 取消当前用户的其他默认提示词
        self.db.query(SystemPrompt).filter(
            SystemPrompt.user_id == user_id, SystemPrompt.is_default == True
        ).update({"is_default": False})

        # 如果是用户自己的提示词，设置为默认
        if prompt.user_id == user_id:
            prompt.is_default = True
        # 如果是系统提示词，需要创建用户偏好记录或使用其他方式记录
        # 当前简化实现：系统提示词不能被设为用户默认，但可以在对话中选择使用

        self.db.commit()

        logger.info(f"设置默认提示词成功: user_id={user_id}, prompt_id={prompt_id}")
        return True

    def get_default_prompt(self, user_id: int) -> Optional[SystemPrompt]:
        """
        获取用户的默认提示词

        Args:
            user_id: 用户ID

        Returns:
            默认提示词或None
        """
        # 先查找用户自定义的默认提示词
        prompt = (
            self.db.query(SystemPrompt)
            .filter(SystemPrompt.user_id == user_id, SystemPrompt.is_default == True)
            .first()
        )

        if prompt:
            return prompt

        # 如果没有，返回系统默认提示词
        return (
            self.db.query(SystemPrompt)
            .filter(SystemPrompt.is_system == True, SystemPrompt.is_default == True)
            .first()
        )

    def init_system_prompts(self):
        """初始化系统内置提示词"""
        system_prompts = [
            {
                "name": "通用助手",
                "content": "你是一个智能助手，可以帮助用户解答各种问题。请用简洁、准确的语言回答用户的问题。",
                "category": "general",
                "is_default": True,
            },
            {
                "name": "专业顾问",
                "content": "你是一个专业的顾问，擅长提供深入、专业的分析和建议。请基于事实和逻辑进行回答，必要时引用相关资料。",
                "category": "professional",
                "is_default": False,
            },
            {
                "name": "创意写手",
                "content": "你是一个富有创意的写作助手，擅长创作各种文体的内容。请发挥想象力，创作出有趣、生动的内容。",
                "category": "creative",
                "is_default": False,
            },
        ]

        for prompt_data in system_prompts:
            existing = (
                self.db.query(SystemPrompt)
                .filter(
                    SystemPrompt.is_system == True,
                    SystemPrompt.name == prompt_data["name"],
                )
                .first()
            )

            if not existing:
                prompt = SystemPrompt(user_id=None, is_system=True, **prompt_data)
                self.db.add(prompt)

        self.db.commit()
        logger.info("系统提示词初始化完成")


__all__ = ["SystemPromptService"]
