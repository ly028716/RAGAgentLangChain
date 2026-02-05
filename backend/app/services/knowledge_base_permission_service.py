"""
知识库权限服务

提供知识库权限的管理功能。
"""

import logging
from typing import List, Optional, Tuple

from sqlalchemy import and_
from sqlalchemy.orm import Session

from app.models.knowledge_base import KnowledgeBase
from app.models.knowledge_base_permission import (KnowledgeBasePermission,
                                                  PermissionType)
from app.models.user import User
from app.schemas.knowledge_base_permission import (PermissionCreate,
                                                   PermissionUpdate)

logger = logging.getLogger(__name__)


# 权限等级映射
PERMISSION_LEVELS = {
    PermissionType.VIEWER.value: 1,
    PermissionType.EDITOR.value: 2,
    PermissionType.OWNER.value: 3,
}


class KnowledgeBasePermissionService:
    """知识库权限服务"""

    def __init__(self, db: Session):
        self.db = db

    def check_permission(
        self,
        kb_id: int,
        user_id: int,
        required_permission: str = PermissionType.VIEWER.value,
    ) -> Tuple[bool, Optional[KnowledgeBase]]:
        """
        检查用户对知识库的权限

        Args:
            kb_id: 知识库ID
            user_id: 用户ID
            required_permission: 所需权限级别

        Returns:
            (是否有权限, 知识库对象)
        """
        kb = self.db.query(KnowledgeBase).filter(KnowledgeBase.id == kb_id).first()
        if not kb:
            return False, None

        # 检查是否为超级管理员
        user = self.db.query(User).filter(User.id == user_id).first()
        if user and user.is_admin:
            return True, kb

        # 所有者拥有所有权限
        if kb.user_id == user_id:
            return True, kb

        # 检查公开知识库（仅查看权限）
        if hasattr(kb, "visibility") and kb.visibility == "public":
            if required_permission == PermissionType.VIEWER.value:
                return True, kb

        # 检查用户权限
        permission = (
            self.db.query(KnowledgeBasePermission)
            .filter(
                KnowledgeBasePermission.knowledge_base_id == kb_id,
                KnowledgeBasePermission.user_id == user_id,
            )
            .first()
        )

        if not permission:
            return False, kb

        # 权限等级检查
        user_level = PERMISSION_LEVELS.get(permission.permission_type, 0)
        required_level = PERMISSION_LEVELS.get(required_permission, 0)

        return user_level >= required_level, kb

    def check_permissions_batch(
        self,
        kb_ids: List[int],
        user_id: int,
        required_permission: str = PermissionType.VIEWER.value,
    ) -> Tuple[bool, List[int]]:
        """
        批量检查用户对知识库的权限

        Args:
            kb_ids: 知识库ID列表
            user_id: 用户ID
            required_permission: 所需权限级别

        Returns:
            (是否全部有权限, 无权限的知识库ID列表)
        """
        if not kb_ids:
            return True, []

        # 检查是否为超级管理员
        user = self.db.query(User).filter(User.id == user_id).first()
        if user and user.is_admin:
            return True, []

        # 查询所有涉及的知识库
        kbs = self.db.query(KnowledgeBase).filter(KnowledgeBase.id.in_(kb_ids)).all()
        kb_map = {kb.id: kb for kb in kbs}

        # 检查不存在的知识库
        found_ids = set(kb_map.keys())
        missing_ids = [kb_id for kb_id in kb_ids if kb_id not in found_ids]
        if missing_ids:
            return False, missing_ids

        # 查询用户的权限记录
        permissions = (
            self.db.query(KnowledgeBasePermission)
            .filter(
                KnowledgeBasePermission.knowledge_base_id.in_(kb_ids),
                KnowledgeBasePermission.user_id == user_id,
            )
            .all()
        )
        perm_map = {p.knowledge_base_id: p for p in permissions}

        required_level = PERMISSION_LEVELS.get(required_permission, 0)
        failed_ids = []

        for kb_id in kb_ids:
            kb = kb_map[kb_id]
            
            # 1. 所有者拥有所有权限
            if kb.user_id == user_id:
                continue
                
            # 2. 公开知识库（仅查看权限）
            if (
                hasattr(kb, "visibility") 
                and kb.visibility == "public" 
                and required_permission == PermissionType.VIEWER.value
            ):
                continue

            # 3. 检查权限记录
            permission = perm_map.get(kb_id)
            if not permission:
                failed_ids.append(kb_id)
                continue

            user_level = PERMISSION_LEVELS.get(permission.permission_type, 0)
            if user_level < required_level:
                failed_ids.append(kb_id)

        return len(failed_ids) == 0, failed_ids

    def get_permissions(self, kb_id: int, user_id: int) -> Tuple[List[dict], int]:
        """
        获取知识库的权限列表

        Args:
            kb_id: 知识库ID
            user_id: 当前用户ID（用于权限检查）

        Returns:
            (权限列表, 总数)
        """
        # 检查是否有权限查看
        has_permission, kb = self.check_permission(
            kb_id, user_id, PermissionType.OWNER.value
        )
        if not has_permission:
            # 非所有者只能看到自己的权限
            permission = (
                self.db.query(KnowledgeBasePermission)
                .filter(
                    KnowledgeBasePermission.knowledge_base_id == kb_id,
                    KnowledgeBasePermission.user_id == user_id,
                )
                .first()
            )

            if permission:
                user = self.db.query(User).filter(User.id == user_id).first()
                return [
                    {
                        "id": permission.id,
                        "knowledge_base_id": permission.knowledge_base_id,
                        "user_id": permission.user_id,
                        "username": user.username if user else None,
                        "permission_type": permission.permission_type,
                        "is_public": permission.is_public,
                        "created_at": permission.created_at,
                    }
                ], 1
            return [], 0

        # 所有者可以看到所有权限 - 使用JOIN优化查询
        from sqlalchemy.orm import joinedload

        permissions = (
            self.db.query(KnowledgeBasePermission)
            .options(joinedload(KnowledgeBasePermission.user))
            .filter(KnowledgeBasePermission.knowledge_base_id == kb_id)
            .all()
        )

        result = []
        for perm in permissions:
            result.append(
                {
                    "id": perm.id,
                    "knowledge_base_id": perm.knowledge_base_id,
                    "user_id": perm.user_id,
                    "username": perm.user.username if perm.user else None,
                    "permission_type": perm.permission_type,
                    "is_public": perm.is_public,
                    "created_at": perm.created_at,
                }
            )

        return result, len(result)

    def add_permission(
        self, kb_id: int, owner_id: int, data: PermissionCreate
    ) -> Optional[KnowledgeBasePermission]:
        """
        添加权限

        Args:
            kb_id: 知识库ID
            owner_id: 所有者ID
            data: 权限数据

        Returns:
            创建的权限对象或None
        """
        # 检查是否为所有者
        kb = (
            self.db.query(KnowledgeBase)
            .filter(KnowledgeBase.id == kb_id, KnowledgeBase.user_id == owner_id)
            .first()
        )

        if not kb:
            return None

        # 不能给自己添加权限
        if data.user_id == owner_id:
            return None

        # 检查用户是否存在
        if data.user_id:
            user = self.db.query(User).filter(User.id == data.user_id).first()
            if not user:
                return None

        # 检查是否已存在权限
        existing = (
            self.db.query(KnowledgeBasePermission)
            .filter(
                KnowledgeBasePermission.knowledge_base_id == kb_id,
                KnowledgeBasePermission.user_id == data.user_id,
            )
            .first()
        )

        if existing:
            # 更新现有权限
            existing.permission_type = data.permission_type
            self.db.commit()
            self.db.refresh(existing)
            return existing

        # 创建新权限
        permission = KnowledgeBasePermission(
            knowledge_base_id=kb_id,
            user_id=data.user_id,
            permission_type=data.permission_type,
            is_public=data.user_id is None,
        )

        self.db.add(permission)
        self.db.commit()
        self.db.refresh(permission)

        logger.info(
            f"添加权限成功: kb_id={kb_id}, user_id={data.user_id}, type={data.permission_type}"
        )
        return permission

    def update_permission(
        self, kb_id: int, permission_id: int, owner_id: int, data: PermissionUpdate
    ) -> Optional[KnowledgeBasePermission]:
        """
        更新权限

        Args:
            kb_id: 知识库ID
            permission_id: 权限ID
            owner_id: 所有者ID
            data: 更新数据

        Returns:
            更新后的权限对象或None
        """
        # 检查是否为所有者
        kb = (
            self.db.query(KnowledgeBase)
            .filter(KnowledgeBase.id == kb_id, KnowledgeBase.user_id == owner_id)
            .first()
        )

        if not kb:
            return None

        permission = (
            self.db.query(KnowledgeBasePermission)
            .filter(
                KnowledgeBasePermission.id == permission_id,
                KnowledgeBasePermission.knowledge_base_id == kb_id,
            )
            .first()
        )

        if not permission:
            return None

        permission.permission_type = data.permission_type
        self.db.commit()
        self.db.refresh(permission)

        logger.info(
            f"更新权限成功: permission_id={permission_id}, type={data.permission_type}"
        )
        return permission

    def delete_permission(self, kb_id: int, permission_id: int, owner_id: int) -> bool:
        """
        删除权限

        Args:
            kb_id: 知识库ID
            permission_id: 权限ID
            owner_id: 所有者ID

        Returns:
            是否删除成功
        """
        # 检查是否为所有者
        kb = (
            self.db.query(KnowledgeBase)
            .filter(KnowledgeBase.id == kb_id, KnowledgeBase.user_id == owner_id)
            .first()
        )

        if not kb:
            return False

        permission = (
            self.db.query(KnowledgeBasePermission)
            .filter(
                KnowledgeBasePermission.id == permission_id,
                KnowledgeBasePermission.knowledge_base_id == kb_id,
            )
            .first()
        )

        if not permission:
            return False

        self.db.delete(permission)
        self.db.commit()

        logger.info(f"删除权限成功: permission_id={permission_id}")
        return True

    def share_by_username(
        self,
        kb_id: int,
        owner_id: int,
        username: str,
        permission_type: str = PermissionType.VIEWER.value,
    ) -> Optional[KnowledgeBasePermission]:
        """
        通过用户名分享知识库

        Args:
            kb_id: 知识库ID
            owner_id: 所有者ID
            username: 目标用户名
            permission_type: 权限类型

        Returns:
            创建的权限对象或None
        """
        # 查找用户
        user = self.db.query(User).filter(User.username == username).first()
        if not user:
            return None

        # 使用add_permission添加权限
        data = PermissionCreate(user_id=user.id, permission_type=permission_type)
        return self.add_permission(kb_id, owner_id, data)

    def get_shared_knowledge_bases(
        self, user_id: int, skip: int = 0, limit: int = 20
    ) -> Tuple[List[KnowledgeBase], int]:
        """
        获取分享给用户的知识库列表

        Args:
            user_id: 用户ID
            skip: 跳过数量
            limit: 返回数量

        Returns:
            (知识库列表, 总数)
        """
        # 查询用户有权限的知识库（非自己创建的）
        query = (
            self.db.query(KnowledgeBase)
            .join(
                KnowledgeBasePermission,
                KnowledgeBase.id == KnowledgeBasePermission.knowledge_base_id,
            )
            .filter(
                KnowledgeBasePermission.user_id == user_id,
                KnowledgeBase.user_id != user_id,  # 排除自己创建的
            )
        )

        total = query.count()
        knowledge_bases = query.offset(skip).limit(limit).all()

        return knowledge_bases, total


__all__ = ["KnowledgeBasePermissionService", "PERMISSION_LEVELS"]
