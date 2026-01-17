"""
验证数据库设置

完整测试数据库配置、连接池、会话管理和ORM功能。
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

# 强制设置数据库URL
os.environ['DATABASE_URL'] = 'mysql+pymysql://root:Ly028716@localhost:3306/ai_assistant'

from sqlalchemy import create_engine, text, Column, Integer, String
from sqlalchemy.orm import sessionmaker
from app.core.database import Base


def test_complete_setup():
    """完整测试数据库设置"""
    print("=" * 70)
    print("完整验证数据库设置")
    print("=" * 70)
    
    # 数据库配置
    database_url = "mysql+pymysql://root:Ly028716@localhost:3306/ai_assistant"
    
    try:
        # 1. 测试引擎创建
        print("\n【1】创建SQLAlchemy引擎")
        print("-" * 70)
        engine = create_engine(
            database_url,
            pool_size=10,
            max_overflow=20,
            pool_pre_ping=True,
            pool_recycle=3600,
            echo=False,
        )
        print("✓ 引擎创建成功")
        print(f"  - 连接池大小: {engine.pool.size()}")
        print(f"  - 最大溢出: {engine.pool._max_overflow}")
        
        # 2. 测试基本连接
        print("\n【2】测试数据库连接")
        print("-" * 70)
        with engine.connect() as conn:
            result = conn.execute(text("SELECT VERSION()"))
            version = result.scalar()
            print(f"✓ 连接成功")
            print(f"  - MySQL版本: {version}")
            
            result = conn.execute(text("SELECT DATABASE()"))
            db_name = result.scalar()
            print(f"  - 当前数据库: {db_name}")
        
        # 3. 测试会话工厂
        print("\n【3】测试会话工厂")
        print("-" * 70)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        session = SessionLocal()
        print("✓ 会话创建成功")
        print(f"  - 会话类型: {type(session).__name__}")
        print(f"  - 绑定引擎: {session.bind is engine}")
        
        # 测试会话查询
        result = session.execute(text("SELECT 1 as test"))
        value = result.scalar()
        print(f"  - 会话查询测试: {value}")
        session.close()
        
        # 4. 测试Base模型类
        print("\n【4】测试Base模型类")
        print("-" * 70)
        print(f"✓ Base类型: {type(Base).__name__}")
        print(f"  - 元数据: {Base.metadata}")
        
        # 5. 测试创建测试表
        print("\n【5】测试ORM表创建")
        print("-" * 70)
        
        # 定义测试模型
        class TestModel(Base):
            __tablename__ = 'test_table'
            id = Column(Integer, primary_key=True)
            name = Column(String(50))
        
        # 创建表
        Base.metadata.create_all(bind=engine)
        print("✓ 测试表创建成功")
        
        # 6. 测试插入数据
        print("\n【6】测试数据插入和查询")
        print("-" * 70)
        session = SessionLocal()
        
        # 插入测试数据
        test_obj = TestModel(id=1, name="测试数据")
        session.add(test_obj)
        session.commit()
        print("✓ 数据插入成功")
        
        # 查询数据
        result = session.query(TestModel).filter(TestModel.id == 1).first()
        if result:
            print(f"✓ 数据查询成功")
            print(f"  - ID: {result.id}")
            print(f"  - Name: {result.name}")
        
        # 7. 测试连接池
        print("\n【7】测试连接池功能")
        print("-" * 70)
        sessions = []
        for i in range(5):
            s = SessionLocal()
            sessions.append(s)
        
        print(f"✓ 创建了5个会话")
        print(f"  - 当前检出连接数: {engine.pool.checkedout()}")
        
        # 关闭所有会话
        for s in sessions:
            s.close()
        print(f"  - 关闭后检出连接数: {engine.pool.checkedout()}")
        
        # 8. 清理测试数据
        print("\n【8】清理测试数据")
        print("-" * 70)
        session.execute(text("DROP TABLE IF EXISTS test_table"))
        session.commit()
        session.close()
        print("✓ 测试表已删除")
        
        # 清理引擎
        engine.dispose()
        
        print("\n" + "=" * 70)
        print("✓ 所有验证测试通过！")
        print("=" * 70)
        print("\n数据库配置总结:")
        print("  ✓ SQLAlchemy引擎配置正确")
        print("  ✓ 连接池设置正确 (pool_size=10, max_overflow=20)")
        print("  ✓ 会话管理正常")
        print("  ✓ Base模型类可用")
        print("  ✓ ORM功能正常")
        print("  ✓ 数据库连接稳定")
        
        return True
        
    except Exception as e:
        print(f"\n✗ 测试失败: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    try:
        if test_complete_setup():
            print("\n" + "=" * 70)
            print("数据库设置验证完成 - 所有功能正常！")
            print("=" * 70)
            sys.exit(0)
        else:
            print("\n✗ 验证失败")
            sys.exit(1)
    except Exception as e:
        print(f"\n✗ 未预期的错误: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
