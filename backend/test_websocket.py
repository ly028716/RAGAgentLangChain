"""
WebSocket功能测试

测试WebSocket连接管理和消息推送功能。
"""
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from fastapi import WebSocket

from app.websocket.connection_manager import ConnectionManager, connection_manager


class TestConnectionManager:
    """测试连接管理器"""
    
    @pytest.fixture
    def manager(self):
        """创建连接管理器实例"""
        return ConnectionManager()
    
    @pytest.fixture
    def mock_websocket(self):
        """创建模拟的WebSocket对象"""
        ws = Mock(spec=WebSocket)
        ws.accept = AsyncMock()
        ws.send_json = AsyncMock()
        ws.send_text = AsyncMock()
        ws.close = AsyncMock()
        return ws
    
    @pytest.mark.asyncio
    async def test_connect(self, manager, mock_websocket):
        """测试连接建立"""
        user_id = 1
        
        # 建立连接
        await manager.connect(user_id, mock_websocket)
        
        # 验证连接已建立
        assert manager.is_connected(user_id)
        assert manager.get_connection_count() == 1
        assert user_id in manager.get_connected_users()
        
        # 验证WebSocket被接受
        mock_websocket.accept.assert_called_once()
        
        # 验证发送了欢迎消息
        mock_websocket.send_json.assert_called_once()
        call_args = mock_websocket.send_json.call_args[0][0]
        assert call_args['type'] == 'connection_established'
    
    @pytest.mark.asyncio
    async def test_disconnect(self, manager, mock_websocket):
        """测试连接断开"""
        user_id = 1
        
        # 先建立连接
        await manager.connect(user_id, mock_websocket)
        assert manager.is_connected(user_id)
        
        # 断开连接
        manager.disconnect(user_id)
        
        # 验证连接已断开
        assert not manager.is_connected(user_id)
        assert manager.get_connection_count() == 0
        assert user_id not in manager.get_connected_users()
    
    @pytest.mark.asyncio
    async def test_send_personal_message(self, manager, mock_websocket):
        """测试发送个人消息"""
        user_id = 1
        message = {
            "type": "test",
            "data": {"message": "Hello"}
        }
        
        # 建立连接
        await manager.connect(user_id, mock_websocket)
        
        # 重置mock以清除欢迎消息的调用
        mock_websocket.send_json.reset_mock()
        
        # 发送消息
        await manager.send_personal_message(user_id, message)
        
        # 验证消息已发送
        mock_websocket.send_json.assert_called_once_with(message)
    
    @pytest.mark.asyncio
    async def test_send_message_to_disconnected_user(self, manager):
        """测试向未连接用户发送消息"""
        user_id = 999
        message = {"type": "test", "data": {}}
        
        # 向未连接用户发送消息（不应抛出异常）
        await manager.send_personal_message(user_id, message)
        
        # 验证用户仍未连接
        assert not manager.is_connected(user_id)
    
    @pytest.mark.asyncio
    async def test_broadcast(self, manager):
        """测试广播消息"""
        # 创建多个模拟WebSocket
        ws1 = Mock(spec=WebSocket)
        ws1.accept = AsyncMock()
        ws1.send_json = AsyncMock()
        
        ws2 = Mock(spec=WebSocket)
        ws2.accept = AsyncMock()
        ws2.send_json = AsyncMock()
        
        ws3 = Mock(spec=WebSocket)
        ws3.accept = AsyncMock()
        ws3.send_json = AsyncMock()
        
        # 建立多个连接
        await manager.connect(1, ws1)
        await manager.connect(2, ws2)
        await manager.connect(3, ws3)
        
        # 重置mock
        ws1.send_json.reset_mock()
        ws2.send_json.reset_mock()
        ws3.send_json.reset_mock()
        
        # 广播消息，排除用户2
        message = {"type": "broadcast", "data": {"message": "Hello all"}}
        await manager.broadcast(message, exclude_user_ids=[2])
        
        # 验证用户1和3收到消息，用户2未收到
        ws1.send_json.assert_called_once_with(message)
        ws2.send_json.assert_not_called()
        ws3.send_json.assert_called_once_with(message)
    
    @pytest.mark.asyncio
    async def test_replace_existing_connection(self, manager):
        """测试替换已存在的连接"""
        user_id = 1
        
        # 创建两个WebSocket
        ws1 = Mock(spec=WebSocket)
        ws1.accept = AsyncMock()
        ws1.send_json = AsyncMock()
        ws1.close = AsyncMock()
        
        ws2 = Mock(spec=WebSocket)
        ws2.accept = AsyncMock()
        ws2.send_json = AsyncMock()
        
        # 建立第一个连接
        await manager.connect(user_id, ws1)
        assert manager.get_connection_count() == 1
        
        # 建立第二个连接（应该关闭第一个）
        await manager.connect(user_id, ws2)
        
        # 验证仍然只有一个连接
        assert manager.get_connection_count() == 1
        
        # 验证旧连接被关闭
        ws1.close.assert_called_once()
    
    def test_get_connection_info(self, manager):
        """测试获取连接信息"""
        user_id = 1
        
        # 未连接时返回None
        info = manager.get_connection_info(user_id)
        assert info is None
    
    @pytest.mark.asyncio
    async def test_send_text_message(self, manager, mock_websocket):
        """测试发送文本消息"""
        user_id = 1
        text = "Hello, World!"
        
        # 建立连接
        await manager.connect(user_id, mock_websocket)
        
        # 发送文本消息
        await manager.send_text_message(user_id, text)
        
        # 验证消息已发送
        mock_websocket.send_text.assert_called_once_with(text)


class TestGlobalConnectionManager:
    """测试全局连接管理器实例"""
    
    def test_global_instance_exists(self):
        """测试全局实例存在"""
        assert connection_manager is not None
        assert isinstance(connection_manager, ConnectionManager)
    
    @pytest.mark.asyncio
    async def test_global_instance_functionality(self):
        """测试全局实例功能"""
        # 创建模拟WebSocket
        ws = Mock(spec=WebSocket)
        ws.accept = AsyncMock()
        ws.send_json = AsyncMock()
        
        user_id = 999  # 使用特殊ID避免与其他测试冲突
        
        try:
            # 使用全局实例
            await connection_manager.connect(user_id, ws)
            assert connection_manager.is_connected(user_id)
        finally:
            # 清理
            connection_manager.disconnect(user_id)


def test_connection_manager_initialization():
    """测试连接管理器初始化"""
    manager = ConnectionManager()
    
    # 验证初始状态
    assert manager.get_connection_count() == 0
    assert len(manager.get_connected_users()) == 0
    assert manager.active_connections == {}
    assert manager.connection_times == {}


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
