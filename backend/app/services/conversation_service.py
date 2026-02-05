"""
对话服务模块

实现对话管理相关业务逻辑，包括对话创建、查询、更新、删除和消息管理。

需求引用:
    - 需求2.1: 创建对话并返回唯一对话ID
    - 需求2.4: 查询对话历史，按更新时间倒序排列，支持分页
    - 需求2.5: 软删除对话
    - 需求2.6: 导出对话内容为Markdown或JSON格式
    - 需求2.8: 自动根据消息内容生成对话标题
"""

import json
import logging
from datetime import datetime
from typing import List, Optional, Tuple

from sqlalchemy.orm import Session

from app.models.conversation import Conversation
from app.models.message import Message, MessageRole
from app.repositories.conversation_repository import ConversationRepository
from app.repositories.message_repository import MessageRepository

logger = logging.getLogger(__name__)


class ConversationServiceError(Exception):
    """对话服务异常基类"""

    pass


class ConversationNotFoundError(ConversationServiceError):
    """对话不存在异常"""

    pass


class ConversationAccessDeniedError(ConversationServiceError):
    """对话访问被拒绝异常"""

    pass


class ConversationService:
    """
    对话服务类

    提供对话管理功能，包括创建、查询、更新、删除对话和消息管理。

    使用方式:
        service = ConversationService(db)
        conversation = service.create_conversation(user_id=1, title="新对话")
        conversations, total = service.get_conversations(user_id=1, skip=0, limit=20)
    """

    def __init__(self, db: Session):
        """
        初始化对话服务

        Args:
            db: SQLAlchemy数据库会话
        """
        self.db = db
        self.conversation_repo = ConversationRepository(db)
        self.message_repo = MessageRepository(db)

    def create_conversation(self, user_id: int, title: str = "新对话") -> Conversation:
        """
        创建新对话

        Args:
            user_id: 用户ID
            title: 对话标题，默认为"新对话"

        Returns:
            Conversation: 创建的对话对象

        需求引用:
            - 需求2.1: 创建对话记录并返回唯一对话ID，默认标题为"新对话"
        """
        conversation = self.conversation_repo.create(user_id=user_id, title=title)
        return conversation

    def get_conversations(
        self, user_id: int, skip: int = 0, limit: int = 20
    ) -> Tuple[List[dict], int]:
        """
        获取用户的对话列表（分页）

        按更新时间倒序排列，返回对话列表和总数。
        每个对话包含消息数量统计。

        Args:
            user_id: 用户ID
            skip: 跳过的记录数
            limit: 返回的最大记录数

        Returns:
            Tuple[List[dict], int]: (对话列表, 总数)

        需求引用:
            - 需求2.4: 返回用户所有未删除的对话列表，按更新时间倒序排列，支持分页查询
        """
        conversations, total = self.conversation_repo.get_by_user(
            user_id=user_id, skip=skip, limit=limit, include_deleted=False
        )

        # 批量获取所有对话的消息数量，避免 N+1 查询
        conversation_ids = [conv.id for conv in conversations]
        message_counts = self.conversation_repo.get_message_counts_batch(
            conversation_ids
        )

        # 为每个对话添加消息数量
        result = []
        for conv in conversations:
            result.append(
                {
                    "id": conv.id,
                    "title": conv.title,
                    "created_at": conv.created_at,
                    "updated_at": conv.updated_at,
                    "message_count": message_counts.get(conv.id, 0),
                }
            )

        return result, total

    def get_conversation(self, conversation_id: int, user_id: int) -> Conversation:
        """
        获取单个对话

        Args:
            conversation_id: 对话ID
            user_id: 用户ID（用于权限验证）

        Returns:
            Conversation: 对话对象

        Raises:
            ConversationNotFoundError: 对话不存在或不属于该用户
        """
        conversation = self.conversation_repo.get_by_id_and_user(
            conversation_id=conversation_id, user_id=user_id
        )

        if not conversation:
            raise ConversationNotFoundError(f"对话 {conversation_id} 不存在或无权访问")

        return conversation

    def update_conversation(
        self, conversation_id: int, user_id: int, title: str
    ) -> Conversation:
        """
        更新对话标题

        Args:
            conversation_id: 对话ID
            user_id: 用户ID（用于权限验证）
            title: 新标题

        Returns:
            Conversation: 更新后的对话对象

        Raises:
            ConversationNotFoundError: 对话不存在或不属于该用户
        """
        conversation = self.conversation_repo.update(
            conversation_id=conversation_id, user_id=user_id, title=title
        )

        if not conversation:
            raise ConversationNotFoundError(f"对话 {conversation_id} 不存在或无权访问")

        return conversation

    def delete_conversation(self, conversation_id: int, user_id: int) -> bool:
        """
        软删除对话

        将对话的is_deleted字段标记为True，而非物理删除。

        Args:
            conversation_id: 对话ID
            user_id: 用户ID（用于权限验证）

        Returns:
            bool: 删除成功返回True

        Raises:
            ConversationNotFoundError: 对话不存在或不属于该用户

        需求引用:
            - 需求2.5: 将对话记录的is_deleted字段标记为true而非物理删除
        """
        success = self.conversation_repo.soft_delete(
            conversation_id=conversation_id, user_id=user_id
        )

        if not success:
            raise ConversationNotFoundError(f"对话 {conversation_id} 不存在或无权访问")

        return True

    def get_messages(
        self,
        conversation_id: int,
        user_id: int,
        skip: int = 0,
        limit: Optional[int] = None,
    ) -> List[Message]:
        """
        获取对话的所有消息

        按创建时间升序排列（从旧到新）。

        Args:
            conversation_id: 对话ID
            user_id: 用户ID（用于权限验证）
            skip: 跳过的记录数
            limit: 返回的最大记录数，None表示不限制

        Returns:
            List[Message]: 消息列表

        Raises:
            ConversationNotFoundError: 对话不存在或不属于该用户
        """
        # 验证对话存在且属于该用户
        conversation = self.conversation_repo.get_by_id_and_user(
            conversation_id=conversation_id, user_id=user_id
        )

        if not conversation:
            raise ConversationNotFoundError(f"对话 {conversation_id} 不存在或无权访问")

        messages = self.message_repo.get_by_conversation(
            conversation_id=conversation_id, skip=skip, limit=limit, order_asc=True
        )

        return messages

    def add_message(
        self,
        conversation_id: int,
        user_id: int,
        role: MessageRole,
        content: str,
        tokens: int = 0,
    ) -> Message:
        """
        添加消息到对话

        Args:
            conversation_id: 对话ID
            user_id: 用户ID（用于权限验证）
            role: 消息角色
            content: 消息内容
            tokens: 消耗的token数量

        Returns:
            Message: 创建的消息对象

        Raises:
            ConversationNotFoundError: 对话不存在或不属于该用户
        """
        # 验证对话存在且属于该用户
        conversation = self.conversation_repo.get_by_id_and_user(
            conversation_id=conversation_id, user_id=user_id
        )

        if not conversation:
            raise ConversationNotFoundError(f"对话 {conversation_id} 不存在或无权访问")

        # 创建消息
        message = self.message_repo.create(
            conversation_id=conversation_id, role=role, content=content, tokens=tokens
        )

        # 更新对话的更新时间
        self.conversation_repo.touch(conversation_id)

        return message

    def get_recent_messages(
        self, conversation_id: int, user_id: int, limit: int = 10
    ) -> List[Message]:
        """
        获取对话的最近消息

        用于获取对话上下文。

        Args:
            conversation_id: 对话ID
            user_id: 用户ID（用于权限验证）
            limit: 返回的最大记录数

        Returns:
            List[Message]: 消息列表（按时间正序）

        Raises:
            ConversationNotFoundError: 对话不存在或不属于该用户
        """
        # 验证对话存在且属于该用户
        conversation = self.conversation_repo.get_by_id_and_user(
            conversation_id=conversation_id, user_id=user_id
        )

        if not conversation:
            raise ConversationNotFoundError(f"对话 {conversation_id} 不存在或无权访问")

        return self.message_repo.get_recent_messages(
            conversation_id=conversation_id, limit=limit
        )

    def get_conversation_token_usage(self, conversation_id: int, user_id: int) -> int:
        """
        获取对话的总token消耗

        Args:
            conversation_id: 对话ID
            user_id: 用户ID（用于权限验证）

        Returns:
            int: 总token数量

        Raises:
            ConversationNotFoundError: 对话不存在或不属于该用户
        """
        # 验证对话存在且属于该用户
        conversation = self.conversation_repo.get_by_id_and_user(
            conversation_id=conversation_id, user_id=user_id
        )

        if not conversation:
            raise ConversationNotFoundError(f"对话 {conversation_id} 不存在或无权访问")

        return self.message_repo.get_total_tokens(conversation_id)

    def update_conversation_title(
        self, conversation_id: int, title: str
    ) -> Optional[Conversation]:
        """
        更新对话标题（不验证用户）

        用于系统自动生成标题等场景。

        Args:
            conversation_id: 对话ID
            title: 新标题

        Returns:
            Optional[Conversation]: 更新后的对话对象
        """
        return self.conversation_repo.update_title(
            conversation_id=conversation_id, title=title
        )

    def conversation_exists(self, conversation_id: int, user_id: int) -> bool:
        """
        检查对话是否存在且属于指定用户

        Args:
            conversation_id: 对话ID
            user_id: 用户ID

        Returns:
            bool: 存在返回True，否则返回False
        """
        return self.conversation_repo.exists(
            conversation_id=conversation_id, user_id=user_id
        )

    def export_conversation(
        self, conversation_id: int, user_id: int, format: str = "markdown"
    ) -> str:
        """
        导出对话内容

        将对话的所有消息导出为Markdown或JSON格式。

        Args:
            conversation_id: 对话ID
            user_id: 用户ID（用于权限验证）
            format: 导出格式，支持 "markdown" 或 "json"

        Returns:
            str: 导出的内容字符串

        Raises:
            ConversationNotFoundError: 对话不存在或不属于该用户
            ValueError: 不支持的导出格式

        需求引用:
            - 需求2.6: 生成包含所有消息的Markdown或JSON格式文件
        """
        # 验证格式
        format = format.lower()
        if format not in ("markdown", "json", "md"):
            raise ValueError(f"不支持的导出格式: {format}，支持的格式: markdown, json")

        # 获取对话
        conversation = self.conversation_repo.get_by_id_and_user(
            conversation_id=conversation_id, user_id=user_id
        )

        if not conversation:
            raise ConversationNotFoundError(f"对话 {conversation_id} 不存在或无权访问")

        # 获取所有消息
        messages = self.message_repo.get_by_conversation(
            conversation_id=conversation_id, skip=0, limit=None, order_asc=True
        )

        if format in ("markdown", "md"):
            return self._export_to_markdown(conversation, messages)
        else:
            return self._export_to_json(conversation, messages)

    def _export_to_markdown(
        self, conversation: Conversation, messages: List[Message]
    ) -> str:
        """
        将对话导出为Markdown格式

        Args:
            conversation: 对话对象
            messages: 消息列表

        Returns:
            str: Markdown格式的对话内容
        """
        lines = []

        # 标题
        lines.append(f"# {conversation.title}")
        lines.append("")

        # 元信息
        lines.append(
            f"**创建时间:** {conversation.created_at.strftime('%Y-%m-%d %H:%M:%S')}"
        )
        lines.append(
            f"**更新时间:** {conversation.updated_at.strftime('%Y-%m-%d %H:%M:%S')}"
        )
        lines.append(f"**消息数量:** {len(messages)}")
        lines.append("")
        lines.append("---")
        lines.append("")

        # 消息内容
        for msg in messages:
            role_display = {
                MessageRole.USER: "👤 用户",
                MessageRole.ASSISTANT: "🤖 AI助手",
                MessageRole.SYSTEM: "⚙️ 系统",
            }.get(msg.role, str(msg.role.value))

            lines.append(f"### {role_display}")
            lines.append(f"*{msg.created_at.strftime('%Y-%m-%d %H:%M:%S')}*")
            lines.append("")
            lines.append(msg.content)
            lines.append("")

            if msg.tokens > 0:
                lines.append(f"*Token消耗: {msg.tokens}*")
                lines.append("")

        return "\n".join(lines)

    def _export_to_json(
        self, conversation: Conversation, messages: List[Message]
    ) -> str:
        """
        将对话导出为JSON格式

        Args:
            conversation: 对话对象
            messages: 消息列表

        Returns:
            str: JSON格式的对话内容
        """
        data = {
            "conversation": {
                "id": conversation.id,
                "title": conversation.title,
                "created_at": conversation.created_at.isoformat(),
                "updated_at": conversation.updated_at.isoformat(),
            },
            "messages": [
                {
                    "id": msg.id,
                    "role": msg.role.value,
                    "content": msg.content,
                    "tokens": msg.tokens,
                    "created_at": msg.created_at.isoformat(),
                }
                for msg in messages
            ],
            "statistics": {
                "message_count": len(messages),
                "total_tokens": sum(msg.tokens for msg in messages),
                "user_messages": sum(
                    1 for msg in messages if msg.role == MessageRole.USER
                ),
                "assistant_messages": sum(
                    1 for msg in messages if msg.role == MessageRole.ASSISTANT
                ),
            },
            "exported_at": datetime.utcnow().isoformat(),
        }

        return json.dumps(data, ensure_ascii=False, indent=2)

    async def generate_title(self, first_message: str, max_length: int = 20) -> str:
        """
        使用LLM根据第一条消息生成对话标题

        Args:
            first_message: 第一条用户消息内容
            max_length: 标题最大长度，默认20个字符

        Returns:
            str: 生成的对话标题

        需求引用:
            - 需求2.8: 自动根据消息内容生成对话标题（最多20个字符）
        """
        from app.core.llm import invoke_llm

        prompt = f"""请根据以下用户消息，生成一个简短的对话标题。

要求：
1. 标题长度不超过{max_length}个字符
2. 标题要简洁明了，概括消息的主题
3. 只返回标题文本，不要包含任何其他内容
4. 不要使用引号包裹标题

用户消息：
{first_message[:500]}

标题："""

        try:
            title = await invoke_llm(
                prompt=prompt, temperature=0.3, max_tokens=50  # 使用较低温度以获得更稳定的输出
            )

            # 清理标题
            title = title.strip()

            # 移除可能的引号
            if title.startswith('"') and title.endswith('"'):
                title = title[1:-1]
            if title.startswith("'") and title.endswith("'"):
                title = title[1:-1]
            if title.startswith("《") and title.endswith("》"):
                title = title[1:-1]

            # 截断到最大长度
            if len(title) > max_length:
                title = title[: max_length - 1] + "…"

            # 如果标题为空，返回默认值
            if not title:
                title = "新对话"

            logger.info(f"生成对话标题: {title}")
            return title

        except Exception as e:
            logger.error(f"生成对话标题失败: {str(e)}")
            # 失败时返回默认标题
            return "新对话"

    def generate_title_sync(self, first_message: str, max_length: int = 20) -> str:
        """
        同步版本：使用LLM根据第一条消息生成对话标题

        Args:
            first_message: 第一条用户消息内容
            max_length: 标题最大长度，默认20个字符

        Returns:
            str: 生成的对话标题

        需求引用:
            - 需求2.8: 自动根据消息内容生成对话标题（最多20个字符）
        """
        from app.core.llm import invoke_llm_sync

        prompt = f"""请根据以下用户消息，生成一个简短的对话标题。

要求：
1. 标题长度不超过{max_length}个字符
2. 标题要简洁明了，概括消息的主题
3. 只返回标题文本，不要包含任何其他内容
4. 不要使用引号包裹标题

用户消息：
{first_message[:500]}

标题："""

        try:
            title = invoke_llm_sync(
                prompt=prompt, temperature=0.3, max_tokens=50  # 使用较低温度以获得更稳定的输出
            )

            # 清理标题
            title = title.strip()

            # 移除可能的引号
            if title.startswith('"') and title.endswith('"'):
                title = title[1:-1]
            if title.startswith("'") and title.endswith("'"):
                title = title[1:-1]
            if title.startswith("《") and title.endswith("》"):
                title = title[1:-1]

            # 截断到最大长度
            if len(title) > max_length:
                title = title[: max_length - 1] + "…"

            # 如果标题为空，返回默认值
            if not title:
                title = "新对话"

            logger.info(f"生成对话标题: {title}")
            return title

        except Exception as e:
            logger.error(f"生成对话标题失败: {str(e)}")
            # 失败时返回默认标题
            return "新对话"

    def is_first_user_message(self, conversation_id: int) -> bool:
        """
        检查对话是否还没有用户消息

        用于判断是否需要自动生成标题。

        Args:
            conversation_id: 对话ID

        Returns:
            bool: 如果没有用户消息返回True
        """
        messages = self.message_repo.get_by_conversation(
            conversation_id=conversation_id, skip=0, limit=1, order_asc=True
        )

        # 检查是否有用户消息
        user_messages = [m for m in messages if m.role == MessageRole.USER]
        return len(user_messages) == 0


# 导出
__all__ = [
    "ConversationService",
    "ConversationServiceError",
    "ConversationNotFoundError",
    "ConversationAccessDeniedError",
]
