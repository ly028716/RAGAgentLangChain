# 部署检查清单

## ✅ 管理员权限和安全加固 - 部署指南

### 📋 部署前准备

#### 1. 环境检查

```bash
# 检查Python版本
python --version  # 应该 >= 3.10

# 检查MySQL服务
docker-compose ps | grep mysql
# 或
systemctl status mysql

# 检查Redis服务
docker-compose ps | grep redis
# 或
systemctl status redis
```

#### 2. 配置检查

```bash
# 检查.env文件
cat backend/.env

# 必需配置项:
# - MYSQL_USER
# - MYSQL_PASSWORD
# - MYSQL_DATABASE
# - SECRET_KEY (强随机字符串)
# - DASHSCOPE_API_KEY
```

### 🚀 部署步骤

#### 步骤1: 应用数据库迁移

**使用Docker Compose（推荐）**:

```bash
cd backend

# 启动服务
docker-compose up -d

# 等待MySQL启动（约10秒）
sleep 10

# 应用迁移
docker-compose exec backend alembic upgrade head

# 查看迁移状态
docker-compose exec backend alembic current
# 应该显示: 005_is_admin (head)
```

**本地环境**:

```bash
cd backend

# 激活虚拟环境
source .venv/bin/activate  # Linux/Mac
# 或
.venv\Scripts\activate  # Windows

# 应用迁移
alembic upgrade head

# 查看迁移状态
alembic current
```

**遇到问题？** 查看 [MIGRATION_GUIDE.md](MIGRATION_GUIDE.md)

#### 步骤2: 验证迁移

```bash
# 运行验证脚本
python test_migration.py
```

**预期输出**:
```
✓ 数据库连接成功
✓ users表存在
✓ is_admin字段已存在
✓ is_admin索引已创建
✓ 所有检查通过！
```

#### 步骤3: 创建管理员用户

```bash
# 创建默认管理员（用户名: admin, 密码: Admin123456）
python create_admin.py
```

**输出**:
```
✓ admin 管理员用户创建成功
  用户名: admin
  密码: Admin123456
  权限: 管理员
  配额: 1,000,000 tokens/月

⚠️  请在生产环境中立即修改默认密码！
```

#### 步骤4: 修改默认密码（生产环境必须！）

**方法1: 通过API**

```bash
# 1. 登录获取令牌
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "Admin123456"}' \
  | jq -r '.access_token')

# 2. 修改密码
curl -X PUT http://localhost:8000/api/v1/auth/password \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"old_password": "Admin123456", "new_password": "YourStrongPassword123!"}'
```

**方法2: 通过前端界面**

1. 登录系统（admin / Admin123456）
2. 进入个人设置
3. 修改密码

#### 步骤5: 运行安全检查

```bash
# 运行安全配置检查
python scripts/security_check.py
```

**预期输出**:
```
============================================================
                        检查总结
============================================================
总检查项: 10
通过: 10
失败: 0
通过率: 100.0%

✓ 所有安全检查通过！
```

#### 步骤6: 运行测试

```bash
# 运行管理员权限测试
pytest tests/test_admin_permissions.py -v
```

**预期输出**:
```
tests/test_admin_permissions.py::TestAdminPermissions::test_admin_can_update_quota PASSED
tests/test_admin_permissions.py::TestAdminPermissions::test_normal_user_cannot_update_quota PASSED
...
==================== 15 passed in 2.34s ====================
```

### ✅ 部署验证清单

完成以下检查项：

- [ ] 数据库迁移成功（alembic current 显示 005_is_admin）
- [ ] 迁移验证通过（python test_migration.py）
- [ ] 管理员用户已创建
- [ ] 默认密码已修改（生产环境）
- [ ] 安全检查通过（python scripts/security_check.py）
- [ ] 测试通过（pytest tests/test_admin_permissions.py）
- [ ] 管理员可以登录
- [ ] 管理员可以访问管理端点
- [ ] 普通用户无法访问管理端点

### 🔧 常见问题

#### 问题1: 数据库连接失败

```bash
# 检查Docker服务
docker-compose ps

# 重启服务
docker-compose restart mysql

# 查看日志
docker-compose logs mysql
```

#### 问题2: 迁移失败

```bash
# 查看当前版本
alembic current

# 查看迁移历史
alembic history

# 如果需要，回滚并重试
alembic downgrade -1
alembic upgrade head
```

#### 问题3: 字段已存在

如果is_admin字段已经存在：

```bash
# 标记迁移为已完成
alembic stamp 005_is_admin

# 验证
python test_migration.py
```

### 📚 相关文档

- **迁移指南**: [MIGRATION_GUIDE.md](MIGRATION_GUIDE.md) - 详细的迁移说明
- **快速配置**: [SECURITY_QUICKSTART.md](SECURITY_QUICKSTART.md) - 5分钟配置
- **安全指南**: [SECURITY_HARDENING.md](SECURITY_HARDENING.md) - 完整安全指南
- **实施报告**: [ADMIN_SECURITY_IMPLEMENTATION.md](ADMIN_SECURITY_IMPLEMENTATION.md) - 详细实施

### 🎯 下一步

部署完成后：

1. **配置生产环境**
   - 设置强SECRET_KEY
   - 配置CORS_ORIGINS
   - 关闭DEBUG模式
   - 配置HTTPS

2. **设置监控**
   - 配置日志收集
   - 设置告警规则
   - 监控管理员操作

3. **定期维护**
   - 定期备份数据库
   - 审查管理员列表
   - 检查安全日志
   - 更新依赖包

### 🆘 需要帮助？

1. 查看迁移指南: [MIGRATION_GUIDE.md](MIGRATION_GUIDE.md)
2. 运行测试脚本: `python test_migration.py`
3. 查看日志: `docker-compose logs backend`
4. 运行安全检查: `python scripts/security_check.py`

---

**最后更新**: 2025-01-16  
**版本**: 1.0.0
