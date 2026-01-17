# 安全加固指南

本文档描述了AI智能助手系统的安全加固措施和最佳实践。

## 📋 目录

- [管理员权限管理](#管理员权限管理)
- [密码安全](#密码安全)
- [API安全](#api安全)
- [数据加密](#数据加密)
- [速率限制](#速率限制)
- [日志审计](#日志审计)
- [安全配置检查清单](#安全配置检查清单)

---

## 🔐 管理员权限管理

### 1. 管理员字段

用户表中添加了 `is_admin` 字段来标识管理员用户：

```sql
ALTER TABLE users ADD COLUMN is_admin BOOLEAN NOT NULL DEFAULT FALSE;
CREATE INDEX ix_users_is_admin ON users(is_admin);
```

### 2. 创建管理员用户

**方法一：使用脚本创建默认管理员**

```bash
# 创建默认管理员账户（用户名: admin, 密码: Admin123456）
python create_admin.py

# ⚠️ 生产环境必须立即修改默认密码！
```

**方法二：设置现有用户为管理员**

```bash
# 设置用户为管理员
python set_admin.py <username>

# 示例
python set_admin.py john

# 撤销管理员权限
python set_admin.py --revoke <username>

# 列出所有管理员
python set_admin.py --list
```

**方法三：通过数据库直接设置**

```sql
-- 设置用户为管理员
UPDATE users SET is_admin = TRUE WHERE username = 'admin';

-- 撤销管理员权限
UPDATE users SET is_admin = FALSE WHERE username = 'testuser';

-- 查询所有管理员
SELECT id, username, email, is_active, is_admin FROM users WHERE is_admin = TRUE;
```

### 3. 管理员权限验证

系统提供了 `get_current_admin_user` 依赖函数用于验证管理员权限：

```python
from app.dependencies import get_current_admin_user

@router.get("/admin/stats")
async def get_admin_stats(
    admin: User = Depends(get_current_admin_user)
):
    # 只有管理员可以访问
    return {"message": "Admin only"}
```

### 4. 需要管理员权限的端点

以下API端点需要管理员权限：

- `PUT /api/v1/quota` - 更新用户配额
- `POST /api/v1/quota/reset` - 重置用户配额
- `GET /api/v1/system/config` - 获取系统配置
- `PUT /api/v1/system/config` - 更新系统配置
- `GET /api/v1/system/stats/all` - 获取全局使用统计

---

## 🔒 密码安全

### 1. 密码强度要求

系统强制执行以下密码策略：

- **最小长度**: 8个字符
- **必须包含**: 
  - 至少1个大写字母
  - 至少1个小写字母
  - 至少1个数字
- **推荐**: 包含特殊字符

### 2. 密码加密

- 使用 **Bcrypt** 算法加密密码
- 工作因子（rounds）: **12**
- 密码哈希存储在 `password_hash` 字段

```python
from app.core.security import hash_password, verify_password

# 加密密码
hashed = hash_password("MyPassword123")

# 验证密码
is_valid = verify_password("MyPassword123", hashed)
```

### 3. 登录失败锁定

防止暴力破解攻击：

- **失败阈值**: 5次
- **锁定时间**: 15分钟
- **记录表**: `login_attempts`

配置项：
```bash
ACCOUNT_LOCKOUT_THRESHOLD=5
ACCOUNT_LOCKOUT_DURATION=900  # 秒
```

### 4. 密码修改建议

**生产环境部署后必须执行：**

1. 修改默认管理员密码
2. 禁用或删除测试账户
3. 定期提醒用户更新密码（建议90天）

---

## 🛡️ API安全

### 1. JWT令牌安全

**令牌配置：**

```bash
# JWT密钥（必须修改为强随机字符串）
SECRET_KEY=your-secret-key-at-least-32-characters-long

# 令牌过期时间
JWT_ACCESS_TOKEN_EXPIRE_DAYS=7
JWT_REFRESH_TOKEN_EXPIRE_DAYS=30

# 签名算法
JWT_ALGORITHM=HS256
```

**生成强密钥：**

```bash
# 方法1: 使用OpenSSL
openssl rand -hex 32

# 方法2: 使用Python
python -c "import secrets; print(secrets.token_hex(32))"
```

**令牌黑名单：**

- 用户登出时令牌加入黑名单
- 存储在Redis中，自动过期
- 防止令牌重放攻击

### 2. CORS配置

限制允许的来源：

```bash
# 开发环境
CORS_ORIGINS=http://localhost:3000,http://localhost:5173

# 生产环境（必须指定具体域名）
CORS_ORIGINS=https://yourdomain.com,https://app.yourdomain.com
```

**不要使用 `*` 允许所有来源！**

### 3. HTTPS强制

生产环境必须使用HTTPS：

```nginx
# Nginx配置
server {
    listen 80;
    server_name api.yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name api.yourdomain.com;
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    # 强制使用TLS 1.2+
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    
    # HSTS
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
}
```

### 4. 请求验证

所有API输入都经过Pydantic验证：

- 类型检查
- 长度限制
- 格式验证
- SQL注入防护（ORM参数化查询）
- XSS防护（输入清理）

---

## 🔐 数据加密

### 1. 敏感数据加密

使用AES-256加密存储敏感数据：

```python
from app.core.security import encrypt_data, decrypt_data

# 加密API密钥
encrypted_key = encrypt_data("sk-your-api-key")

# 解密
original_key = decrypt_data(encrypted_key)
```

**需要加密的数据：**
- API密钥（通义千问等）
- 第三方服务凭证
- 敏感配置项

### 2. 数据脱敏

查询系统配置时自动脱敏：

```python
# API密钥脱敏
"sk-abc123def456" -> "sk-abc***def456"

# 邮箱脱敏
"user@example.com" -> "u***r@example.com"
```

### 3. 数据库连接安全

```bash
# 使用SSL连接MySQL
DATABASE_URL=mysql+pymysql://user:pass@host:3306/db?ssl_ca=/path/to/ca.pem

# Redis密码保护
REDIS_PASSWORD=your-strong-redis-password
```

---

## ⏱️ 速率限制

### 1. API速率限制

使用 `slowapi` 实现速率限制：

```python
# 配置
RATE_LIMIT_LOGIN=5/minute        # 登录接口
RATE_LIMIT_API=100/minute        # 通用API
RATE_LIMIT_LLM=20/minute         # LLM调用
```

### 2. 自定义速率限制

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@router.post("/sensitive-operation")
@limiter.limit("5/minute")
async def sensitive_operation():
    pass
```

### 3. IP黑名单

可以在Nginx层面实现IP黑名单：

```nginx
# 拒绝特定IP
deny 192.168.1.100;
deny 10.0.0.0/8;

# 允许其他IP
allow all;
```

---

## 📝 日志审计

### 1. 安全事件日志

系统记录以下安全事件：

- 登录成功/失败
- 密码修改
- 管理员操作（配额调整、配置修改等）
- 权限验证失败
- 异常API调用

### 2. 日志格式

```json
{
  "timestamp": "2025-01-16T10:30:00Z",
  "level": "INFO",
  "event": "admin_action",
  "user_id": 1,
  "username": "admin",
  "action": "update_quota",
  "target_user_id": 5,
  "details": {"new_quota": 200000},
  "ip_address": "192.168.1.100",
  "request_id": "abc-123-def"
}
```

### 3. 日志查询

```bash
# 查看管理员操作日志
grep "admin_action" logs/app.log

# 查看登录失败记录
grep "login_failed" logs/app.log

# 查看特定用户的操作
grep "user_id=5" logs/app.log
```

### 4. 日志保留策略

- **保留时间**: 90天
- **轮转策略**: 每天或达到10MB
- **备份**: 定期备份到安全存储

---

## ✅ 安全配置检查清单

### 部署前检查

- [ ] 修改默认管理员密码
- [ ] 设置强随机的 `SECRET_KEY`
- [ ] 配置正确的 `CORS_ORIGINS`
- [ ] 启用HTTPS
- [ ] 配置防火墙规则
- [ ] 设置数据库访问限制
- [ ] 配置Redis密码
- [ ] 启用日志记录
- [ ] 配置备份策略
- [ ] 删除或禁用测试账户

### 环境变量检查

```bash
# 必须设置的安全相关环境变量
✓ SECRET_KEY (至少32字符)
✓ DASHSCOPE_API_KEY
✓ DATABASE_URL (生产数据库)
✓ REDIS_PASSWORD
✓ CORS_ORIGINS (具体域名)

# 推荐设置
✓ MAX_LOGIN_ATTEMPTS=5
✓ ACCOUNT_LOCKOUT_MINUTES=15
✓ BCRYPT_ROUNDS=12
✓ JWT_ACCESS_TOKEN_EXPIRE_DAYS=7
```

### 定期安全审计

**每月检查：**
- [ ] 审查管理员账户列表
- [ ] 检查异常登录记录
- [ ] 审查API使用统计
- [ ] 检查失败的认证尝试
- [ ] 更新依赖包版本

**每季度检查：**
- [ ] 密码策略审查
- [ ] 权限配置审查
- [ ] 日志分析
- [ ] 安全漏洞扫描
- [ ] 备份恢复测试

---

## 🚨 安全事件响应

### 1. 发现可疑活动

```bash
# 立即禁用可疑账户
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
```

### 2. 撤销所有令牌

```bash
# 清空Redis中的所有令牌
redis-cli FLUSHDB
```

### 3. 强制所有用户重新登录

```bash
# 清空令牌缓存
redis-cli KEYS "token:*" | xargs redis-cli DEL
```

### 4. 紧急联系方式

- 技术负责人: [联系方式]
- 安全团队: [联系方式]
- 应急响应流程: [文档链接]

---

## 📚 相关文档

- [API文档](API_DOCUMENTATION.md)
- [部署指南](DEPLOYMENT.md)
- [配置说明](CONFIG_USAGE.md)
- [故障排查](README.md#故障排查)

---

## 🔄 更新日志

- **2025-01-16**: 添加管理员权限验证和安全加固措施
- **2025-01-09**: 初始版本

---

**⚠️ 重要提醒：**

1. 生产环境部署前必须完成所有安全配置检查
2. 定期更新系统和依赖包
3. 保持安全意识，及时响应安全事件
4. 定期备份数据和配置
5. 遵循最小权限原则

如有安全问题或建议，请联系安全团队。
