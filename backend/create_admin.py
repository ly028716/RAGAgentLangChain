#!/usr/bin/env python3
"""创建 admin 管理员用户"""
from sqlalchemy.orm import sessionmaker
from app.core.database import engine
from app.core.security import hash_password
from app.models.user import User
from app.models.user_quota import UserQuota
from datetime import datetime, date

SessionLocal = sessionmaker(bind=engine)
session = SessionLocal()

try:
    # 检查用户是否存在
    existing = session.query(User).filter(User.username == 'admin').first()
    if existing:
        print('✓ admin 用户已存在')
        # 确保是管理员
        if not existing.is_admin:
            existing.is_admin = True
            session.commit()
            print('✓ 已将 admin 用户设置为管理员')
        else:
            print('✓ admin 用户已经是管理员')
    else:
        # 创建管理员用户
        user = User(
            username='admin',
            email='admin@example.com',
            password_hash=hash_password('Admin123456'),
            is_active=True,
            is_admin=True,  # 设置为管理员
            created_at=datetime.utcnow()
        )
        session.add(user)
        session.flush()

        # 创建配额
        quota = UserQuota(
            user_id=user.id,
            monthly_quota=1000000,  # 管理员给予更高配额
            used_quota=0,
            reset_date=date.today().replace(day=1),
            created_at=datetime.utcnow()
        )
        session.add(quota)
        session.commit()
        print('✓ admin 管理员用户创建成功')
        print('  用户名: admin')
        print('  密码: Admin123456')
        print('  权限: 管理员')
        print('  配额: 1,000,000 tokens/月')
        print('\n⚠️  请在生产环境中立即修改默认密码！')
finally:
    session.close()

