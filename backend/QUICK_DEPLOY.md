# 🚀 快速部署指南

## 一键部署（推荐）

### Windows用户

```cmd
cd backend
deploy_admin_security.bat
```

### Linux/Mac用户

```bash
cd backend
chmod +x deploy_admin_security.sh
./deploy_admin_security.sh
```

## 手动部署

### 步骤1: 重新构建镜像

```bash
cd backend
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### 步骤2: 等待服务启动

```bash
# 等待30秒
sleep 30

# 检查服务状态
docker-compose ps
```

### 步骤3: 应用迁移

```bash
docker-compose exec backend alembic upgrade head
```

### 步骤4: 创建管理员

```bash
docker-compose exec backend python create_admin.py
```

### 步骤5: 验证部署

```bash
# 检查迁移状态
docker-compose exec backend alembic current
# 应该显示: 005_is_admin (head)

# 检查字段
docker-compose exec mysql mysql -u ai_user -pai_password ai_assistant -e "DESCRIBE users;" | grep is_admin

# 检查管理员
docker-compose exec mysql mysql -u ai_user -pai_password ai_assistant -e "SELECT id, username, is_admin FROM users WHERE is_admin = 1;"
```

## 快速测试

### 1. 测试登录

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "Admin123456"}'
```

### 2. 测试管理员权限

```bash
# 获取令牌
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "Admin123456"}' \
  | jq -r '.access_token')

# 测试管理员端点
curl -X GET http://localhost:8000/api/v1/system/config \
  -H "Authorization: Bearer $TOKEN"
```

## 常见问题

### Q: 找不到test_migration.py文件

**A**: 需要重新构建Docker镜像：

```bash
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### Q: 数据库连接失败

**A**: 检查MySQL服务：

```bash
docker-compose ps mysql
docker-compose logs mysql
docker-compose restart mysql
```

### Q: 迁移失败

**A**: 手动应用迁移：

```bash
# 检查当前版本
docker-compose exec backend alembic current

# 如果需要，回滚并重试
docker-compose exec backend alembic downgrade -1
docker-compose exec backend alembic upgrade head
```

## 下一步

1. **修改默认密码**（生产环境必须！）
   - 访问: http://localhost:8000
   - 登录: admin / Admin123456
   - 修改密码

2. **运行安全检查**
   ```bash
   docker-compose exec backend python scripts/security_check.py
   ```

3. **查看API文档**
   - http://localhost:8000/docs

## 需要帮助？

- [DOCKER_DEPLOYMENT.md](DOCKER_DEPLOYMENT.md) - Docker详细部署
- [MIGRATION_GUIDE.md](MIGRATION_GUIDE.md) - 迁移问题排查
- [DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md) - 完整检查清单

---

**提示**: 如果使用一键部署脚本，所有步骤都会自动完成！
