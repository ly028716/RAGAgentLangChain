"""
文件存储服务

提供头像上传、存储和管理功能。
"""

import logging
import secrets
from pathlib import Path
from datetime import datetime
from typing import Optional, Tuple, Set
from io import BytesIO

from fastapi import UploadFile, HTTPException, status

from app.config import settings

logger = logging.getLogger(__name__)


class FileService:
    """文件存储服务"""
    
    # 允许的图片类型
    ALLOWED_IMAGE_TYPES: Set[str] = {'image/jpeg', 'image/png', 'image/gif', 'image/webp'}
    ALLOWED_EXTENSIONS: Set[str] = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}
    
    # 文件大小限制
    MAX_AVATAR_SIZE = 2 * 1024 * 1024  # 2MB
    
    # 图片魔数（文件头）
    IMAGE_MAGIC_NUMBERS = {
        b'\xff\xd8\xff': 'jpeg',
        b'\x89PNG': 'png',
        b'GIF8': 'gif',
        b'RIFF': 'webp',
    }
    
    def __init__(self, upload_dir: Optional[str] = None):
        self.upload_dir = Path(upload_dir or settings.file_storage.upload_dir)
        self.avatar_dir = self.upload_dir / "avatars"
        self._ensure_directories()
    
    def _ensure_directories(self):
        """确保目录存在"""
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self.avatar_dir.mkdir(parents=True, exist_ok=True)
    
    def _validate_image_content(self, content: bytes) -> bool:
        """验证图片文件头，防止伪装文件"""
        for magic, _ in self.IMAGE_MAGIC_NUMBERS.items():
            if content.startswith(magic):
                return True
        return False
    
    def _sanitize_filename(self, filename: str) -> str:
        """清理文件名，防止路径遍历攻击"""
        # 移除路径分隔符
        filename = filename.replace('/', '').replace('\\', '')
        # 只保留安全字符
        safe_chars = set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._-')
        return ''.join(c for c in filename if c in safe_chars)
    
    def _generate_avatar_filename(self, user_id: int, extension: str) -> str:
        """生成唯一的头像文件名"""
        timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S')
        random_str = secrets.token_hex(4)
        return f"{user_id}_{timestamp}_{random_str}{extension}"
    
    def _get_user_avatar_dir(self, user_id: int) -> Path:
        """获取用户头像目录"""
        user_dir = self.avatar_dir / str(user_id)
        user_dir.mkdir(parents=True, exist_ok=True)
        return user_dir
    
    async def validate_avatar(self, file: UploadFile) -> Tuple[bytes, str]:
        """
        验证头像文件
        
        Returns:
            (文件内容, 扩展名)
        """
        # 检查文件名
        if not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="文件名不能为空"
            )
        
        # 检查扩展名
        extension = Path(file.filename).suffix.lower()
        if extension not in self.ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"不支持的文件格式，允许: {', '.join(self.ALLOWED_EXTENSIONS)}"
            )
        
        # 检查Content-Type
        if file.content_type not in self.ALLOWED_IMAGE_TYPES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="不支持的图片类型"
            )
        
        # 读取文件内容
        content = await file.read()
        
        # 检查文件大小
        if len(content) > self.MAX_AVATAR_SIZE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"文件大小超过限制（最大{self.MAX_AVATAR_SIZE // 1024 // 1024}MB）"
            )
        
        # 验证文件内容（魔数检查）
        if not self._validate_image_content(content):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="文件内容无效，请上传真实的图片文件"
            )
        
        return content, extension
    
    async def save_avatar(self, user_id: int, file: UploadFile) -> dict:
        """
        保存用户头像
        
        Args:
            user_id: 用户ID
            file: 上传的文件
            
        Returns:
            包含头像URL的字典
        """
        # 验证文件
        content, extension = await self.validate_avatar(file)
        
        # 生成文件名
        filename = self._generate_avatar_filename(user_id, extension)
        
        # 获取用户头像目录
        user_dir = self._get_user_avatar_dir(user_id)
        
        # 删除旧头像
        self._delete_user_avatars(user_id)
        
        # 保存文件
        file_path = user_dir / filename
        try:
            with open(file_path, 'wb') as f:
                f.write(content)
            
            logger.info(f"头像保存成功: user_id={user_id}, file={filename}")
            
            # 生成URL
            avatar_url = f"/uploads/avatars/{user_id}/{filename}"
            
            return {
                "avatar_url": avatar_url,
                "thumbnail_url": avatar_url,  # 简化实现，暂不生成缩略图
                "filename": filename
            }
        except Exception as e:
            logger.error(f"保存头像失败: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="保存头像失败"
            )
    
    def _delete_user_avatars(self, user_id: int):
        """删除用户的所有头像文件"""
        user_dir = self.avatar_dir / str(user_id)
        if user_dir.exists():
            for file in user_dir.iterdir():
                if file.is_file():
                    try:
                        file.unlink()
                    except Exception as e:
                        logger.warning(f"删除旧头像失败: {e}")
    
    def delete_avatar(self, user_id: int) -> bool:
        """
        删除用户头像
        
        Args:
            user_id: 用户ID
            
        Returns:
            是否删除成功
        """
        try:
            self._delete_user_avatars(user_id)
            logger.info(f"头像删除成功: user_id={user_id}")
            return True
        except Exception as e:
            logger.error(f"删除头像失败: {e}")
            return False
    
    def get_avatar_path(self, user_id: int) -> Optional[Path]:
        """获取用户头像文件路径"""
        user_dir = self.avatar_dir / str(user_id)
        if not user_dir.exists():
            return None
        
        for file in user_dir.iterdir():
            if file.is_file() and file.suffix.lower() in self.ALLOWED_EXTENSIONS:
                return file
        
        return None


# 创建全局实例
file_service = FileService()


__all__ = ['FileService', 'file_service']
