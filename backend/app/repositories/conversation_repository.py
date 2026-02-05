"""
对话数据访问层（Repository）

封装对话相关的数据库操作，提供统一的数据访问接口。
实现CRUD操作、分页查询和软删除功能。
"""

from datetime import datetime
from typing import List, Optional, Tuple

from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from app.models.conversation import Conversation
from app.models.message import Message


class ConversationRepository:
    """
    对话Repository类

    提供对话数据的CRUD操作和查询功能。
    支持分页查询、软删除和消息计数。

    使用方式:
        repo = ConversationRepository(db)
        conversation = repo.create(user_id=1, title="新对话")
        conversations, total = repo.get_by_user(user_id=1, skip=0, limit=20)
    """

    def __init__(self, db: Session):
        """
        初始化Repository

        Args:
            db: SQLAlchemy数据库会话
        """
        self.db = db

    def create(self, user_id: int, title: str = "新对话") -> Conversation:
        """
        创建新对话

        Args:
            user_id: 用户ID
            title: 对话标题，默认为"新对话"

        Returns:
            Conversation: 创建的对话对象
        """
        conversation = Conversation(user_id=user_id, title=title)
        self.db.add(conversation)
        self.db.commit()
        self.db.refresh(conversation)
        return conversation

    def get_by_id(self, conversation_id: int) -> Optional[Conversation]:
        """
        根据ID获取对话

        Args:
            conversation_id: 对话ID

        Returns:
            Optional[Conversation]: 对话对象，不存在则返回None
        """
        return (
            self.db.query(Conversation)
            .filter(Conversation.id == conversation_id)
            .first()
        )

    def get_by_id_and_user(
        self, conversation_id: int, user_id: int, include_deleted: bool = False
    ) -> Optional[Conversation]:
        """
        根据ID和用户ID获取对话

        Args:
            conversation_id: 对话ID
            user_id: 用户ID
            include_deleted: 是否包含已删除的对话

        Returns:
            Optional[Conversation]: 对话对象，不存在或不属于该用户则返回None
        """
        query = self.db.query(Conversation).filter(
            Conversation.id == conversation_id, Conversation.user_id == user_id
        )
        if not include_deleted:
            query = query.filter(Conversation.is_deleted == False)
        return query.first()

    def get_by_user(
        self,
        user_id: int,
        skip: int = 0,
        limit: int = 20,
        include_deleted: bool = False,
    ) -> Tuple[List[Conversation], int]:
        """
        获取用户的对话列表（分页）

        按更新时间倒序排列，返回对话列表和总数。

        Args:
            user_id: 用户ID
            skip: 跳过的记录数
            limit: 返回的最大记录数
            include_deleted: 是否包含已删除的对话

        Returns:
            Tuple[List[Conversation], int]: (对话列表, 总数)
        """
        query = self.db.query(Conversation).filter(Conversation.user_id == user_id)
        if not include_deleted:
            query = query.filter(Conversation.is_deleted == False)

        # 获取总数
        total = query.count()

        # 按更新时间倒序排列并分页
        conversations = (
            query.order_by(desc(Conversation.updated_at))
            .offset(skip)
            .limit(limit)
            .all()
        )

        return conversations, total

    def update(
        self, conversation_id: int, user_id: int, title: Optional[str] = None
    ) -> Optional[Conversation]:
        """
        更新对话信息

        Args:
            conversation_id: 对话ID
            user_id: 用户ID（用于权限验证）
            title: 新标题（可选）

        Returns:
            Optional[Conversation]: 更新后的对话对象，对话不存在或不属于该用户则返回None
        """
        conversation = self.get_by_id_and_user(conversation_id, user_id)
        if not conversation:
            return None

        if title is not None:
            conversation.title = title

        # 更新时间会自动更新（onupdate）
        self.db.commit()
        self.db.refresh(conversation)
        return conversation

    def update_title(self, conversation_id: int, title: str) -> Optional[Conversation]:
        """
        更新对话标题（不验证用户）

        用于系统自动生成标题等场景。

        Args:
            conversation_id: 对话ID
            title: 新标题

        Returns:
            Optional[Conversation]: 更新后的对话对象，对话不存在则返回None
        """
        conversation = self.get_by_id(conversation_id)
        if not conversation:
            return None

        conversation.title = title
        self.db.commit()
        self.db.refresh(conversation)
        return conversation

    def soft_delete(self, conversation_id: int, user_id: int) -> bool:
        """
        软删除对话

        将对话的is_deleted字段标记为True，而非物理删除。

        Args:
            conversation_id: 对话ID
            user_id: 用户ID（用于权限验证）

        Returns:
            bool: 删除成功返回True，对话不存在或不属于该用户返回False
        """
        conversation = self.get_by_id_and_user(conversation_id, user_id)
        if not conversation:
            return False

        conversation.is_deleted = True
        self.db.commit()
        return True

    def restore(self, conversation_id: int, user_id: int) -> Optional[Conversation]:
        """
        恢复已删除的对话

        Args:
            conversation_id: 对话ID
            user_id: 用户ID（用于权限验证）

        Returns:
            Optional[Conversation]: 恢复后的对话对象，对话不存在或不属于该用户返回None
        """
        conversation = self.get_by_id_and_user(
            conversation_id, user_id, include_deleted=True
        )
        if not conversation:
            return None

        conversation.is_deleted = False
        self.db.commit()
        self.db.refresh(conversation)
        return conversation

    def hard_delete(self, conversation_id: int, user_id: int) -> bool:
        """
        物理删除对话

        永久删除对话及其所有消息（通过级联删除）。

        Args:
            conversation_id: 对话ID
            user_id: 用户ID（用于权限验证）

        Returns:
            bool: 删除成功返回True，对话不存在或不属于该用户返回False
        """
        conversation = self.get_by_id_and_user(
            conversation_id, user_id, include_deleted=True
        )
        if not conversation:
            return False

        self.db.delete(conversation)
        self.db.commit()
        return True

    def count_by_user(self, user_id: int, include_deleted: bool = False) -> int:
        """
        获取用户的对话总数

        Args:
            user_id: 用户ID
            include_deleted: 是否包含已删除的对话

        Returns:
            int: 对话总数
        """
        query = self.db.query(Conversation).filter(Conversation.user_id == user_id)
        if not include_deleted:
            query = query.filter(Conversation.is_deleted == False)
        return query.count()

    def get_message_count(self, conversation_id: int) -> int:
        """
        获取对话的消息数量

        Args:
            conversation_id: 对话ID

        Returns:
            int: 消息数量
        """
        return (
            self.db.query(Message)
            .filter(Message.conversation_id == conversation_id)
            .count()
        )

    def get_message_counts_batch(self, conversation_ids: List[int]) -> dict:
        """
        批量获取多个对话的消息数量

        使用单次查询获取多个对话的消息计数，避免 N+1 查询问题。

        Args:
            conversation_ids: 对话ID列表

        Returns:
            dict: {conversation_id: message_count} 的字典
        """
        if not conversation_ids:
            return {}

        # 使用 GROUP BY 一次性获取所有对话的消息计数
        counts = (
            self.db.query(
                Message.conversation_id, func.count(Message.id).label("count")
            )
            .filter(Message.conversation_id.in_(conversation_ids))
            .group_by(Message.conversation_id)
            .all()
        )

        # 转换为字典，未找到的对话计数为 0
        result = {conv_id: 0 for conv_id in conversation_ids}
        for conv_id, count in counts:
            result[conv_id] = count

        return result

    def touch(self, conversation_id: int) -> Optional[Conversation]:
        """
        更新对话的更新时间

        用于在添加新消息后更新对话的updated_at字段。

        Args:
            conversation_id: 对话ID

        Returns:
            Optional[Conversation]: 更新后的对话对象，对话不存在则返回None
        """
        conversation = self.get_by_id(conversation_id)
        if not conversation:
            return None

        conversation.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(conversation)
        return conversation

    def exists(
        self, conversation_id: int, user_id: int, include_deleted: bool = False
    ) -> bool:
        """
        检查对话是否存在且属于指定用户

        Args:
            conversation_id: 对话ID
            user_id: 用户ID
            include_deleted: 是否包含已删除的对话

        Returns:
            bool: 存在返回True，否则返回False
        """
        query = self.db.query(Conversation).filter(
            Conversation.id == conversation_id, Conversation.user_id == user_id
        )
        if not include_deleted:
            query = query.filter(Conversation.is_deleted == False)
        return query.first() is not None


# 导出
__all__ = ["ConversationRepository"]
