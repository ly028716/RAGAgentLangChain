"""
验证码服务测试
"""
import pytest
import secrets
from datetime import datetime, timedelta
from unittest.mock import MagicMock, AsyncMock, patch

import sys
sys.path.insert(0, '.')

from app.models.verification_code import VerificationCode
from app.services.verification_service import VerificationService


class TestVerificationService:
    """验证码服务测试类"""
    
    def setup_method(self):
        """测试前置设置"""
        self.mock_db = MagicMock()
        self.service = VerificationService(self.mock_db)
    
    def test_generate_code(self):
        """测试验证码生成"""
        code = self.service._generate_code()
        assert len(code) == 6
        assert code.isdigit()
    
    def test_generate_code_is_random(self):
        """测试验证码随机性"""
        codes = set()
        for _ in range(100):
            codes.add(self.service._generate_code())
        # 100次生成应该有很多不同的值
        assert len(codes) > 50
    
    def test_check_send_rate_limit_no_previous(self):
        """测试发送频率限制 - 无历史记录"""
        self.mock_db.query.return_value.filter.return_value.count.return_value = 0
        self.mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = None
        
        can_send, error_msg = self.service._check_send_rate_limit("test@example.com", "register")
        
        assert can_send is True
        assert error_msg == ""
    
    def test_check_send_rate_limit_exceeded(self):
        """测试发送频率限制 - 超过限制"""
        self.mock_db.query.return_value.filter.return_value.count.return_value = 5
        
        can_send, error_msg = self.service._check_send_rate_limit("test@example.com", "register")
        
        assert can_send is False
        assert "1小时后再试" in error_msg
    
    def test_check_send_rate_limit_too_frequent(self):
        """测试发送频率限制 - 发送过于频繁"""
        self.mock_db.query.return_value.filter.return_value.count.return_value = 1
        
        # 模拟30秒前发送过
        last_code = MagicMock()
        last_code.created_at = datetime.utcnow() - timedelta(seconds=30)
        self.mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = last_code
        
        can_send, error_msg = self.service._check_send_rate_limit("test@example.com", "register")
        
        assert can_send is False
        assert "秒后再试" in error_msg
    
    def test_verify_code_success(self):
        """测试验证码验证 - 成功"""
        mock_code = MagicMock()
        mock_code.code = "123456"
        mock_code.attempts = 0
        mock_code.is_used = False
        
        self.mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = mock_code
        
        result = self.service.verify_code("test@example.com", "123456", "register")
        
        assert result["success"] is True
        assert mock_code.is_used is True
    
    def test_verify_code_wrong_code(self):
        """测试验证码验证 - 验证码错误"""
        mock_code = MagicMock()
        mock_code.code = "123456"
        mock_code.attempts = 0
        mock_code.is_used = False
        
        self.mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = mock_code
        
        result = self.service.verify_code("test@example.com", "654321", "register")
        
        assert result["success"] is False
        assert "验证码错误" in result["message"]
        assert mock_code.attempts == 1
    
    def test_verify_code_not_found(self):
        """测试验证码验证 - 验证码不存在"""
        self.mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = None
        
        result = self.service.verify_code("test@example.com", "123456", "register")
        
        assert result["success"] is False
        assert "不存在或已过期" in result["message"]
    
    def test_verify_code_max_attempts(self):
        """测试验证码验证 - 超过最大尝试次数"""
        mock_code = MagicMock()
        mock_code.code = "123456"
        mock_code.attempts = 5
        mock_code.is_used = False
        
        self.mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = mock_code
        
        result = self.service.verify_code("test@example.com", "654321", "register")
        
        assert result["success"] is False
        assert "验证次数过多" in result["message"]
    
    @pytest.mark.asyncio
    async def test_send_email_code_success(self):
        """测试发送邮箱验证码 - 成功"""
        self.mock_db.query.return_value.filter.return_value.count.return_value = 0
        self.mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = None
        
        with patch.object(self.service, '_send_email', new_callable=AsyncMock):
            result = await self.service.send_email_code("test@example.com", "register")
        
        assert result["success"] is True
        assert result["expires_in"] == 600
        self.mock_db.add.assert_called_once()
        self.mock_db.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_send_email_code_rate_limited(self):
        """测试发送邮箱验证码 - 频率限制"""
        self.mock_db.query.return_value.filter.return_value.count.return_value = 5
        
        result = await self.service.send_email_code("test@example.com", "register")
        
        assert result["success"] is False
        assert result["expires_in"] == 0
    
    @pytest.mark.asyncio
    async def test_send_email_code_failure_rollback(self):
        """测试发送邮箱验证码 - 发送失败时回滚"""
        self.mock_db.query.return_value.filter.return_value.count.return_value = 0
        self.mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = None
        
        with patch.object(self.service, '_send_email', new_callable=AsyncMock) as mock_send:
            mock_send.side_effect = Exception("发送失败")
            result = await self.service.send_email_code("test@example.com", "register")
        
        assert result["success"] is False
        self.mock_db.rollback.assert_called_once()
    
    def test_cleanup_expired_codes(self):
        """测试清理过期验证码"""
        self.mock_db.query.return_value.filter.return_value.delete.return_value = 5
        
        deleted = self.service.cleanup_expired_codes()
        
        assert deleted == 5
        self.mock_db.commit.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
