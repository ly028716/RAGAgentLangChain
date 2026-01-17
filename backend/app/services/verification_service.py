"""
验证码服务

提供邮箱和短信验证码的发送和验证功能。
"""

import logging
import secrets
import string
from datetime import datetime, timedelta
from typing import Optional, Tuple

from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.verification_code import VerificationCode
from app.config import settings

logger = logging.getLogger(__name__)


class VerificationService:
    """验证码服务"""
    
    # 配置常量
    CODE_LENGTH = 6
    CODE_EXPIRE_MINUTES = 10
    MAX_SEND_PER_HOUR = 5
    MAX_VERIFY_ATTEMPTS = 5
    MIN_SEND_INTERVAL_SECONDS = 60
    MAX_SEND_PER_IP_HOUR = 10  # 单IP每小时最多发送次数
    
    def __init__(self, db: Session):
        self.db = db
    
    def _generate_code(self) -> str:
        """生成6位数字验证码（使用安全随机数）"""
        return ''.join(secrets.choice(string.digits) for _ in range(self.CODE_LENGTH))
    
    def _check_send_rate_limit(self, target: str, code_type: str, ip_address: Optional[str] = None) -> Tuple[bool, str]:
        """
        检查发送频率限制
        
        Args:
            target: 目标(邮箱/手机号)
            code_type: 验证码类型
            ip_address: 请求IP地址（可选）
        
        Returns:
            (是否允许发送, 错误消息)
        """
        now = datetime.utcnow()
        one_hour_ago = now - timedelta(hours=1)
        
        # 检查目标1小时内发送次数
        count = self.db.query(VerificationCode).filter(
            and_(
                VerificationCode.target == target,
                VerificationCode.code_type == code_type,
                VerificationCode.created_at >= one_hour_ago
            )
        ).count()
        
        if count >= self.MAX_SEND_PER_HOUR:
            return False, "发送过于频繁，请1小时后再试"
        
        # 检查最近一次发送时间间隔
        last_code = self.db.query(VerificationCode).filter(
            and_(
                VerificationCode.target == target,
                VerificationCode.code_type == code_type
            )
        ).order_by(VerificationCode.created_at.desc()).first()
        
        if last_code:
            time_diff = (now - last_code.created_at).total_seconds()
            if time_diff < self.MIN_SEND_INTERVAL_SECONDS:
                remaining = int(self.MIN_SEND_INTERVAL_SECONDS - time_diff)
                return False, f"请{remaining}秒后再试"
        
        return True, ""
    
    async def send_email_code(self, email: str, code_type: str, ip_address: Optional[str] = None) -> dict:
        """
        发送邮箱验证码
        
        Args:
            email: 邮箱地址
            code_type: 验证码类型
            ip_address: 请求IP地址（可选）
            
        Returns:
            发送结果字典
        """
        # 检查发送频率
        can_send, error_msg = self._check_send_rate_limit(email, code_type, ip_address)
        if not can_send:
            return {
                "success": False,
                "message": error_msg,
                "expires_in": 0
            }
        
        # 生成验证码
        code = self._generate_code()
        expires_at = datetime.utcnow() + timedelta(minutes=self.CODE_EXPIRE_MINUTES)
        
        # 创建验证码记录（先不提交）
        verification_code = VerificationCode(
            target=email,
            code=code,
            code_type=code_type,
            channel="email",
            expires_at=expires_at
        )
        
        # 先发送邮件，成功后再保存到数据库
        try:
            await self._send_email(email, code, code_type)
            
            # 发送成功后保存到数据库
            self.db.add(verification_code)
            self.db.commit()
            
            logger.info(f"验证码已发送到邮箱: {email}, 类型: {code_type}")
            
            return {
                "success": True,
                "message": "验证码已发送",
                "expires_in": self.CODE_EXPIRE_MINUTES * 60
            }
        except Exception as e:
            # 发送失败，回滚事务
            self.db.rollback()
            logger.error(f"发送邮件失败: {e}")
            return {
                "success": False,
                "message": "发送失败，请稍后重试",
                "expires_in": 0
            }
    
    async def send_sms_code(self, phone: str, code_type: str, ip_address: Optional[str] = None) -> dict:
        """
        发送短信验证码
        
        Args:
            phone: 手机号
            code_type: 验证码类型
            ip_address: 请求IP地址（可选）
            
        Returns:
            发送结果字典
        """
        # 检查发送频率
        can_send, error_msg = self._check_send_rate_limit(phone, code_type, ip_address)
        if not can_send:
            return {
                "success": False,
                "message": error_msg,
                "expires_in": 0
            }
        
        # 生成验证码
        code = self._generate_code()
        expires_at = datetime.utcnow() + timedelta(minutes=self.CODE_EXPIRE_MINUTES)
        
        # 创建验证码记录（先不提交）
        verification_code = VerificationCode(
            target=phone,
            code=code,
            code_type=code_type,
            channel="sms",
            expires_at=expires_at
        )
        
        # 先发送短信，成功后再保存到数据库
        try:
            await self._send_sms(phone, code, code_type)
            
            # 发送成功后保存到数据库
            self.db.add(verification_code)
            self.db.commit()
            
            logger.info(f"验证码已发送到手机: {phone}, 类型: {code_type}")
            
            return {
                "success": True,
                "message": "验证码已发送",
                "expires_in": self.CODE_EXPIRE_MINUTES * 60
            }
        except Exception as e:
            # 发送失败，回滚事务
            self.db.rollback()
            logger.error(f"发送短信失败: {e}")
            return {
                "success": False,
                "message": "发送失败，请稍后重试",
                "expires_in": 0
            }
    
    def verify_code(self, target: str, code: str, code_type: str) -> dict:
        """
        验证验证码
        
        Args:
            target: 目标(邮箱/手机号)
            code: 验证码
            code_type: 验证码类型
            
        Returns:
            验证结果字典
        """
        now = datetime.utcnow()
        
        # 查询未使用且未过期的验证码
        verification_code = self.db.query(VerificationCode).filter(
            and_(
                VerificationCode.target == target,
                VerificationCode.code_type == code_type,
                VerificationCode.is_used == False,
                VerificationCode.expires_at > now
            )
        ).order_by(VerificationCode.created_at.desc()).first()
        
        if not verification_code:
            return {
                "success": False,
                "message": "验证码不存在或已过期"
            }
        
        # 检查验证尝试次数
        if verification_code.attempts >= self.MAX_VERIFY_ATTEMPTS:
            return {
                "success": False,
                "message": "验证次数过多，请重新获取验证码"
            }
        
        # 验证码比对
        if verification_code.code != code:
            verification_code.attempts += 1
            self.db.commit()
            remaining = self.MAX_VERIFY_ATTEMPTS - verification_code.attempts
            return {
                "success": False,
                "message": f"验证码错误，还剩{remaining}次机会"
            }
        
        # 验证成功，标记为已使用
        verification_code.is_used = True
        self.db.commit()
        
        logger.info(f"验证码验证成功: {target}, 类型: {code_type}")
        
        return {
            "success": True,
            "message": "验证成功"
        }
    
    async def _send_email(self, email: str, code: str, code_type: str):
        """
        发送邮件（模拟实现）
        
        实际生产环境需要集成aiosmtplib或其他邮件服务
        """
        # TODO: 集成实际的邮件发送服务
        # 示例代码:
        # import aiosmtplib
        # from email.mime.text import MIMEText
        # 
        # message = MIMEText(f"您的验证码是: {code}，{self.CODE_EXPIRE_MINUTES}分钟内有效。")
        # message["From"] = settings.smtp_from
        # message["To"] = email
        # message["Subject"] = self._get_email_subject(code_type)
        # 
        # await aiosmtplib.send(
        #     message,
        #     hostname=settings.smtp_host,
        #     port=settings.smtp_port,
        #     username=settings.smtp_user,
        #     password=settings.smtp_password,
        #     use_tls=settings.smtp_use_tls
        # )
        
        # 开发环境：打印验证码到日志（生产环境应移除）
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(f"[DEV] 邮箱验证码 - {email}: {code}")
    
    async def _send_sms(self, phone: str, code: str, code_type: str):
        """
        发送短信（模拟实现）
        
        实际生产环境需要集成阿里云SMS或其他短信服务
        """
        # TODO: 集成实际的短信发送服务
        # 示例代码（阿里云SMS）:
        # from alibabacloud_dysmsapi20170525.client import Client
        # from alibabacloud_dysmsapi20170525 import models
        # 
        # request = models.SendSmsRequest(
        #     phone_numbers=phone,
        #     sign_name=settings.aliyun_sms_sign_name,
        #     template_code=settings.aliyun_sms_template_code,
        #     template_param=json.dumps({"code": code})
        # )
        # client.send_sms(request)
        
        # 开发环境：打印验证码到日志（生产环境应移除）
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(f"[DEV] 短信验证码 - {phone}: {code}")
    
    def _get_email_subject(self, code_type: str) -> str:
        """获取邮件主题"""
        subjects = {
            "register": "注册验证码",
            "reset_password": "重置密码验证码",
            "bind_email": "绑定邮箱验证码"
        }
        return f"【AI智能助手】{subjects.get(code_type, '验证码')}"
    
    def cleanup_expired_codes(self):
        """清理过期的验证码"""
        now = datetime.utcnow()
        deleted = self.db.query(VerificationCode).filter(
            VerificationCode.expires_at < now
        ).delete()
        self.db.commit()
        
        if deleted > 0:
            logger.info(f"清理了 {deleted} 条过期验证码")
        
        return deleted


__all__ = ['VerificationService']
