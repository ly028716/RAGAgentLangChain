# 安全配置快速指南

本指南帮助您快速完成系统的安全配置。

## 🚀 5分钟安全配置

### 1. 生成强密钥

```bash
# 生成SECRET_KEY
python -c "import secrets; print('SECRET_KEY=' + secrets.token_hex(32))"

# 将输出添加到.env文件
```

### 2. 创建管理员用户

```bash
# 方法1: 使用脚本创建默认管理员
python create_admin.py

# 方法2: 设置现有用户为管理员
python set_admin.py <username>
```

### 3. 修改默认密码

```bash
# 登录系统后立即修改密码
# 或通过API修改:
curl -X PUT http://localhost:8000/api/v1/auth/password \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"old_password": "Admin123456", "new_password": "YourStrongPassword123!"}'
```

### 4. 配置CORS

编辑 `.env` 文件：

```bash
# 开发环境
CORS_ORIGINS=http://localhost:3000,http://localhost:5173

# 生产环境（替换为实际域名）
CORS_ORIGINS=https://yourdomain.com,https://app.yourdomain.com
```

### 5. 运行安全检查

```bash
python scripts/security_check.py
```

## ✅ 部署前检查清单

复制以下清单，逐项检查：

```
部署前安全检查清单
====================

[ ] 1. 已生成并设置强随机SECRET_KEY（≥32字符）
[ ] 2. 已创建管理员用户
[ ] 3. 已修改默认管理员密码
[ ] 4. 已配置正确的CORS_ORIGINS（不包含*）
[ ] 5. 已设置DASHSCOPE_API_KEY
[ ] 6. 已配置生产数据库（不使用localhost）
[ ] 7. 已设置Redis密码
[ ] 8. DEBUG模式已关闭（DEBUG=False）
[ ] 9. 已配置HTTPS（生产环境）
[ ] 10. 已删除或禁用测试账户
[ ] 11. 已运行安全检查脚本（python scripts/security_check.py）
[ ] 12. 已配置防火墙规则
[ ] 13. 已设置日志记录
[ ] 14. 已配置备份策略
```

## 🔐 必需的环境变量

创建 `.env` 文件并设置以下变量：

```bash
# ============ 必需配置 ============

# JWT密钥（必须修改！）
SECRET_KEY=your-secret-key-at-least-32-characters-long

# 通义千问API密钥
DASHSCOPE_API_KEY=sk-your-api-key-here

# 数据库配置
DATABASE_URL=mysql+pymysql://user:password@host:3306/database

# Redis配置
REDIS_URL=redis://localhost:6379/0
REDIS_PASSWORD=your-redis-password

# CORS配置（生产环境必须指定具体域名）
CORS_ORIGINS=https://yourdomain.com

# ============ 安全配置 ============

# 调试模式（生产环境必须为False）
DEBUG=False

# 密码策略
PASSWORD_MIN_LENGTH=8
MAX_LOGIN_ATTEMPTS=5
ACCOUNT_LOCKOUT_MINUTES=15

# JWT配置
JWT_ACCESS_TOKEN_EXPIRE_DAYS=7
JWT_REFRESH_TOKEN_EXPIRE_DAYS=30

# 文件上传限制
MAX_UPLOAD_SIZE_MB=10
ALLOWED_FILE_TYPES=pdf,docx,doc,txt,md

# 速率限制
RATE_LIMIT_LOGIN=5/minute
RATE_LIMIT_API=100/minute
RATE_LIMIT_LLM=20/minute
```

## 🛠️ 常用命令

### 管理员管理

```bash
# 设置用户为管理员
python set_admin.py <username>

# 撤销管理员权限
python set_admin.py --revoke <username>

# 列出所有管理员
python set_admin.py --list
```

### 数据库管理

```bash
# 应用数据库迁移
alembic upgrade head

# 创建管理员用户
python create_admin.py

# 查看数据库版本
alembic current
```

### 安全检查

```bash
# 运行安全配置检查
python scripts/security_check.py

# 运行测试（包括安全测试）
pytest tests/test_admin_permissions.py -v
```

## 🚨 紧急情况处理

### 禁用可疑账户

```bash
# 方法1: 使用Python
python -c "
from app.core.database import SessionLocal
from app.models.user import User
db = SessionLocal()
user = db.query(User).filter(User.username == 'suspicious_user').first()
if user:
    user.is_active = False
    db.commit()
    print('账户已禁用')
db.close()
"

# 方法2: 直接SQL
mysql -u root -p -e "UPDATE users SET is_active = FALSE WHERE username = 'suspicious_user';"
```

### 撤销所有令牌

```bash
# 清空Redis中的所有令牌
redis-cli FLUSHDB

# 或只清空令牌相关的键
redis-cli KEYS "token:*" | xargs redis-cli DEL
```

### 查看可疑登录

```bash
# 查看登录失败记录
grep "login_failed" logs/app.log | tail -n 50

# 查看特定IP的活动
grep "192.168.1.100" logs/app.log
```

## 📚 更多信息

- 完整安全指南: [SECURITY_HARDENING.md](SECURITY_HARDENING.md)
- API文档: [API_DOCUMENTATION.md](API_DOCUMENTATION.md)
- 部署指南: [DEPLOYMENT.md](DEPLOYMENT.md)

## ⚠️ 重要提醒

1. **永远不要**在生产环境使用默认密码
2. **永远不要**将SECRET_KEY提交到版本控制
3. **永远不要**在生产环境启用DEBUG模式
4. **永远不要**允许所有CORS来源（*）
5. **定期**更新依赖包和系统
6. **定期**备份数据库和配置
7. **定期**审查日志和用户活动

## 🆘 需要帮助？

如有安全问题或疑问，请：

1. 查看 [SECURITY_HARDENING.md](SECURITY_HARDENING.md)
2. 运行 `python scripts/security_check.py` 获取详细信息
3. 联系安全团队

---

**最后更新**: 2025-01-16
