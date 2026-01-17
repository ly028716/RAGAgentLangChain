#!/usr/bin/env python3
"""
测试数据库迁移

验证is_admin字段迁移是否正确
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import inspect, text
from app.core.database import engine, SessionLocal
from app.models.user import User


def check_database_connection():
    """检查数据库连接"""
    print("=" * 60)
    print("检查数据库连接...")
    print("=" * 60)
    
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            print("✓ 数据库连接成功")
            return True
    except Exception as e:
        print(f"✗ 数据库连接失败: {str(e)}")
        print("\n请确保:")
        print("1. MySQL服务正在运行")
        print("2. .env文件中配置了正确的DATABASE_URL")
        print("3. 数据库已创建")
        print("\n示例配置:")
        print("DATABASE_URL=mysql+pymysql://ai_user:ai_password@localhost:3306/ai_assistant")
        return False


def check_users_table():
    """检查users表结构"""
    print("\n" + "=" * 60)
    print("检查users表结构...")
    print("=" * 60)
    
    try:
        inspector = inspect(engine)
        
        # 检查表是否存在
        if 'users' not in inspector.get_table_names():
            print("✗ users表不存在")
            print("请先运行: alembic upgrade head")
            return False
        
        print("✓ users表存在")
        
        # 获取列信息
        columns = inspector.get_columns('users')
        column_names = [col['name'] for col in columns]
        
        print(f"\n表字段 ({len(column_names)}个):")
        for col in columns:
            nullable = "NULL" if col['nullable'] else "NOT NULL"
            default = f", default={col['default']}" if col.get('default') else ""
            print(f"  - {col['name']:30s} {col['type']!s:20s} {nullable}{default}")
        
        # 检查is_admin字段
        if 'is_admin' in column_names:
            print("\n✓ is_admin字段已存在")
            
            # 检查索引
            indexes = inspector.get_indexes('users')
            has_admin_index = any('is_admin' in idx.get('column_names', []) for idx in indexes)
            
            if has_admin_index:
                print("✓ is_admin索引已创建")
            else:
                print("⚠ is_admin索引未创建")
            
            return True
        else:
            print("\n✗ is_admin字段不存在")
            print("请运行迁移: alembic upgrade head")
            return False
            
    except Exception as e:
        print(f"✗ 检查失败: {str(e)}")
        return False


def check_admin_users():
    """检查管理员用户"""
    print("\n" + "=" * 60)
    print("检查管理员用户...")
    print("=" * 60)
    
    try:
        db = SessionLocal()
        
        # 统计用户
        total_users = db.query(User).count()
        admin_users = db.query(User).filter(User.is_admin == True).count()
        
        print(f"总用户数: {total_users}")
        print(f"管理员数: {admin_users}")
        
        if admin_users == 0:
            print("\n⚠ 没有管理员用户")
            print("请运行: python create_admin.py")
        else:
            print("\n管理员列表:")
            admins = db.query(User).filter(User.is_admin == True).all()
            for admin in admins:
                status = "激活" if admin.is_active else "停用"
                print(f"  - ID: {admin.id}, 用户名: {admin.username}, 状态: {status}")
        
        db.close()
        return True
        
    except Exception as e:
        print(f"✗ 检查失败: {str(e)}")
        return False


def test_admin_field():
    """测试is_admin字段功能"""
    print("\n" + "=" * 60)
    print("测试is_admin字段功能...")
    print("=" * 60)
    
    try:
        db = SessionLocal()
        
        # 测试查询
        print("\n1. 测试查询管理员用户...")
        admins = db.query(User).filter(User.is_admin == True).all()
        print(f"   查询到 {len(admins)} 个管理员")
        
        # 测试查询普通用户
        print("\n2. 测试查询普通用户...")
        normal_users = db.query(User).filter(User.is_admin == False).all()
        print(f"   查询到 {len(normal_users)} 个普通用户")
        
        # 测试字段访问
        if admins:
            print("\n3. 测试字段访问...")
            admin = admins[0]
            print(f"   用户: {admin.username}")
            print(f"   is_admin: {admin.is_admin}")
            print(f"   类型: {type(admin.is_admin)}")
        
        db.close()
        print("\n✓ 所有测试通过")
        return True
        
    except Exception as e:
        print(f"✗ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("数据库迁移测试")
    print("=" * 60)
    
    # 检查数据库连接
    if not check_database_connection():
        sys.exit(1)
    
    # 检查表结构
    if not check_users_table():
        sys.exit(1)
    
    # 检查管理员用户
    check_admin_users()
    
    # 测试字段功能
    if not test_admin_field():
        sys.exit(1)
    
    print("\n" + "=" * 60)
    print("✓ 所有检查通过！")
    print("=" * 60)
    print("\n下一步:")
    print("1. 如果没有管理员用户，运行: python create_admin.py")
    print("2. 运行安全检查: python scripts/security_check.py")
    print("3. 运行测试: pytest tests/test_admin_permissions.py -v")
    print()


if __name__ == "__main__":
    main()
