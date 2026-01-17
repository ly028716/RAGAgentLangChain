"""
验证码 API 测试
测试范围：邮箱验证码发送、短信验证码发送、验证码验证
"""
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from datetime import datetime, timedelta
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.schemas.verification import (
    SendEmailCodeRequest,
    SendSMSCodeRequest,
    VerifyCodeRequest,
    SendCodeResponse,
    VerifyCodeResponse
)


class TestVerificationSchemas:
    """验证码 Schema 测试"""

    def test_send_email_code_request_valid(self):
        """测试有效的邮箱验证码请求"""
        request = SendEmailCodeRequest(
            email="test@example.com",
            code_type="register"
        )
        assert request.email == "test@example.com"
        assert request.code_type == "register"

    def test_send_email_code_request_invalid_email(self):
        """测试无效邮箱格式"""
        with pytest.raises(ValueError):
            SendEmailCodeRequest(
                email="invalid-email",
                code_type="register"
            )

    def test_send_email_code_request_invalid_type(self):
        """测试无效验证码类型"""
        with pytest.raises(ValueError):
            SendEmailCodeRequest(
                email="test@example.com",
                code_type="invalid_type"
            )

    def test_send_email_code_request_all_types(self):
        """测试所有有效的验证码类型"""
        valid_types = ["register", "reset_password", "bind_email"]
        for code_type in valid_types:
            request = SendEmailCodeRequest(
                email="test@example.com",
                code_type=code_type
            )
            assert request.code_type == code_type

    def test_send_sms_code_request_valid(self):
        """测试有效的短信验证码请求"""
        request = SendSMSCodeRequest(
            phone="13812345678",
            code_type="register"
        )
        assert request.phone == "13812345678"
        assert request.code_type == "register"

    def test_send_sms_code_request_invalid_phone(self):
        """测试无效手机号格式"""
        invalid_phones = ["12345678901", "1381234567", "23812345678", "138123456789"]
        for phone in invalid_phones:
            with pytest.raises(ValueError):
                SendSMSCodeRequest(
                    phone=phone,
                    code_type="register"
                )

    def test_send_sms_code_request_valid_phones(self):
        """测试有效的手机号格式"""
        valid_phones = ["13812345678", "15912345678", "18612345678", "19912345678"]
        for phone in valid_phones:
            request = SendSMSCodeRequest(
                phone=phone,
                code_type="register"
            )
            assert request.phone == phone

    def test_verify_code_request_valid(self):
        """测试有效的验证码验证请求"""
        request = VerifyCodeRequest(
            target="test@example.com",
            code="123456",
            code_type="register"
        )
        assert request.target == "test@example.com"
        assert request.code == "123456"
        assert request.code_type == "register"

    def test_verify_code_request_invalid_code_length(self):
        """测试无效验证码长度"""
        with pytest.raises(ValueError):
            VerifyCodeRequest(
                target="test@example.com",
                code="12345",  # 5位
                code_type="register"
            )
        with pytest.raises(ValueError):
            VerifyCodeRequest(
                target="test@example.com",
                code="1234567",  # 7位
                code_type="register"
            )

    def test_verify_code_request_invalid_code_format(self):
        """测试无效验证码格式（非数字）"""
        with pytest.raises(ValueError):
            VerifyCodeRequest(
                target="test@example.com",
                code="abcdef",
                code_type="register"
            )

    def test_send_code_response(self):
        """测试发送验证码响应"""
        response = SendCodeResponse(
            success=True,
            message="验证码已发送",
            expires_in=600
        )
        assert response.success is True
        assert response.message == "验证码已发送"
        assert response.expires_in == 600

    def test_verify_code_response(self):
        """测试验证码验证响应"""
        response = VerifyCodeResponse(
            success=True,
            message="验证成功"
        )
        assert response.success is True
        assert response.message == "验证成功"


