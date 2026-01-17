"""
用户账号注销API测试

测试账号注销相关的API端点。
"""

import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.user import User
from app.services.user_service import UserService


class TestUserDeletionAPI:
    """用户账号注销API测试类"""
    
    def test_request_deletion_success(self, client: TestClient, auth_headers: dict, test_user: User, db: Session):
        """测试成功请求注销账号"""
        response = client.post(
            "/api/v1/user/deletion/request",
            json={"password": "testpassword123", "reason": "测试注销"},
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["cooldown_days"] == 7
        assert "requested_at" in data
        assert "scheduled_at" in data
        
        # 验证数据库中的用户状态
        db.refresh(test_user)
        assert test_user.deletion_requested_at is not None
        assert test_user.deletion_scheduled_at is not None
        assert test_user.deletion_reason == "测试注销"
    
    def test_request_deletion_wrong_password(self, client: TestClient, auth_headers: dict, test_user: User):
        """测试密码错误时请求注销"""
        response = client.post(
            "/api/v1/user/deletion/request",
            json={"password": "wrongpassword"},
            headers=auth_headers
        )
        
        assert response.status_code == 400
        data = response.json()
        # 检查响应中包含错误信息
        assert "密码" in str(data) or "password" in str(data).lower()
    
    def test_request_deletion_already_requested(self, client: TestClient, auth_headers: dict, test_user: User, db: Session):
        """测试重复请求注销"""
        # 先设置用户已请求注销
        test_user.deletion_requested_at = datetime.utcnow()
        test_user.deletion_scheduled_at = datetime.utcnow() + timedelta(days=7)
        db.commit()
        
        response = client.post(
            "/api/v1/user/deletion/request",
            json={"password": "testpassword123"},
            headers=auth_headers
        )
        
        assert response.status_code == 400
    
    def test_cancel_deletion_success(self, client: TestClient, auth_headers: dict, test_user: User, db: Session):
        """测试成功取消注销请求"""
        # 先设置用户已请求注销
        test_user.deletion_requested_at = datetime.utcnow()
        test_user.deletion_scheduled_at = datetime.utcnow() + timedelta(days=7)
        test_user.deletion_reason = "测试"
        db.commit()
        
        response = client.post(
            "/api/v1/user/deletion/cancel",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        
        # 验证数据库中的用户状态
        db.refresh(test_user)
        assert test_user.deletion_requested_at is None
        assert test_user.deletion_scheduled_at is None
        assert test_user.deletion_reason is None
    
    def test_cancel_deletion_no_request(self, client: TestClient, auth_headers: dict, test_user: User):
        """测试没有注销请求时取消"""
        response = client.post(
            "/api/v1/user/deletion/cancel",
            headers=auth_headers
        )
        
        assert response.status_code == 400
    
    def test_cancel_deletion_cooldown_expired(self, client: TestClient, auth_headers: dict, test_user: User, db: Session):
        """测试冷静期已过时取消"""
        # 设置用户注销请求已过期
        test_user.deletion_requested_at = datetime.utcnow() - timedelta(days=8)
        test_user.deletion_scheduled_at = datetime.utcnow() - timedelta(days=1)
        db.commit()
        
        response = client.post(
            "/api/v1/user/deletion/cancel",
            headers=auth_headers
        )
        
        assert response.status_code == 400
    
    def test_get_deletion_status_no_request(self, client: TestClient, auth_headers: dict, test_user: User):
        """测试查询注销状态（无注销请求）"""
        response = client.get(
            "/api/v1/user/deletion/status",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["has_deletion_request"] is False
    
    def test_get_deletion_status_with_request(self, client: TestClient, auth_headers: dict, test_user: User, db: Session):
        """测试查询注销状态（有注销请求）"""
        # 设置用户已请求注销
        now = datetime.utcnow()
        test_user.deletion_requested_at = now
        test_user.deletion_scheduled_at = now + timedelta(days=5, hours=12)
        test_user.deletion_reason = "测试注销"
        db.commit()
        
        response = client.get(
            "/api/v1/user/deletion/status",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["has_deletion_request"] is True
        assert data["reason"] == "测试注销"
        assert data["can_cancel"] is True
        assert data["remaining_days"] >= 4  # 至少4天
    
    def test_request_deletion_unauthorized(self, client: TestClient):
        """测试未授权时请求注销"""
        response = client.post(
            "/api/v1/user/deletion/request",
            json={"password": "testpassword123"}
        )
        
        assert response.status_code == 401


class TestUserDeletionService:
    """用户注销服务测试类"""
    
    def test_request_deletion_sets_correct_dates(self, db: Session, test_user: User):
        """测试请求注销时设置正确的日期"""
        service = UserService(db)
        result = service.request_deletion(test_user.id, "testpassword123", "测试原因")
        
        assert result["success"] is True
        assert result["cooldown_days"] == 7
        
        db.refresh(test_user)
        assert test_user.deletion_requested_at is not None
        assert test_user.deletion_scheduled_at is not None
        assert test_user.deletion_reason == "测试原因"
        
        # 验证计划删除时间约为7天后
        time_diff = test_user.deletion_scheduled_at - test_user.deletion_requested_at
        assert 6 <= time_diff.days <= 7
    
    def test_cancel_deletion_clears_dates(self, db: Session, test_user: User):
        """测试取消注销时清除日期"""
        # 先设置注销请求
        test_user.deletion_requested_at = datetime.utcnow()
        test_user.deletion_scheduled_at = datetime.utcnow() + timedelta(days=7)
        test_user.deletion_reason = "测试"
        db.commit()
        
        service = UserService(db)
        result = service.cancel_deletion(test_user.id)
        
        assert result["success"] is True
        
        db.refresh(test_user)
        assert test_user.deletion_requested_at is None
        assert test_user.deletion_scheduled_at is None
        assert test_user.deletion_reason is None
    
    def test_get_deletion_status_calculates_remaining_time(self, db: Session, test_user: User):
        """测试获取注销状态时正确计算剩余时间"""
        # 设置注销请求
        now = datetime.utcnow()
        test_user.deletion_requested_at = now
        test_user.deletion_scheduled_at = now + timedelta(days=3, hours=12)
        db.commit()
        
        service = UserService(db)
        result = service.get_deletion_status(test_user.id)
        
        assert result["has_deletion_request"] is True
        assert result["remaining_days"] == 3
        assert result["can_cancel"] is True
    
    def test_execute_deletion_removes_user(self, db: Session, test_user: User):
        """测试执行删除时移除用户"""
        user_id = test_user.id
        
        service = UserService(db)
        result = service.execute_deletion(user_id)
        
        assert result["success"] is True
        
        # 验证用户已被删除
        deleted_user = db.query(User).filter(User.id == user_id).first()
        assert deleted_user is None
