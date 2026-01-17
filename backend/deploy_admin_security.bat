@echo off
REM 部署管理员权限和安全加固 (Windows版本)
REM 使用方法: deploy_admin_security.bat

echo ==========================================
echo 部署管理员权限和安全加固
echo ==========================================
echo.

REM 1. 停止旧服务
echo 1. 停止旧服务...
docker-compose down
if %errorlevel% neq 0 (
    echo 错误: 停止服务失败
    pause
    exit /b 1
)
echo [OK] 服务已停止
echo.

REM 2. 重新构建镜像
echo 2. 重新构建镜像...
docker-compose build --no-cache
if %errorlevel% neq 0 (
    echo 错误: 构建镜像失败
    pause
    exit /b 1
)
echo [OK] 镜像构建完成
echo.

REM 3. 启动服务
echo 3. 启动服务...
docker-compose up -d
if %errorlevel% neq 0 (
    echo 错误: 启动服务失败
    pause
    exit /b 1
)
echo [OK] 服务已启动
echo.

REM 4. 等待服务启动
echo 4. 等待服务启动（30秒）...
timeout /t 30 /nobreak > nul
echo [OK] 等待完成
echo.

REM 5. 检查服务状态
echo 5. 检查服务状态...
docker-compose ps
echo.

REM 6. 应用数据库迁移
echo 6. 应用数据库迁移...
docker-compose exec -T backend alembic upgrade head
if %errorlevel% neq 0 (
    echo 错误: 迁移失败
    pause
    exit /b 1
)
echo [OK] 迁移已应用
echo.

REM 7. 检查迁移状态
echo 7. 检查迁移状态...
docker-compose exec -T backend alembic current
echo.

REM 8. 创建管理员用户
echo 8. 创建管理员用户...
docker-compose exec -T backend python create_admin.py
echo.

echo ==========================================
echo [OK] 部署完成！
echo ==========================================
echo.
echo 下一步:
echo 1. 修改默认密码（生产环境必须！）
echo    - 登录系统: http://localhost:8000
echo    - 用户名: admin
echo    - 密码: Admin123456
echo.
echo 2. 运行安全检查:
echo    docker-compose exec backend python scripts/security_check.py
echo.
echo 3. 运行测试:
echo    docker-compose exec backend pytest tests/test_admin_permissions.py -v
echo.
echo 4. 查看日志:
echo    docker-compose logs -f backend
echo.
echo 5. 查看API文档:
echo    http://localhost:8000/docs
echo.
pause
