"""
设置用户为管理员

使用方法:
    python set_admin.py <username>
    
示例:
    python set_admin.py admin
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.repositories.user_repository import UserRepository


def set_admin(username: str) -> bool:
    """
    设置用户为管理员
    
    Args:
        username: 用户名
    
    Returns:
        bool: 是否成功
    """
    db: Session = SessionLocal()
    
    try:
        user_repo = UserRepository(db)
        user = user_repo.get_by_username(username)
        
        if not user:
            print(f"❌ 用户不存在: {username}")
            return False
        
        if user.is_admin:
            print(f"ℹ️  用户 {username} 已经是管理员")
            return True
        
        # 设置为管理员
        user.is_admin = True
        db.commit()
        
        print(f"✅ 成功将用户 {username} 设置为管理员")
        return True
        
    except Exception as e:
        db.rollback()
        print(f"❌ 设置管理员失败: {str(e)}")
        return False
    finally:
        db.close()


def revoke_admin(username: str) -> bool:
    """
    撤销用户的管理员权限
    
    Args:
        username: 用户名
    
    Returns:
        bool: 是否成功
    """
    db: Session = SessionLocal()
    
    try:
        user_repo = UserRepository(db)
        user = user_repo.get_by_username(username)
        
        if not user:
            print(f"❌ 用户不存在: {username}")
            return False
        
        if not user.is_admin:
            print(f"ℹ️  用户 {username} 不是管理员")
            return True
        
        # 撤销管理员权限
        user.is_admin = False
        db.commit()
        
        print(f"✅ 成功撤销用户 {username} 的管理员权限")
        return True
        
    except Exception as e:
        db.rollback()
        print(f"❌ 撤销管理员权限失败: {str(e)}")
        return False
    finally:
        db.close()


def list_admins() -> None:
    """列出所有管理员用户"""
    db: Session = SessionLocal()
    
    try:
        # 查询所有管理员
        admins = db.query(User).filter(User.is_admin == True).all()
        
        if not admins:
            print("ℹ️  当前没有管理员用户")
            return
        
        print(f"\n📋 管理员列表 (共 {len(admins)} 个):")
        print("-" * 60)
        for admin in admins:
            status = "✅ 激活" if admin.is_active else "❌ 停用"
            print(f"  ID: {admin.id:4d} | 用户名: {admin.username:20s} | {status}")
        print("-" * 60)
        
    except Exception as e:
        print(f"❌ 查询管理员列表失败: {str(e)}")
    finally:
        db.close()


if __name__ == "__main__":
    from app.models.user import User
    
    if len(sys.argv) < 2:
        print("使用方法:")
        print("  设置管理员:   python set_admin.py <username>")
        print("  撤销管理员:   python set_admin.py --revoke <username>")
        print("  列出管理员:   python set_admin.py --list")
        print("\n示例:")
        print("  python set_admin.py admin")
        print("  python set_admin.py --revoke testuser")
        print("  python set_admin.py --list")
        sys.exit(1)
    
    if sys.argv[1] == "--list":
        list_admins()
    elif sys.argv[1] == "--revoke":
        if len(sys.argv) < 3:
            print("❌ 请指定要撤销管理员权限的用户名")
            sys.exit(1)
        username = sys.argv[2]
        success = revoke_admin(username)
        sys.exit(0 if success else 1)
    else:
        username = sys.argv[1]
        success = set_admin(username)
        sys.exit(0 if success else 1)
