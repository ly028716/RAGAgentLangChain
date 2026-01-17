#!/usr/bin/env python3
"""
安全配置检查脚本

检查系统的安全配置是否符合最佳实践
"""

import os
import sys
import re
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config import settings


class Colors:
    """终端颜色"""
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    END = '\033[0m'
    BOLD = '\033[1m'


def print_header(text: str):
    """打印标题"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text:^60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}\n")


def print_check(name: str, passed: bool, message: str = ""):
    """打印检查结果"""
    if passed:
        icon = f"{Colors.GREEN}✓{Colors.END}"
        status = f"{Colors.GREEN}通过{Colors.END}"
    else:
        icon = f"{Colors.RED}✗{Colors.END}"
        status = f"{Colors.RED}失败{Colors.END}"
    
    print(f"{icon} {name:40s} [{status}]")
    if message:
        print(f"  {Colors.YELLOW}→ {message}{Colors.END}")


def print_warning(name: str, message: str):
    """打印警告"""
    icon = f"{Colors.YELLOW}⚠{Colors.END}"
    print(f"{icon} {name:40s} [{Colors.YELLOW}警告{Colors.END}]")
    print(f"  {Colors.YELLOW}→ {message}{Colors.END}")


def check_secret_key() -> tuple[bool, str]:
    """检查SECRET_KEY"""
    secret_key = settings.SECRET_KEY
    
    if not secret_key or secret_key == "your-secret-key-here":
        return False, "SECRET_KEY未设置或使用默认值"
    
    if len(secret_key) < 32:
        return False, f"SECRET_KEY长度不足（当前: {len(secret_key)}，建议: ≥32）"
    
    # 检查是否是简单密码
    simple_patterns = [
        r'^[a-z]+$',  # 纯小写
        r'^[A-Z]+$',  # 纯大写
        r'^[0-9]+$',  # 纯数字
        r'^(123|abc|password|secret)',  # 常见弱密码
    ]
    
    for pattern in simple_patterns:
        if re.match(pattern, secret_key, re.IGNORECASE):
            return False, "SECRET_KEY过于简单，建议使用强随机字符串"
    
    return True, ""


def check_database_config() -> tuple[bool, str]:
    """检查数据库配置"""
    db_url = settings.DATABASE_URL
    
    if not db_url:
        return False, "DATABASE_URL未设置"
    
    # 检查是否使用默认密码
    if "password" in db_url.lower() or "123456" in db_url:
        return False, "数据库密码过于简单"
    
    # 检查是否使用localhost（生产环境警告）
    if "localhost" in db_url or "127.0.0.1" in db_url:
        if not settings.DEBUG:
            return False, "生产环境不应使用localhost数据库"
    
    return True, ""


def check_cors_origins() -> tuple[bool, str]:
    """检查CORS配置"""
    origins = settings.CORS_ORIGINS
    
    if not origins:
        return False, "CORS_ORIGINS未设置"
    
    # 检查是否允许所有来源
    if "*" in origins:
        return False, "不应允许所有来源（*），请指定具体域名"
    
    # 检查是否包含localhost（生产环境警告）
    if not settings.DEBUG:
        if any("localhost" in origin for origin in origins):
            return False, "生产环境不应包含localhost"
    
    return True, ""


def check_api_key() -> tuple[bool, str]:
    """检查API密钥"""
    api_key = settings.DASHSCOPE_API_KEY
    
    if not api_key:
        return False, "DASHSCOPE_API_KEY未设置"
    
    if api_key == "your-api-key-here":
        return False, "使用默认API密钥"
    
    return True, ""


def check_redis_config() -> tuple[bool, str]:
    """检查Redis配置"""
    redis_url = settings.REDIS_URL
    
    if not redis_url:
        return False, "REDIS_URL未设置"
    
    # 检查是否设置密码
    if not settings.DEBUG and "password" not in redis_url.lower():
        return False, "生产环境Redis应设置密码"
    
    return True, ""


def check_password_policy() -> tuple[bool, str]:
    """检查密码策略"""
    min_length = getattr(settings, 'PASSWORD_MIN_LENGTH', 8)
    
    if min_length < 8:
        return False, f"密码最小长度过短（当前: {min_length}，建议: ≥8）"
    
    return True, ""


def check_rate_limiting() -> tuple[bool, str]:
    """检查速率限制"""
    # 检查是否配置了速率限制
    has_rate_limit = hasattr(settings, 'RATE_LIMIT_LOGIN')
    
    if not has_rate_limit:
        return False, "未配置速率限制"
    
    return True, ""


def check_jwt_config() -> tuple[bool, str]:
    """检查JWT配置"""
    access_expire = settings.JWT_ACCESS_TOKEN_EXPIRE_DAYS
    refresh_expire = settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS
    
    if access_expire > 30:
        return False, f"访问令牌过期时间过长（当前: {access_expire}天，建议: ≤30天）"
    
    if refresh_expire > 90:
        return False, f"刷新令牌过期时间过长（当前: {refresh_expire}天，建议: ≤90天）"
    
    return True, ""


def check_debug_mode() -> tuple[bool, str]:
    """检查调试模式"""
    if settings.DEBUG:
        return False, "生产环境不应启用DEBUG模式"
    
    return True, ""


def check_file_upload() -> tuple[bool, str]:
    """检查文件上传配置"""
    max_size = settings.MAX_UPLOAD_SIZE_MB
    
    if max_size > 50:
        return False, f"文件上传大小限制过大（当前: {max_size}MB，建议: ≤50MB）"
    
    allowed_types = settings.ALLOWED_FILE_TYPES
    if not allowed_types:
        return False, "未限制允许的文件类型"
    
    return True, ""


def check_admin_users():
    """检查管理员用户"""
    try:
        from app.core.database import SessionLocal
        from app.models.user import User
        
        db = SessionLocal()
        admin_count = db.query(User).filter(User.is_admin == True).count()
        db.close()
        
        if admin_count == 0:
            print_warning("管理员用户", "系统中没有管理员用户")
        else:
            print_check("管理员用户", True, f"共有 {admin_count} 个管理员")
    except Exception as e:
        print_warning("管理员用户", f"无法检查: {str(e)}")


def main():
    """主函数"""
    print_header("AI智能助手系统 - 安全配置检查")
    
    print(f"{Colors.BOLD}环境信息:{Colors.END}")
    print(f"  调试模式: {Colors.YELLOW if settings.DEBUG else Colors.GREEN}{settings.DEBUG}{Colors.END}")
    print(f"  应用版本: {settings.APP_VERSION}")
    
    # 执行检查
    checks = [
        ("SECRET_KEY强度", check_secret_key),
        ("数据库配置", check_database_config),
        ("CORS配置", check_cors_origins),
        ("API密钥配置", check_api_key),
        ("Redis配置", check_redis_config),
        ("密码策略", check_password_policy),
        ("速率限制", check_rate_limiting),
        ("JWT配置", check_jwt_config),
        ("调试模式", check_debug_mode),
        ("文件上传限制", check_file_upload),
    ]
    
    print_header("配置检查")
    
    passed_count = 0
    failed_count = 0
    
    for name, check_func in checks:
        try:
            passed, message = check_func()
            print_check(name, passed, message)
            if passed:
                passed_count += 1
            else:
                failed_count += 1
        except Exception as e:
            print_check(name, False, f"检查失败: {str(e)}")
            failed_count += 1
    
    # 检查管理员用户
    print_header("用户检查")
    check_admin_users()
    
    # 总结
    print_header("检查总结")
    total = passed_count + failed_count
    pass_rate = (passed_count / total * 100) if total > 0 else 0
    
    print(f"总检查项: {total}")
    print(f"{Colors.GREEN}通过: {passed_count}{Colors.END}")
    print(f"{Colors.RED}失败: {failed_count}{Colors.END}")
    print(f"通过率: {Colors.GREEN if pass_rate >= 80 else Colors.RED}{pass_rate:.1f}%{Colors.END}")
    
    if failed_count > 0:
        print(f"\n{Colors.RED}⚠️  发现 {failed_count} 个安全问题，请及时修复！{Colors.END}")
        print(f"{Colors.YELLOW}详细信息请参考: SECURITY_HARDENING.md{Colors.END}")
        sys.exit(1)
    else:
        print(f"\n{Colors.GREEN}✓ 所有安全检查通过！{Colors.END}")
        sys.exit(0)


if __name__ == "__main__":
    main()
