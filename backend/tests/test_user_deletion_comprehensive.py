"""
用户账号注销功能综合测试

包含边界条件、异常情况和定时任务的测试。
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.conversation import Conversation
from app.models.knowledge_base import KnowledgeBase
from app.services.user_service import (
    UserService,
    UserNotFoundError,
    PasswordMismatchError,
    DeletionAlreadyRequestedError,
    NoDeletionRequestError,
    DeletionCooldownExpiredError,
)


class TestUserDeletionEdgeCases:
    """边界条件测试"""
    
    def test_request_deletion_with_empty_reason(self, client: TestClient, auth_headers: dict, test_user: User, db: Session):
        """测试空注销原因"""
        response = client.post(
            "/api/v1/user/deletion/request",
            json={"password": "testpassword123", "reason": ""},
            headers=auth_headers
        )
        
        assert response.status_code == 200
        db.refresh(test_user)
        assert test_user.deletion_reason == ""
    
    def test_request_deletion_with_long_reason(self, client: TestClient, auth_headers: dict, test_user: User, db: Session):
        """测试长注销原因（接近500字符限制）"""
        long_reason = "测试原因" * 100  # 400字符
        response = client.post(
            "/api/v1/user/deletion/request",
            json={"password": "testpassword123", "reason": long_reason},
            headers=auth_headers
        )
        
        assert response.status_code == 200
        db.refresh(test_user)
        assert test_user.deletion_reason == long_reason
    
    def test_request_deletion_reason_exceeds_limit(self, client: TestClient, auth_headers: dict, test_user: User):
        """测试注销原因超过500字符限制"""
        too_long_reason = "a" * 501
        response = client.post(
            "/api/v1/user/deletion/request",
            json={"password": "testpassword123", "reason": too_long_reason},
            headers=auth_headers
        )
        
        # 应该返回验证错误
        assert response.status_code == 422
    
    def test_deletion_status_at_exact_cooldown_boundary(self, db: Session, test_user: User):
        """测试恰好在冷静期边界的状态"""
        service = UserService(db)
        
        # 设置恰好在冷静期结束时刻
        now = datetime.utcnow()
        test_user.deletion_requested_at = now - timedelta(days=7)
        test_user.deletion_scheduled_at = now  # 恰好现在
        db.commit()
        
        result = service.get_deletion_status(test_user.id)
        
        # 恰好到期时应该不能取消
        assert result["has_deletion_request"] is True
        assert result["can_cancel"] is False
    
    def test_cancel_deletion_one_second_before_expiry(self, db: Session, test_user: User):
        """测试在到期前1秒取消"""
        service = UserService(db)
        
        # 设置在1秒后到期
        now = datetime.utcnow()
        test_user.deletion_requested_at = now - timedelta(days=7)
        test_user.deletion_scheduled_at = now + timedelta(seconds=1)
        db.commit()
        
        result = service.cancel_deletion(test_user.id)
        
        assert result["success"] is True
        db.refresh(test_user)
        assert test_user.deletion_requested_at is None


class TestUserDeletionWithRelatedData:
    """测试删除用户时关联数据的处理"""
    
    def test_execute_deletion_with_conversations(self, db: Session, test_user: User):
        """测试删除有对话记录的用户"""
        # 创建对话
        conversation = Conversation(
            user_id=test_user.id,
            title="测试对话"
        )
        db.add(conversation)
        db.commit()
        
        user_id = test_user.id
        conv_id = conversation.id
        
        service = UserService(db)
        result = service.execute_deletion(user_id)
        
        assert result["success"] is True
        
        # 验证对话也被删除
        deleted_conv = db.query(Conversation).filter(Conversation.id == conv_id).first()
        assert deleted_conv is None
    
    def test_execute_deletion_with_knowledge_bases(self, db: Session, test_user: User):
        """测试删除有知识库的用户"""
        # 创建知识库
        kb = KnowledgeBase(
            user_id=test_user.id,
            name="测试知识库",
            description="测试描述"
        )
        db.add(kb)
        db.commit()
        
        user_id = test_user.id
        kb_id = kb.id
        
        service = UserService(db)
        result = service.execute_deletion(user_id)
        
        assert result["success"] is True
        
        # 验证知识库也被删除
        deleted_kb = db.query(KnowledgeBase).filter(KnowledgeBase.id == kb_id).first()
        assert deleted_kb is None
    
    def test_execute_deletion_nonexistent_user(self, db: Session):
        """测试删除不存在的用户"""
        service = UserService(db)
        result = service.execute_deletion(99999)
        
        assert result["success"] is False
        assert "不存在" in result["message"]


class TestProcessAccountDeletionsTask:
    """定时任务测试 - 使用mock避免真实数据库连接"""
    
    def test_process_no_pending_deletions(self, db: Session):
        """测试没有待处理的删除请求"""
        from app.tasks.cleanup_tasks import process_account_deletions
        from unittest.mock import patch
        
        # Mock SessionLocal 返回测试数据库会话
        with patch('app.tasks.cleanup_tasks.SessionLocal', return_value=db):
            result = process_account_deletions()
        
            assert result["success"] is True
            assert result["processed_count"] == 0
            assert result["deleted_count"] == 0
    
    def test_process_expired_deletion_request(self, db: Session, test_user: User):
        """测试处理已过期的删除请求"""
        from app.tasks.cleanup_tasks import process_account_deletions
        from unittest.mock import patch
        
        # 设置已过期的删除请求
        test_user.deletion_requested_at = datetime.utcnow() - timedelta(days=8)
        test_user.deletion_scheduled_at = datetime.utcnow() - timedelta(days=1)
        db.commit()
        
        user_id = test_user.id
        
        # Mock SessionLocal 返回测试数据库会话
        with patch('app.tasks.cleanup_tasks.SessionLocal', return_value=db):
            result = process_account_deletions()
        
            assert result["processed_count"] == 1
            assert result["deleted_count"] == 1
        
            # 验证用户已被删除
            deleted_user = db.query(User).filter(User.id == user_id).first()
            assert deleted_user is None
    
    def test_process_not_yet_expired_request(self, db: Session, test_user: User):
        """测试不处理未过期的删除请求"""
        from app.tasks.cleanup_tasks import process_account_deletions
        from unittest.mock import patch
        
        # 设置未过期的删除请求
        test_user.deletion_requested_at = datetime.utcnow()
        test_user.deletion_scheduled_at = datetime.utcnow() + timedelta(days=7)
        db.commit()
        
        user_id = test_user.id
        
        # Mock SessionLocal 返回测试数据库会话
        with patch('app.tasks.cleanup_tasks.SessionLocal', return_value=db):
            result = process_account_deletions()
        
            assert result["processed_count"] == 0
        
            # 验证用户未被删除
            user = db.query(User).filter(User.id == user_id).first()
            assert user is not None


class TestUserDeletionServiceExceptions:
    """服务层异常测试"""
    
    def test_request_deletion_user_not_found(self, db: Session):
        """测试请求注销不存在的用户"""
        service = UserService(db)
        
        with pytest.raises(UserNotFoundError):
            service.request_deletion(99999, "password123")
    
    def test_cancel_deletion_user_not_found(self, db: Session):
        """测试取消注销不存在的用户"""
        service = UserService(db)
        
        with pytest.raises(UserNotFoundError):
            service.cancel_deletion(99999)
    
    def test_get_deletion_status_user_not_found(self, db: Session):
        """测试查询不存在用户的注销状态"""
        service = UserService(db)
        
        with pytest.raises(UserNotFoundError):
            service.get_deletion_status(99999)
    
    def test_request_deletion_password_mismatch(self, db: Session, test_user: User):
        """测试密码错误"""
        service = UserService(db)
        
        with pytest.raises(PasswordMismatchError):
            service.request_deletion(test_user.id, "wrongpassword")
    
    def test_request_deletion_already_requested(self, db: Session, test_user: User):
        """测试重复请求注销"""
        test_user.deletion_requested_at = datetime.utcnow()
        test_user.deletion_scheduled_at = datetime.utcnow() + timedelta(days=7)
        db.commit()
        
        service = UserService(db)
        
        with pytest.raises(DeletionAlreadyRequestedError):
            service.request_deletion(test_user.id, "testpassword123")
    
    def test_cancel_deletion_no_request(self, db: Session, test_user: User):
        """测试取消不存在的注销请求"""
        service = UserService(db)
        
        with pytest.raises(NoDeletionRequestError):
            service.cancel_deletion(test_user.id)
    
    def test_cancel_deletion_cooldown_expired(self, db: Session, test_user: User):
        """测试冷静期已过无法取消"""
        test_user.deletion_requested_at = datetime.utcnow() - timedelta(days=8)
        test_user.deletion_scheduled_at = datetime.utcnow() - timedelta(days=1)
        db.commit()
        
        service = UserService(db)
        
        with pytest.raises(DeletionCooldownExpiredError):
            service.cancel_deletion(test_user.id)


class TestUserDeletionAPIValidation:
    """API输入验证测试"""
    
    def test_request_deletion_missing_password(self, client: TestClient, auth_headers: dict):
        """测试缺少密码字段"""
        response = client.post(
            "/api/v1/user/deletion/request",
            json={"reason": "测试"},
            headers=auth_headers
        )
        
        assert response.status_code == 422
    
    def test_request_deletion_empty_password(self, client: TestClient, auth_headers: dict):
        """测试空密码"""
        response = client.post(
            "/api/v1/user/deletion/request",
            json={"password": ""},
            headers=auth_headers
        )
        
        assert response.status_code == 422
    
    def test_request_deletion_invalid_json(self, client: TestClient, auth_headers: dict):
        """测试无效JSON"""
        response = client.post(
            "/api/v1/user/deletion/request",
            content="invalid json",
            headers={**auth_headers, "Content-Type": "application/json"}
        )
        
        assert response.status_code == 422


class TestUserProfileWithDeletionStatus:
    """测试用户信息中的注销状态"""
    
    def test_profile_shows_deletion_status(self, client: TestClient, auth_headers: dict, test_user: User, db: Session):
        """测试用户信息包含注销状态"""
        # 设置注销请求
        now = datetime.utcnow()
        test_user.deletion_requested_at = now
        test_user.deletion_scheduled_at = now + timedelta(days=7)
        db.commit()
        
        response = client.get("/api/v1/user/profile", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "deletion_requested_at" in data
        assert "deletion_scheduled_at" in data
        assert data["deletion_requested_at"] is not None
