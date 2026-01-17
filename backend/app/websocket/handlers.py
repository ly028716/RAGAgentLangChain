"""
WebSocket处理器

处理WebSocket连接、消息和心跳。
"""
from fastapi import WebSocket, WebSocketDisconnect, Depends, Query, status
from fastapi.responses import JSONResponse
from jose import JWTError, jwt
from typing import Optional
import logging
import asyncio
import json
from datetime import datetime

from app.websocket.connection_manager import connection_manager
from app.core.security import SECRET_KEY, ALGORITHM
from app.dependencies import get_current_user_from_token

logger = logging.getLogger(__name__)

# WebSocket心跳间隔（秒）
HEARTBEAT_INTERVAL = 30


async def verify_websocket_token(token: str) -> Optional[int]:
    """
    验证WebSocket连接的JWT令牌
    
    Args:
        token: JWT令牌
        
    Returns:
        int: 用户ID，如果验证失败返回None
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("sub")
        if user_id is None:
            return None
        return int(user_id)
    except JWTError as e:
        logger.warning(f"JWT验证失败: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"令牌验证异常: {str(e)}")
        return None


async def handle_websocket_message(user_id: int, message: dict):
    """
    处理客户端发送的WebSocket消息
    
    Args:
        user_id: 用户ID
        message: 消息内容
    """
    message_type = message.get("type")
    
    if message_type == "ping":
        # 心跳响应
        await connection_manager.send_personal_message(user_id, {
            "type": "pong",
            "data": {
                "timestamp": datetime.utcnow().isoformat()
            }
        })
    
    elif message_type == "subscribe":
        # 订阅特定事件（预留功能）
        channels = message.get("data", {}).get("channels", [])
        logger.info(f"用户订阅频道 user_id={user_id}, channels={channels}")
        await connection_manager.send_personal_message(user_id, {
            "type": "subscribed",
            "data": {
                "channels": channels,
                "message": "订阅成功"
            }
        })
    
    elif message_type == "unsubscribe":
        # 取消订阅（预留功能）
        channels = message.get("data", {}).get("channels", [])
        logger.info(f"用户取消订阅 user_id={user_id}, channels={channels}")
        await connection_manager.send_personal_message(user_id, {
            "type": "unsubscribed",
            "data": {
                "channels": channels,
                "message": "取消订阅成功"
            }
        })
    
    else:
        logger.warning(f"未知消息类型 user_id={user_id}, type={message_type}")
        await connection_manager.send_personal_message(user_id, {
            "type": "error",
            "data": {
                "message": f"未知消息类型: {message_type}"
            }
        })


async def send_heartbeat(user_id: int):
    """
    发送心跳消息
    
    Args:
        user_id: 用户ID
    """
    while connection_manager.is_connected(user_id):
        try:
            await connection_manager.send_personal_message(user_id, {
                "type": "heartbeat",
                "data": {
                    "timestamp": datetime.utcnow().isoformat()
                }
            })
            await asyncio.sleep(HEARTBEAT_INTERVAL)
        except Exception as e:
            logger.error(f"心跳发送失败 user_id={user_id}: {str(e)}")
            break


async def websocket_endpoint(
    websocket: WebSocket,
    token: str = Query(..., description="JWT认证令牌")
):
    """
    WebSocket端点处理函数
    
    Args:
        websocket: WebSocket连接对象
        token: JWT认证令牌（从查询参数获取）
    """
    # 验证令牌
    user_id = await verify_websocket_token(token)
    
    if user_id is None:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Invalid token")
        logger.warning("WebSocket连接被拒绝：令牌无效")
        return
    
    # 建立连接
    await connection_manager.connect(user_id, websocket)
    
    # 启动心跳任务
    heartbeat_task = asyncio.create_task(send_heartbeat(user_id))
    
    try:
        while True:
            # 接收消息
            try:
                # 设置超时，避免长时间阻塞
                data = await asyncio.wait_for(websocket.receive_text(), timeout=60.0)
                
                # 解析消息
                try:
                    message = json.loads(data)
                    await handle_websocket_message(user_id, message)
                except json.JSONDecodeError:
                    logger.warning(f"无效的JSON消息 user_id={user_id}")
                    await connection_manager.send_personal_message(user_id, {
                        "type": "error",
                        "data": {
                            "message": "无效的JSON格式"
                        }
                    })
                
            except asyncio.TimeoutError:
                # 超时，继续等待
                continue
            
    except WebSocketDisconnect:
        logger.info(f"WebSocket客户端主动断开 user_id={user_id}")
    except Exception as e:
        logger.error(f"WebSocket异常 user_id={user_id}: {str(e)}")
    finally:
        # 取消心跳任务
        heartbeat_task.cancel()
        try:
            await heartbeat_task
        except asyncio.CancelledError:
            pass
        
        # 断开连接
        connection_manager.disconnect(user_id)


# 用于FastAPI路由注册的函数
def get_websocket_handler():
    """
    获取WebSocket处理器函数
    
    Returns:
        callable: WebSocket处理器
    """
    return websocket_endpoint
