"""
WebSocket连接管理器

管理WebSocket连接的生命周期，支持用户连接、断开和消息推送。
"""
import json
import logging
from datetime import datetime
from typing import Dict, Optional

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    """WebSocket连接管理器"""

    def __init__(self):
        # 存储活跃连接: user_id -> WebSocket
        self.active_connections: Dict[int, WebSocket] = {}
        # 连接时间记录
        self.connection_times: Dict[int, datetime] = {}

    async def connect(self, user_id: int, websocket: WebSocket):
        """
        接受WebSocket连接

        Args:
            user_id: 用户ID
            websocket: WebSocket连接对象
        """
        await websocket.accept()

        # 如果用户已有连接，先断开旧连接
        if user_id in self.active_connections:
            try:
                old_ws = self.active_connections[user_id]
                await old_ws.close(code=1000, reason="New connection established")
            except Exception as e:
                logger.warning(f"关闭旧连接失败 user_id={user_id}: {str(e)}")

        self.active_connections[user_id] = websocket
        self.connection_times[user_id] = datetime.utcnow()

        logger.info(f"WebSocket连接已建立 user_id={user_id}")

        # 发送欢迎消息
        await self.send_personal_message(
            user_id,
            {
                "type": "connection_established",
                "data": {
                    "message": "WebSocket连接成功",
                    "timestamp": datetime.utcnow().isoformat(),
                },
            },
        )

    def disconnect(self, user_id: int):
        """
        断开WebSocket连接

        Args:
            user_id: 用户ID
        """
        if user_id in self.active_connections:
            del self.active_connections[user_id]

        if user_id in self.connection_times:
            connection_duration = (
                datetime.utcnow() - self.connection_times[user_id]
            ).total_seconds()
            del self.connection_times[user_id]
            logger.info(
                f"WebSocket连接已断开 user_id={user_id}, 持续时间={connection_duration:.2f}秒"
            )
        else:
            logger.info(f"WebSocket连接已断开 user_id={user_id}")

    async def send_personal_message(self, user_id: int, message: dict):
        """
        向指定用户发送消息

        Args:
            user_id: 用户ID
            message: 消息内容（字典格式）
        """
        if user_id in self.active_connections:
            try:
                websocket = self.active_connections[user_id]
                await websocket.send_json(message)
                logger.debug(f"消息已发送 user_id={user_id}, type={message.get('type')}")
            except Exception as e:
                logger.error(f"发送消息失败 user_id={user_id}: {str(e)}")
                # 连接可能已断开，清理连接
                self.disconnect(user_id)
        else:
            logger.debug(f"用户未连接，消息未发送 user_id={user_id}")

    async def send_text_message(self, user_id: int, text: str):
        """
        向指定用户发送文本消息

        Args:
            user_id: 用户ID
            text: 文本消息
        """
        if user_id in self.active_connections:
            try:
                websocket = self.active_connections[user_id]
                await websocket.send_text(text)
                logger.debug(f"文本消息已发送 user_id={user_id}")
            except Exception as e:
                logger.error(f"发送文本消息失败 user_id={user_id}: {str(e)}")
                self.disconnect(user_id)

    async def broadcast(self, message: dict, exclude_user_ids: Optional[list] = None):
        """
        广播消息给所有连接的用户

        Args:
            message: 消息内容（字典格式）
            exclude_user_ids: 排除的用户ID列表
        """
        exclude_user_ids = exclude_user_ids or []

        disconnected_users = []
        for user_id, websocket in self.active_connections.items():
            if user_id in exclude_user_ids:
                continue

            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"广播消息失败 user_id={user_id}: {str(e)}")
                disconnected_users.append(user_id)

        # 清理断开的连接
        for user_id in disconnected_users:
            self.disconnect(user_id)

        logger.info(
            f"消息已广播给 {len(self.active_connections) - len(exclude_user_ids)} 个用户"
        )

    def is_connected(self, user_id: int) -> bool:
        """
        检查用户是否已连接

        Args:
            user_id: 用户ID

        Returns:
            bool: 是否已连接
        """
        return user_id in self.active_connections

    def get_connected_users(self) -> list:
        """
        获取所有已连接的用户ID列表

        Returns:
            list: 用户ID列表
        """
        return list(self.active_connections.keys())

    def get_connection_count(self) -> int:
        """
        获取当前连接数

        Returns:
            int: 连接数
        """
        return len(self.active_connections)

    def get_connection_info(self, user_id: int) -> Optional[dict]:
        """
        获取用户连接信息

        Args:
            user_id: 用户ID

        Returns:
            dict: 连接信息，如果用户未连接则返回None
        """
        if user_id not in self.active_connections:
            return None

        connection_time = self.connection_times.get(user_id)
        duration = None
        if connection_time:
            duration = (datetime.utcnow() - connection_time).total_seconds()

        return {
            "user_id": user_id,
            "connected": True,
            "connection_time": connection_time.isoformat() if connection_time else None,
            "duration_seconds": duration,
        }


# 全局连接管理器实例
connection_manager = ConnectionManager()
