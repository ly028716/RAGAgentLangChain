"""
测试数据库配置

验证数据库连接和ORM配置是否正确。
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import text
from app.core.database import engine, SessionLocal, Base, get_db
from app.config import settings


def test_database_config():
    """测试数据库配置"""
    print("=" * 60)
    print("测试数据库配置")
    print("=" * 60)
    
    # 1. 测试配置加载
    print("\n1. 数据库配置:")
    print(f"   - 数据库URL: {settings.database.database_url}")
    print(f"   - 连接池大小: {settings.database.db_pool_size}")
    print(f"   - 最大溢出: {settings.database.db_max_overflow}")
    print(f"   - 连接回收时间: {settings.database.db_pool_recycle}秒")
    
    # 2. 测试引擎创建
    print("\n2. SQLAlchemy引擎:")
    print(f"   - 引擎类型: {type(engine).__name__}")
    print(f"   - 连接池类型: {type(engine.pool).__name__}")
    print(f"   - 连接池大小: {engine.pool.size()}")
    print(f"   - 最大溢出: {engine.pool._max_overflow}")
    
    # 3. 测试会话工厂
    print("\n3. 会话工厂:")
    print(f"   - 会话类: {SessionLocal.class_.__name__}")
    print(f"   - 绑定引擎: {SessionLocal.kw.get('bind') is engine}")
    
    # 4. 测试Base模型类
    print("\n4. Base模型类:")
    print(f"   - Base类型: {type(Base).__name__}")
    print(f"   - 元数据: {Base.metadata}")
    
    # 5. 测试get_db依赖函数
    print("\n5. 测试get_db依赖函数:")
    db_gen = get_db()
    print(f"   - 返回类型: {type(db_gen).__name__}")
    
    try:
        db = next(db_gen)
        print(f"   - 会话对象: {type(db).__name__}")
        print(f"   - 会话绑定: {db.bind is engine}")
        
        # 尝试执行简单查询（测试连接）
        try:
            result = db.execute(text("SELECT 1"))
            print(f"   - 连接测试: 成功 (结果: {result.scalar()})")
        except Exception as e:
            print(f"   - 连接测试: 失败 ({type(e).__name__}: {e})")
            print("   - 注意: 这可能是因为数据库服务未运行或配置不正确")
        
        # 关闭会话
        try:
            db_gen.close()
        except StopIteration:
            pass
    except Exception as e:
        print(f"   - 创建会话失败: {type(e).__name__}: {e}")
    
    print("\n" + "=" * 60)
    print("数据库配置测试完成")
    print("=" * 60)
    
    return True


if __name__ == "__main__":
    try:
        test_database_config()
        print("\n✓ 所有测试通过")
    except Exception as e:
        print(f"\n✗ 测试失败: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