class TestVerificationService:
    """验证码服务测试"""

    @pytest.fixture
    def mock_db(self):
        """Mock 数据库会话"""
        return MagicMock()

    @pytest.fixture
    def service(self, mock_db):
        """创建验证码服务实例"""
        from app.services.verification_service import VerificationService
        return VerificationService(mock_db)

    def test_generate_code_length(self, service):
        """测试验证码长度"""
        code = service._generate_code()
        assert len(code) == 6

    def test_generate_code_is_numeric(self, service):
        """测试验证码是否为纯数字"""
        code = service._generate_code()
        assert code.isdigit()

    def test_generate_code_randomness(self, service):
        """测试验证码随机性"""
        codes = set()
        for _ in range(100):
            codes.add(service._generate_code())
        # 100次生成应该有很多不同的值
        assert len(codes) > 50

    def test_rate_limit_check_no_history(self, service, mock_db):
        """测试无历史记录时的频率检查"""
        mock_db.query.return_value.filter.return_value.count.return_value = 0
        mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = None
        
        can_send, error_msg = service._check_send_rate_limit("test@example.com", "register")
        
        assert can_send is True
        assert error_msg == ""

    def test_rate_limit_check_exceeded(self, service, mock_db):
        """测试超过频率限制"""
        mock_db.query.return_value.filter.return_value.count.return_value = 5
        
        can_send, error_msg = service._check_send_rate_limit("test@example.com", "register")
        
        assert can_send is False
        assert "1小时后再试" in error_msg

    def test_rate_limit_check_too_frequent(self, service, mock_db):
        """测试发送过于频繁"""
        mock_db.query.return_value.filter.return_value.count.return_value = 1
        
        last_code = MagicMock()
        last_code.created_at = datetime.utcnow() - timedelta(seconds=30)
        mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = last_code
        
        can_send, error_msg = service._check_send_rate_limit("test@example.com", "register")
        
        assert can_send is False
        assert "秒后再试" in error_msg

    def test_verify_code_success(self, service, mock_db):
        """测试验证码验证成功"""
        mock_code = MagicMock()
        mock_code.code = "123456"
        mock_code.attempts = 0
        mock_code.is_used = False
        
        mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = mock_code
        
        result = service.verify_code("test@example.com", "123456", "register")
        
        assert result["success"] is True
        assert mock_code.is_used is True

    def test_verify_code_wrong(self, service, mock_db):
        """测试验证码错误"""
        mock_code = MagicMock()
        mock_code.code = "123456"
        mock_code.attempts = 0
        mock_code.is_used = False
        
        mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = mock_code
        
        result = service.verify_code("test@example.com", "654321", "register")
        
        assert result["success"] is False
        assert "验证码错误" in result["message"]
        assert mock_code.attempts == 1

    def test_verify_code_not_found(self, service, mock_db):
        """测试验证码不存在"""
        mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = None
        
        result = service.verify_code("test@example.com", "123456", "register")
        
        assert result["success"] is False
        assert "不存在或已过期" in result["message"]

    def test_verify_code_max_attempts(self, service, mock_db):
        """测试超过最大验证次数"""
        mock_code = MagicMock()
        mock_code.code = "123456"
        mock_code.attempts = 5
        mock_code.is_used = False
        
        mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = mock_code
        
        result = service.verify_code("test@example.com", "654321", "register")
        
        assert result["success"] is False
        assert "验证次数过多" in result["message"]

    @pytest.mark.asyncio
    async def test_send_email_code_success(self, service, mock_db):
        """测试发送邮箱验证码成功"""
        mock_db.query.return_value.filter.return_value.count.return_value = 0
        mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = None
        
        with patch.object(service, '_send_email', new_callable=AsyncMock):
            result = await service.send_email_code("test@example.com", "register")
        
        assert result["success"] is True
        assert result["expires_in"] == 600
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_email_code_rate_limited(self, service, mock_db):
        """测试发送邮箱验证码频率限制"""
        mock_db.query.return_value.filter.return_value.count.return_value = 5
        
        result = await service.send_email_code("test@example.com", "register")
        
        assert result["success"] is False
        assert result["expires_in"] == 0

    @pytest.mark.asyncio
    async def test_send_email_code_failure_rollback(self, service, mock_db):
        """测试发送失败时回滚"""
        mock_db.query.return_value.filter.return_value.count.return_value = 0
        mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = None
        
        with patch.object(service, '_send_email', new_callable=AsyncMock) as mock_send:
            mock_send.side_effect = Exception("发送失败")
            result = await service.send_email_code("test@example.com", "register")
        
        assert result["success"] is False
        mock_db.rollback.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_sms_code_success(self, service, mock_db):
        """测试发送短信验证码成功"""
        mock_db.query.return_value.filter.return_value.count.return_value = 0
        mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = None
        
        with patch.object(service, '_send_sms', new_callable=AsyncMock):
            result = await service.send_sms_code("13812345678", "register")
        
        assert result["success"] is True
        assert result["expires_in"] == 600

    def test_cleanup_expired_codes(self, service, mock_db):
        """测试清理过期验证码"""
        mock_db.query.return_value.filter.return_value.delete.return_value = 10
        
        deleted = service.cleanup_expired_codes()
        
        assert deleted == 10
        mock_db.commit.assert_called_once()


class TestVerificationModel:
    """验证码模型测试"""

    def test_model_fields(self):
        """测试模型字段"""
        from app.models.verification_code import VerificationCode
        
        # 检查必要字段存在
        assert hasattr(VerificationCode, 'id')
        assert hasattr(VerificationCode, 'target')
        assert hasattr(VerificationCode, 'code')
        assert hasattr(VerificationCode, 'code_type')
        assert hasattr(VerificationCode, 'channel')
        assert hasattr(VerificationCode, 'expires_at')
        assert hasattr(VerificationCode, 'is_used')
        assert hasattr(VerificationCode, 'attempts')
        assert hasattr(VerificationCode, 'created_at')

    def test_model_table_name(self):
        """测试表名"""
        from app.models.verification_code import VerificationCode
        
        assert VerificationCode.__tablename__ == "verification_codes"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
