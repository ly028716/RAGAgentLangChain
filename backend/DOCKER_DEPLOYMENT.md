# Docker 部署指南

## 🐳 使用Docker部署管理员权限功能

### 方法一：重新构建镜像（推荐）

由于添加了新文件，需要重新构建Docker镜像：

```bash
cd backend

# 1. 停止并删除旧容器
docker-compose down

# 2. 重新构建镜像
docker-compose build --no-cache

# 3. 启动服务
docker-compose up -d

# 4. 等待服务启动（约30秒）
sleep 30

# 5. 应用数据库迁移
docker-compose exec backend alembic upgrade head

# 6. 验证迁移
docker-compose exec backend python test_migration.py

# 7. 创建管理员
docker-compose exec backend python create_admin.py

# 8. 运行安全检查
docker-compose exec backend python scripts/security_check.py
```

### 方法二：不重新构建（快速方法）

如果不想重新构建镜像，可以直接在容器中运行命令：

```bash
cd backend

# 1. 确保服务正在运行
docker-compose up -d

# 2. 应用迁移
docker-compose exec backend alembic upgrade head

# 3. 手动验证（在容器中）
docker-compose exec backend bash -c "
python -c \"
from sqlalchemy import inspect
from app.core.database import engine

inspector = inspect(engine)
columns = [col['name'] for col in inspector.get_columns('users')]
if 'is_admin' in columns:
    print('✓ is_admin字段已存在')
else:
    print('✗ is_admin字段不存在')
\"
"

# 4. 创建管理员
docker-compose exec backend python create_admin.py

# 5. 设置现有用户为管理员
docker-compose exec backend python set_admin.py <username>
```

### 方法三：在宿主机运行（最简单）

如果有Python环境，可以直接在宿主机运行：

```bash
cd backend

# 1. 激活虚拟环境
source .venv/bin/activate  # Linux/Mac
# 或
.venv\Scripts\activate  # Windows

# 2. 应用迁移
alembic upgrade head

# 3. 验证迁移
python test_migration.py

# 4. 创建管理员
python create_admin.py

# 5. 运行安全检查
python scripts/security_check.py
```

## 📋 快速验证清单

### 1. 检查迁移状态

```bash
# 在容器中
docker-compose exec backend alembic current

# 应该显示: 005_is_admin (head)
```

### 2. 检查字段是否存在

```bash
# 方法A: 使用MySQL客户端
docker-compose exec mysql mysql -u ai_user -p ai_assistant -e "DESCRIBE users;"

# 方法B: 使用Python
docker-compose exec backend python -c "
from sqlalchemy import inspect
from app.core.database import engine
inspector = inspect(engine)
columns = [col['name'] for col in inspector.get_columns('users')]
print('is_admin' in columns)
"
```

### 3. 检查管理员用户

```bash
# 查询管理员
docker-compose exec mysql mysql -u ai_user -p ai_assistant -e "
SELECT id, username, is_admin, is_active FROM users WHERE is_admin = 1;
"
```

### 4. 测试管理员权限

```bash
# 1. 登录获取令牌
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "Admin123456"}' \
  | jq -r '.access_token')

# 2. 测试管理员端点
curl -X GET http://localhost:8000/api/v1/system/config \
  -H "Authorization: Bearer $TOKEN"

# 应该返回系统配置，而不是403错误
```

## 🔧 故障排查

### 问题1: 容器中找不到文件

**错误**: `can't open file '/app/test_migration.py'`

**原因**: Docker镜像构建时文件不存在

**解决方案**:
```bash
# 重新构建镜像
docker-compose build --no-cache
docker-compose up -d
```

### 问题2: 数据库连接失败

**错误**: `Access denied for user`

**解决方案**:
```bash
# 1. 检查MySQL服务
docker-compose ps mysql

# 2. 查看MySQL日志
docker-compose logs mysql

# 3. 重启MySQL
docker-compose restart mysql

# 4. 等待MySQL完全启动
sleep 10
```

