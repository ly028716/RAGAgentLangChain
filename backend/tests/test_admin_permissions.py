"""
管理员权限测试

测试管理员权限验证功能
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.user import User
from app.core.security import hash_password


class TestAdminPermissions:
    """管理员权限测试类"""
    
    @pytest.fixture
    def admin_user(self, db: Session) -> User:
        """创建管理员用户"""
        admin = User(
            username="admin_test",
            email="admin@test.com",
            password_hash=hash_password("Admin123456"),
            is_active=True,
            is_admin=True
        )
        db.add(admin)
        db.commit()
        db.refresh(admin)
        return admin
    
    @pytest.fixture
    def normal_user(self, db: Session) -> User:
        """创建普通用户"""
        user = User(
            username="normal_test",
            email="normal@test.com",
            password_hash=hash_password("User123456"),
            is_active=True,
            is_admin=False
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    
    @pytest.fixture
    def admin_token(self, client: TestClient, admin_user: User) -> str:
        """获取管理员令牌"""
        response = client.post(
            "/api/v1/auth/login",
            json={"username": "admin_test", "password": "Admin123456"}
        )
        assert response.status_code == 200
        return response.json()["access_token"]
    
    @pytest.fixture
    def normal_token(self, client: TestClient, normal_user: User) -> str:
        """获取普通用户令牌"""
        response = client.post(
            "/api/v1/auth/login",
            json={"username": "normal_test", "password": "User123456"}
        )
        assert response.status_code == 200
        return response.json()["access_token"]
    
    # ============ 配额管理权限测试 ============
    
    def test_admin_can_update_quota(
        self, 
        client: TestClient, 
        admin_token: str,
        normal_user: User
    ):
        """测试管理员可以更新配额"""
        response = client.put(
            "/api/v1/quota",
            json={"user_id": normal_user.id, "monthly_quota": 200000},
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["monthly_quota"] == 200000
    
    def test_normal_user_cannot_update_quota(
        self, 
        client: TestClient, 
        normal_token: str,
        normal_user: User
    ):
        """测试普通用户不能更新配额"""
        response = client.put(
            "/api/v1/quota",
            json={"user_id": normal_user.id, "monthly_quota": 200000},
            headers={"Authorization": f"Bearer {normal_token}"}
        )
        assert response.status_code == 403
        assert "管理员权限" in response.json()["detail"]
    
    def test_admin_can_reset_quota(
        self, 
        client: TestClient, 
        admin_token: str,
        normal_user: User
    ):
        """测试管理员可以重置配额"""
        response = client.post(
            f"/api/v1/quota/reset?user_id={normal_user.id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["used_quota"] == 0
    
    def test_normal_user_cannot_reset_quota(
        self, 
        client: TestClient, 
        normal_token: str,
        normal_user: User
    ):
        """测试普通用户不能重置配额"""
        response = client.post(
            f"/api/v1/quota/reset?user_id={normal_user.id}",
            headers={"Authorization": f"Bearer {normal_token}"}
        )
        assert response.status_code == 403
    
    # ============ 系统配置权限测试 ============
    
    def test_admin_can_get_system_config(
        self, 
        client: TestClient, 
        admin_token: str
    ):
        """测试管理员可以获取系统配置"""
        response = client.get(
            "/api/v1/system/config",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "tongyi" in data
    
    def test_normal_user_cannot_get_system_config(
        self, 
        client: TestClient, 
        normal_token: str
    ):
        """测试普通用户不能获取系统配置"""
        response = client.get(
            "/api/v1/system/config",
            headers={"Authorization": f"Bearer {normal_token}"}
        )
        assert response.status_code == 403
    
    def test_admin_can_update_system_config(
        self, 
        client: TestClient, 
        admin_token: str
    ):
        """测试管理员可以更新系统配置"""
        response = client.put(
            "/api/v1/system/config",
            json={
                "tongyi": {
                    "temperature": 0.8,
                    "max_tokens": 2500
                }
            },
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
    
    def test_normal_user_cannot_update_system_config(
        self, 
        client: TestClient, 
        normal_token: str
    ):
        """测试普通用户不能更新系统配置"""
        response = client.put(
            "/api/v1/system/config",
            json={
                "tongyi": {
                    "temperature": 0.8
                }
            },
            headers={"Authorization": f"Bearer {normal_token}"}
        )
        assert response.status_code == 403
    
    # ============ 使用统计权限测试 ============
    
    def test_admin_can_get_all_stats(
        self, 
        client: TestClient, 
        admin_token: str
    ):
        """测试管理员可以获取全局统计"""
        response = client.get(
            "/api/v1/system/stats/all",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
    
    def test_normal_user_cannot_get_all_stats(
        self, 
        client: TestClient, 
        normal_token: str
    ):
        """测试普通用户不能获取全局统计"""
        response = client.get(
            "/api/v1/system/stats/all",
            headers={"Authorization": f"Bearer {normal_token}"}
        )
        assert response.status_code == 403
    
    def test_normal_user_can_get_own_stats(
        self, 
        client: TestClient, 
        normal_token: str,
        normal_user: User
    ):
        """测试普通用户可以获取自己的统计"""
        response = client.get(
            f"/api/v1/system/stats?user_id={normal_user.id}",
            headers={"Authorization": f"Bearer {normal_token}"}
        )
        assert response.status_code == 200
    
    def test_normal_user_cannot_get_others_stats(
        self, 
        client: TestClient, 
        normal_token: str,
        admin_user: User
    ):
        """测试普通用户不能获取其他用户的统计"""
        response = client.get(
            f"/api/v1/system/stats?user_id={admin_user.id}",
            headers={"Authorization": f"Bearer {normal_token}"}
        )
        # 应该返回自己的统计，而不是指定用户的
        assert response.status_code == 200
    
    def test_admin_can_get_specific_user_stats(
        self, 
        client: TestClient, 
        admin_token: str,
        normal_user: User
    ):
        """测试管理员可以获取指定用户的统计"""
        response = client.get(
            f"/api/v1/system/stats?user_id={normal_user.id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
    
    # ============ 用户信息测试 ============
    
    def test_user_profile_includes_is_admin(
        self, 
        client: TestClient, 
        admin_token: str
    ):
        """测试用户信息包含is_admin字段"""
        response = client.get(
            "/api/v1/user/profile",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "is_admin" in data
        assert data["is_admin"] is True
    
    def test_normal_user_is_admin_false(
        self, 
        client: TestClient, 
        normal_token: str
    ):
        """测试普通用户的is_admin为False"""
        response = client.get(
            "/api/v1/user/profile",
            headers={"Authorization": f"Bearer {normal_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["is_admin"] is False
    
    # ============ 无令牌访问测试 ============
    
    def test_admin_endpoints_require_auth(self, client: TestClient):
        """测试管理员端点需要认证"""
        endpoints = [
            "/api/v1/system/config",
            "/api/v1/system/stats/all",
        ]
        
        for endpoint in endpoints:
            response = client.get(endpoint)
            assert response.status_code == 401


class TestAdminDependency:
    """测试管理员依赖函数"""
    
    def test_get_current_admin_user_with_admin(
        self, 
        db: Session
    ):
        """测试管理员用户通过验证"""
        from app.dependencies import get_current_admin_user
        
        admin = User(
            username="admin",
            email="admin@test.com",
            password_hash=hash_password("Admin123"),
            is_admin=True,
            is_active=True
        )
        
        result = get_current_admin_user(admin)
        assert result == admin
    
    def test_get_current_admin_user_with_normal_user(
        self, 
        db: Session
    ):
        """测试普通用户无法通过验证"""
        from app.dependencies import get_current_admin_user
        from fastapi import HTTPException
        
        user = User(
            username="user",
            email="user@test.com",
            password_hash=hash_password("User123"),
            is_admin=False,
            is_active=True
        )
        
        with pytest.raises(HTTPException) as exc_info:
            get_current_admin_user(user)
        
        assert exc_info.value.status_code == 403
        assert "管理员权限" in str(exc_info.value.detail)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
