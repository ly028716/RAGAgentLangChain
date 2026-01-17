"""
消息数据访问层（Repository）

封装消息相关的数据库操作，提供统一的数据访问接口。
实现CRUD操作、分页查询和token统计功能。
"""

from typing import Optional, List, Tuple
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, asc

from app.models.message import Message, MessageRole


class MessageRepository:
    """
    消息Repository类
    
    提供消息数据的CRUD操作和查询功能。
    支持分页查询、按对话查询和token统计。
    
    使用方式:
        repo = MessageRepository(db)
        message = repo.create(conversation_id=1, role=MessageRole.USER, content="你好")
        messages = repo.get_by_conversation(conversation_id=1)
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
        conversation_id: int,
        role: MessageRole,
        content: str,
        tokens: int = 0
    ) -> Message:
        """
        创建新消息
        
        Args:
            conversation_id: 对话ID
            role: 消息角色（user/assistant/system）
            content: 消息内容
            tokens: 消耗的token数量，默认为0
        
        Returns:
            Message: 创建的消息对象
        """
        message = Message(
            conversation_id=conversation_id,
            role=role,
            content=content,
            tokens=tokens
        )
        self.db.add(message)
        self.db.commit()
        self.db.refresh(message)
        return message
    
    def get_by_id(self, message_id: int) -> Optional[Message]:
        """
        根据ID获取消息
        
        Args:
            message_id: 消息ID
        
        Returns:
            Optional[Message]: 消息对象，不存在则返回None
        """
        return self.db.query(Message).filter(
            Message.id == message_id
        ).first()
    
    def get_by_conversation(
        self,
        conversation_id: int,
        skip: int = 0,
        limit: Optional[int] = None,
        order_asc: bool = True
    ) -> List[Message]:
        """
        获取对话的所有消息
        
        按创建时间排序，默认升序（从旧到新）。
        
        Args:
            conversation_id: 对话ID
            skip: 跳过的记录数
            limit: 返回的最大记录数，None表示不限制
            order_asc: 是否升序排列，默认True
        
        Returns:
            List[Message]: 消息列表
        """
        query = self.db.query(Message).filter(
            Message.conversation_id == conversation_id
        )
        
        # 排序
        if order_asc:
            query = query.order_by(asc(Message.created_at))
        else:
            query = query.order_by(desc(Message.created_at))
        
        # 分页
        query = query.offset(skip)
        if limit is not None:
            query = query.limit(limit)
        
        return query.all()

    
    def get_by_conversation_paginated(
        self,
        conversation_id: int,
        skip: int = 0,
        limit: int = 50
    ) -> Tuple[List[Message], int]:
        """
        获取对话的消息列表（分页）
        
        按创建时间升序排列，返回消息列表和总数。
        
        Args:
            conversation_id: 对话ID
            skip: 跳过的记录数
            limit: 返回的最大记录数
        
        Returns:
            Tuple[List[Message], int]: (消息列表, 总数)
        """
        query = self.db.query(Message).filter(
            Message.conversation_id == conversation_id
        )
        
        # 获取总数
        total = query.count()
        
        # 按创建时间升序排列并分页
        messages = query.order_by(
            asc(Message.created_at)
        ).offset(skip).limit(limit).all()
        
        return messages, total
    
    def get_recent_messages(
        self,
        conversation_id: int,
        limit: int = 10
    ) -> List[Message]:
        """
        获取对话的最近消息
        
        按创建时间倒序获取，然后反转为正序返回。
        用于获取对话上下文。
        
        Args:
            conversation_id: 对话ID
            limit: 返回的最大记录数
        
        Returns:
            List[Message]: 消息列表（按时间正序）
        """
        messages = self.db.query(Message).filter(
            Message.conversation_id == conversation_id
        ).order_by(
            desc(Message.created_at)
        ).limit(limit).all()
        
        # 反转为正序
        return list(reversed(messages))
    
    def get_first_user_message(
        self,
        conversation_id: int
    ) -> Optional[Message]:
        """
        获取对话的第一条用户消息
        
        用于自动生成对话标题。
        
        Args:
            conversation_id: 对话ID
        
        Returns:
            Optional[Message]: 第一条用户消息，不存在则返回None
        """
        return self.db.query(Message).filter(
            Message.conversation_id == conversation_id,
            Message.role == MessageRole.USER
        ).order_by(
            asc(Message.created_at)
        ).first()
    
    def update_tokens(
        self,
        message_id: int,
        tokens: int
    ) -> Optional[Message]:
        """
        更新消息的token数量
        
        Args:
            message_id: 消息ID
            tokens: token数量
        
        Returns:
            Optional[Message]: 更新后的消息对象，消息不存在则返回None
        """
        message = self.get_by_id(message_id)
        if not message:
            return None
        
        message.tokens = tokens
        self.db.commit()
        self.db.refresh(message)
        return message
    
    def delete(self, message_id: int) -> bool:
        """
        删除消息
        
        Args:
            message_id: 消息ID
        
        Returns:
            bool: 删除成功返回True，消息不存在返回False
        """
        message = self.get_by_id(message_id)
        if not message:
            return False
        
        self.db.delete(message)
        self.db.commit()
        return True
    
    def delete_by_conversation(self, conversation_id: int) -> int:
        """
        删除对话的所有消息
        
        Args:
            conversation_id: 对话ID
        
        Returns:
            int: 删除的消息数量
        """
        count = self.db.query(Message).filter(
            Message.conversation_id == conversation_id
        ).delete()
        self.db.commit()
        return count

    
    def count_by_conversation(self, conversation_id: int) -> int:
        """
        获取对话的消息数量
        
        Args:
            conversation_id: 对话ID
        
        Returns:
            int: 消息数量
        """
        return self.db.query(Message).filter(
            Message.conversation_id == conversation_id
        ).count()
    
    def get_total_tokens(self, conversation_id: int) -> int:
        """
        获取对话的总token消耗
        
        Args:
            conversation_id: 对话ID
        
        Returns:
            int: 总token数量
        """
        result = self.db.query(
            func.sum(Message.tokens)
        ).filter(
            Message.conversation_id == conversation_id
        ).scalar()
        return result or 0
    
    def get_tokens_by_role(
        self,
        conversation_id: int,
        role: MessageRole
    ) -> int:
        """
        获取对话中指定角色的总token消耗
        
        Args:
            conversation_id: 对话ID
            role: 消息角色
        
        Returns:
            int: 总token数量
        """
        result = self.db.query(
            func.sum(Message.tokens)
        ).filter(
            Message.conversation_id == conversation_id,
            Message.role == role
        ).scalar()
        return result or 0
    
    def get_last_message(
        self,
        conversation_id: int
    ) -> Optional[Message]:
        """
        获取对话的最后一条消息
        
        Args:
            conversation_id: 对话ID
        
        Returns:
            Optional[Message]: 最后一条消息，不存在则返回None
        """
        return self.db.query(Message).filter(
            Message.conversation_id == conversation_id
        ).order_by(
            desc(Message.created_at)
        ).first()
    
    def get_messages_by_role(
        self,
        conversation_id: int,
        role: MessageRole
    ) -> List[Message]:
        """
        获取对话中指定角色的所有消息
        
        Args:
            conversation_id: 对话ID
            role: 消息角色
        
        Returns:
            List[Message]: 消息列表
        """
        return self.db.query(Message).filter(
            Message.conversation_id == conversation_id,
            Message.role == role
        ).order_by(
            asc(Message.created_at)
        ).all()
    
    def exists(self, message_id: int) -> bool:
        """
        检查消息是否存在
        
        Args:
            message_id: 消息ID
        
        Returns:
            bool: 存在返回True，否则返回False
        """
        return self.db.query(Message).filter(
            Message.id == message_id
        ).first() is not None
    
    def bulk_create(
        self,
        messages: List[dict]
    ) -> List[Message]:
        """
        批量创建消息
        
        Args:
            messages: 消息数据列表，每个字典包含:
                - conversation_id: 对话ID
                - role: 消息角色
                - content: 消息内容
                - tokens: token数量（可选）
        
        Returns:
            List[Message]: 创建的消息对象列表
        """
        message_objects = []
        for msg_data in messages:
            message = Message(
                conversation_id=msg_data['conversation_id'],
                role=msg_data['role'],
                content=msg_data['content'],
                tokens=msg_data.get('tokens', 0)
            )
            self.db.add(message)
            message_objects.append(message)
        
        self.db.commit()
        for message in message_objects:
            self.db.refresh(message)
        
        return message_objects


# 导出
__all__ = ['MessageRepository']
