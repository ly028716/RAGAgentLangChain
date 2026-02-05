"""
知识库权限API测试
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.knowledge_base import KnowledgeBase
from app.models.knowledge_base_permission import KnowledgeBasePermission
from app.models.user import User


class TestKnowledgeBasePermissionsAPI:
    """知识库权限API测试类"""
    
    @pytest.fixture
    def test_kb(self, db: Session, test_user: User) -> KnowledgeBase:
        """创建测试知识库"""
        kb = KnowledgeBase(
            user_id=test_user.id,
            name="测试知识库",
            description="测试描述"
        )
        db.add(kb)
        db.commit()
        db.refresh(kb)
        return kb
    
    def test_get_permissions(self, client: TestClient, auth_headers: dict, test_kb: KnowledgeBase):
        """测试获取权限列表"""
        response = client.get(f"/api/v1/knowledge-bases/{test_kb.id}/permissions", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
    
    def test_add_permission(self, client: TestClient, auth_headers: dict, test_kb: KnowledgeBase, other_user: User):
        """测试添加权限"""
        permission_data = {
            "user_id": other_user.id,
            "permission_type": "viewer"
        }
        response = client.post(
            f"/api/v1/knowledge-bases/{test_kb.id}/permissions",
            json=permission_data,
            headers=auth_headers
        )
        assert response.status_code == 201
        data = response.json()
        assert data["user_id"] == other_user.id
        assert data["permission_type"] == "viewer"
    
    def test_update_permission(self, client: TestClient, auth_headers: dict, test_kb: KnowledgeBase, other_user: User, db: Session):
        """测试更新权限"""
        # 先添加权限
        permission = KnowledgeBasePermission(
            knowledge_base_id=test_kb.id,
            user_id=other_user.id,
            permission_type="viewer"
        )
        db.add(permission)
        db.commit()
        db.refresh(permission)
        
        update_data = {"permission_type": "editor"}
        response = client.put(
            f"/api/v1/knowledge-bases/{test_kb.id}/permissions/{permission.id}",
            json=update_data,
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["permission_type"] == "editor"
    
    def test_delete_permission(self, client: TestClient, auth_headers: dict, test_kb: KnowledgeBase, other_user: User, db: Session):
        """测试删除权限"""
        # 先添加权限
        permission = KnowledgeBasePermission(
            knowledge_base_id=test_kb.id,
            user_id=other_user.id,
            permission_type="viewer"
        )
        db.add(permission)
        db.commit()
        db.refresh(permission)
        
        response = client.delete(
            f"/api/v1/knowledge-bases/{test_kb.id}/permissions/{permission.id}",
            headers=auth_headers
        )
        assert response.status_code == 204
    
    def test_share_by_username(self, client: TestClient, auth_headers: dict, test_kb: KnowledgeBase, other_user: User):
        """测试通过用户名分享"""
        share_data = {
            "username": other_user.username,
            "permission_type": "viewer"
        }
        response = client.post(
            f"/api/v1/knowledge-bases/{test_kb.id}/share",
            json=share_data,
            headers=auth_headers
        )
        assert response.status_code == 201
        data = response.json()
        assert data["username"] == other_user.username
    
    def test_share_nonexistent_user(self, client: TestClient, auth_headers: dict, test_kb: KnowledgeBase):
        """测试分享给不存在的用户"""
        share_data = {
            "username": "nonexistent_user",
            "permission_type": "viewer"
        }
        response = client.post(
            f"/api/v1/knowledge-bases/{test_kb.id}/share",
            json=share_data,
            headers=auth_headers
        )
        assert response.status_code == 400
    
    def test_non_owner_cannot_add_permission(self, client: TestClient, test_kb: KnowledgeBase, other_user: User, db: Session):
        """测试非所有者不能添加权限"""
        # 使用其他用户的token
        from app.core.security import create_access_token
        other_token = create_access_token(subject=other_user.id, username=other_user.username)
        other_headers = {"Authorization": f"Bearer {other_token}"}
        
        permission_data = {
            "user_id": 999,
            "permission_type": "viewer"
        }
        response = client.post(
            f"/api/v1/knowledge-bases/{test_kb.id}/permissions",
            json=permission_data,
            headers=other_headers
        )
        assert response.status_code == 403