### 问题3: 迁移已应用但字段不存在

**解决方案**:
```bash
# 1. 检查迁移状态
docker-compose exec backend alembic current

# 2. 如果显示005_is_admin，但字段不存在，手动添加
docker-compose exec mysql mysql -u ai_user -p ai_assistant -e "
ALTER TABLE users ADD COLUMN is_admin TINYINT(1) NOT NULL DEFAULT 0 COMMENT '是否为管理员';
CREATE INDEX ix_users_is_admin ON users(is_admin);
"

# 3. 标记迁移为已完成
docker-compose exec backend alembic stamp 005_is_admin
```

### 问题4: 权限测试失败

**解决方案**:
```bash
# 1. 确认用户是管理员
docker-compose exec mysql mysql -u ai_user -p ai_assistant -e "
UPDATE users SET is_admin = 1 WHERE username = 'admin';
"

# 2. 重新登录获取新令牌
# 3. 再次测试
```

## 📝 完整部署脚本

创建一个自动化部署脚本：

```bash
#!/bin/bash
# deploy_admin_security.sh

set -e  # 遇到错误立即退出

echo "=========================================="
echo "部署管理员权限和安全加固"
echo "=========================================="

# 1. 停止旧服务
echo "1. 停止旧服务..."
docker-compose down

# 2. 重新构建镜像
echo "2. 重新构建镜像..."
docker-compose build --no-cache

# 3. 启动服务
echo "3. 启动服务..."
docker-compose up -d

# 4. 等待服务启动
echo "4. 等待服务启动（30秒）..."
sleep 30

# 5. 检查服务状态
echo "5. 检查服务状态..."
docker-compose ps

# 6. 应用数据库迁移
echo "6. 应用数据库迁移..."
docker-compose exec -T backend alembic upgrade head

# 7. 检查迁移状态
echo "7. 检查迁移状态..."
docker-compose exec -T backend alembic current

# 8. 创建管理员用户
echo "8. 创建管理员用户..."
docker-compose exec -T backend python create_admin.py

# 9. 验证部署
echo "9. 验证部署..."
docker-compose exec -T backend python -c "
from sqlalchemy import inspect
from app.core.database import engine
inspector = inspect(engine)
columns = [col['name'] for col in inspector.get_columns('users')]
if 'is_admin' in columns:
    print('✓ is_admin字段已存在')
    exit(0)
else:
    print('✗ is_admin字段不存在')
    exit(1)
"

echo "=========================================="
echo "✓ 部署完成！"
echo "=========================================="
echo ""
echo "下一步:"
echo "1. 修改默认密码: docker-compose exec backend python -c \"...\""
echo "2. 运行测试: docker-compose exec backend pytest tests/test_admin_permissions.py"
echo "3. 查看日志: docker-compose logs -f backend"
```

使用方法：

```bash
# 赋予执行权限
chmod +x deploy_admin_security.sh

# 运行脚本
./deploy_admin_security.sh
```

## 🎯 推荐流程

**生产环境部署**:

1. **备份数据库**
   ```bash
   docker-compose exec mysql mysqldump -u root -p ai_assistant > backup_$(date +%Y%m%d).sql
   ```

2. **重新构建并部署**
   ```bash
   docker-compose down
   docker-compose build --no-cache
   docker-compose up -d
   sleep 30
   ```

3. **应用迁移**
   ```bash
   docker-compose exec backend alembic upgrade head
   ```

4. **创建管理员**
   ```bash
   docker-compose exec backend python create_admin.py
   ```

5. **修改默认密码**（重要！）
   ```bash
   # 通过API或前端界面修改
   ```

6. **验证功能**
   ```bash
   # 测试管理员登录和权限
   ```

## 📚 相关文档

- [MIGRATION_GUIDE.md](MIGRATION_GUIDE.md) - 迁移详细指南
- [DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md) - 部署检查清单
- [SECURITY_QUICKSTART.md](SECURITY_QUICKSTART.md) - 安全快速配置

---

**最后更新**: 2025-01-16
