# 数据库迁移指南

本指南说明如何正确应用is_admin字段的数据库迁移。

## 📋 迁移概述

**迁移文件**: `migrations/versions/005_add_is_admin_field.py`  
**迁移ID**: `005_is_admin`  
**依赖**: `004_user_deletion`

**变更内容**:
- 添加 `is_admin` 字段到 `users` 表
- 创建 `ix_users_is_admin` 索引

## 🔍 前置检查

### 1. 检查数据库连接

确保MySQL服务正在运行，并且配置正确：

```bash
# 检查MySQL服务状态
# Windows (Docker)
docker ps | grep mysql

# Linux
systemctl status mysql
```

### 2. 检查环境配置

确保 `.env` 文件中有正确的数据库配置：

```bash
# 方法1: 使用Docker Compose（推荐）
# .env文件应包含:
MYSQL_USER=ai_user
MYSQL_PASSWORD=ai_password
MYSQL_DATABASE=ai_assistant

# 方法2: 直接连接
# 需要在.env中添加:
DATABASE_URL=mysql+pymysql://ai_user:ai_password@localhost:3306/ai_assistant
```

### 3. 检查当前迁移状态

```bash
cd backend
alembic current
```

应该显示当前版本为 `004_user_deletion` 或更早。

## 🚀 迁移步骤

### 方法一：使用Docker Compose（推荐）

如果使用Docker Compose部署：

```bash
# 1. 确保服务正在运行
cd backend
docker-compose up -d

# 2. 进入backend容器
docker-compose exec backend bash

# 3. 应用迁移
alembic upgrade head

# 4. 验证迁移
python test_migration.py

# 5. 创建管理员
python create_admin.py

# 6. 退出容器
exit
```

### 方法二：本地环境

如果在本地开发环境：

```bash
cd backend

# 1. 激活虚拟环境
# Windows
.venv\Scripts\activate
# Linux/Mac
source .venv/bin/activate

# 2. 确保MySQL正在运行
# 检查连接
mysql -u ai_user -p -e "SELECT 1"

# 3. 应用迁移
alembic upgrade head

# 4. 验证迁移
python test_migration.py

# 5. 创建管理员
python create_admin.py
```

## ✅ 验证迁移

### 1. 使用测试脚本

```bash
python test_migration.py
```

**预期输出**:
```
============================================================
数据库迁移测试
============================================================
============================================================
检查数据库连接...
============================================================
✓ 数据库连接成功

============================================================
检查users表结构...
============================================================
✓ users表存在

表字段 (15个):
  - id                           INTEGER              NOT NULL
  - username                     VARCHAR(50)          NOT NULL
  - email                        VARCHAR(100)         NULL
  - password_hash                VARCHAR(255)         NOT NULL
  - avatar                       VARCHAR(255)         NULL
  - created_at                   DATETIME             NOT NULL
  - updated_at                   DATETIME             NOT NULL
  - last_login                   DATETIME             NULL
  - is_active                    TINYINT(1)           NOT NULL
  - is_admin                     TINYINT(1)           NOT NULL
  ...

✓ is_admin字段已存在
✓ is_admin索引已创建

============================================================
检查管理员用户...
============================================================
总用户数: 1
管理员数: 1

管理员列表:
  - ID: 1, 用户名: admin, 状态: 激活

============================================================
✓ 所有检查通过！
============================================================
```

### 2. 手动验证

```bash
# 连接到MySQL
mysql -u ai_user -p ai_assistant

# 检查字段
DESCRIBE users;

# 检查索引
SHOW INDEX FROM users WHERE Key_name = 'ix_users_is_admin';

# 检查管理员
SELECT id, username, is_admin FROM users WHERE is_admin = 1;

# 退出
exit
```

### 3. 使用Alembic命令

```bash
# 查看当前版本
alembic current

# 应该显示: 005_is_admin (head)

# 查看迁移历史
alembic history

# 应该显示完整的迁移链
```

## 🔧 故障排查

### 问题1: 数据库连接失败

**错误信息**:
```
OperationalError: (1045, "Access denied for user 'user'@'172.19.0.1'")
```

**解决方案**:

1. **检查Docker服务**:
```bash
docker-compose ps
# 确保mysql服务正在运行
```

2. **检查环境变量**:
```bash
# 查看.env文件
cat .env | grep MYSQL

# 确保配置正确
MYSQL_USER=ai_user
MYSQL_PASSWORD=ai_password
MYSQL_DATABASE=ai_assistant
```

3. **重启服务**:
```bash
docker-compose down
docker-compose up -d
```

4. **手动测试连接**:
```bash
docker-compose exec mysql mysql -u ai_user -p
# 输入密码: ai_password
```

### 问题2: 迁移版本冲突

**错误信息**:
```
Multiple head revisions are present
```

**解决方案**:

1. **检查迁移文件**:
```bash
ls -la migrations/versions/
```

2. **确认迁移链**:
```bash
alembic history
```

3. **如果有冲突，合并分支**:
```bash
alembic merge heads -m "merge migrations"
alembic upgrade head
```

### 问题3: 字段已存在

**错误信息**:
```
Duplicate column name 'is_admin'
```

**解决方案**:

字段已经存在，无需再次迁移：

```bash
# 标记迁移为已完成
alembic stamp head

# 验证
python test_migration.py
```

### 问题4: 没有DATABASE_URL

**错误信息**:
```
KeyError: 'DATABASE_URL'
```

**解决方案**:

添加DATABASE_URL到.env文件：

```bash
# 编辑.env文件
echo "DATABASE_URL=mysql+pymysql://ai_user:ai_password@localhost:3306/ai_assistant" >> .env

# 或者使用Docker Compose的环境变量
# 无需手动添加DATABASE_URL
```

## 📝 回滚迁移

如果需要回滚迁移：

```bash
# 回滚到上一个版本
alembic downgrade -1

# 回滚到特定版本
alembic downgrade 004_user_deletion

# 验证
alembic current
```

**注意**: 回滚会删除 `is_admin` 字段和索引！

## 🔄 重新应用迁移

如果需要重新应用迁移：

```bash
# 1. 回滚
alembic downgrade 004_user_deletion

# 2. 重新应用
alembic upgrade head

# 3. 验证
python test_migration.py
```

## 📊 迁移后检查清单

- [ ] 数据库连接成功
- [ ] users表存在
- [ ] is_admin字段已添加
- [ ] ix_users_is_admin索引已创建
- [ ] 测试脚本通过
- [ ] 创建了管理员用户
- [ ] 管理员可以登录
- [ ] 管理员权限验证正常

## 🆘 需要帮助？

1. **运行测试脚本**:
   ```bash
   python test_migration.py
   ```

2. **查看日志**:
   ```bash
   # Docker日志
   docker-compose logs backend
   
   # 应用日志
   tail -f logs/app.log
   ```

3. **检查配置**:
   ```bash
   python scripts/security_check.py
   ```

4. **查看文档**:
   - [ADMIN_SECURITY_IMPLEMENTATION.md](ADMIN_SECURITY_IMPLEMENTATION.md)
   - [SECURITY_QUICKSTART.md](SECURITY_QUICKSTART.md)

---

**最后更新**: 2025-01-16  
**迁移版本**: 005_is_admin
