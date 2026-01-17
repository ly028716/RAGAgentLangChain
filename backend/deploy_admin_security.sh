#!/bin/bash
# 部署管理员权限和安全加固
# 使用方法: ./deploy_admin_security.sh

set -e  # 遇到错误立即退出

echo "=========================================="
echo "部署管理员权限和安全加固"
echo "=========================================="
echo ""

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 1. 停止旧服务
echo -e "${YELLOW}1. 停止旧服务...${NC}"
docker-compose down
echo -e "${GREEN}✓ 服务已停止${NC}"
echo ""

# 2. 重新构建镜像
echo -e "${YELLOW}2. 重新构建镜像...${NC}"
docker-compose build --no-cache
echo -e "${GREEN}✓ 镜像构建完成${NC}"
echo ""

# 3. 启动服务
echo -e "${YELLOW}3. 启动服务...${NC}"
docker-compose up -d
echo -e "${GREEN}✓ 服务已启动${NC}"
echo ""

# 4. 等待服务启动
echo -e "${YELLOW}4. 等待服务启动（30秒）...${NC}"
for i in {1..30}; do
    echo -n "."
    sleep 1
done
echo ""
echo -e "${GREEN}✓ 等待完成${NC}"
echo ""

# 5. 检查服务状态
echo -e "${YELLOW}5. 检查服务状态...${NC}"
docker-compose ps
echo ""

# 6. 应用数据库迁移
echo -e "${YELLOW}6. 应用数据库迁移...${NC}"
docker-compose exec -T backend alembic upgrade head
echo -e "${GREEN}✓ 迁移已应用${NC}"
echo ""

# 7. 检查迁移状态
echo -e "${YELLOW}7. 检查迁移状态...${NC}"
docker-compose exec -T backend alembic current
echo ""

# 8. 验证is_admin字段
echo -e "${YELLOW}8. 验证is_admin字段...${NC}"
docker-compose exec -T backend python -c "
from sqlalchemy import inspect
from app.core.database import engine

try:
    inspector = inspect(engine)
    columns = [col['name'] for col in inspector.get_columns('users')]
    
    if 'is_admin' in columns:
        print('✓ is_admin字段已存在')
        
        # 检查索引
        indexes = inspector.get_indexes('users')
        has_index = any('is_admin' in str(idx) for idx in indexes)
        if has_index:
            print('✓ is_admin索引已创建')
        else:
            print('⚠ is_admin索引未创建')
    else:
        print('✗ is_admin字段不存在')
        exit(1)
except Exception as e:
    print(f'✗ 验证失败: {e}')
    exit(1)
"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ 字段验证通过${NC}"
else
    echo -e "${RED}✗ 字段验证失败${NC}"
    exit 1
fi
echo ""

# 9. 创建管理员用户
echo -e "${YELLOW}9. 创建管理员用户...${NC}"
docker-compose exec -T backend python create_admin.py
echo ""

# 10. 检查管理员
echo -e "${YELLOW}10. 检查管理员用户...${NC}"
docker-compose exec -T backend python -c "
from app.core.database import SessionLocal
from app.models.user import User

db = SessionLocal()
try:
    admins = db.query(User).filter(User.is_admin == True).all()
    print(f'管理员数量: {len(admins)}')
    for admin in admins:
        status = '激活' if admin.is_active else '停用'
        print(f'  - {admin.username} ({status})')
finally:
    db.close()
"
echo ""

echo "=========================================="
echo -e "${GREEN}✓ 部署完成！${NC}"
echo "=========================================="
echo ""
echo "下一步:"
echo "1. 修改默认密码（生产环境必须！）"
echo "   - 登录系统: http://localhost:8000"
echo "   - 用户名: admin"
echo "   - 密码: Admin123456"
echo ""
echo "2. 运行安全检查:"
echo "   docker-compose exec backend python scripts/security_check.py"
echo ""
echo "3. 运行测试:"
echo "   docker-compose exec backend pytest tests/test_admin_permissions.py -v"
echo ""
echo "4. 查看日志:"
echo "   docker-compose logs -f backend"
echo ""
echo "5. 查看API文档:"
echo "   http://localhost:8000/docs"
echo ""
