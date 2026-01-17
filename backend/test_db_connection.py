"""
测试数据库连接

使用实际的MySQL配置测试数据库连接。
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

# 设置环境变量强制重新加载配置
os.environ['DATABASE_URL'] = 'mysql+pymysql://root:Ly028716@localhost:3306/ai_assistant'

from sqlalchemy import create_engine, text
from sqlalchemy.pool import QueuePool


def test_connection():
    """测试数据库连接"""
    print("=" * 60)
    print("测试MySQL数据库连接")
    print("=" * 60)
    
    # 数据库配置
    database_url = "mysql+pymysql://root:Ly028716@localhost:3306/ai_assistant"
    pool_size = 10
    max_overflow = 20
    pool_recycle = 3600
    
    print(f"\n数据库配置:")
    print(f"  - URL: mysql+pymysql://root:***@localhost:3306/ai_assistant")
    print(f"  - 连接池大小: {pool_size}")
    print(f"  - 最大溢出: {max_overflow}")
    print(f"  - 连接回收时间: {pool_recycle}秒")
    
    try:
        # 创建引擎
        print(f"\n正在创建SQLAlchemy引擎...")
        engine = create_engine(
            database_url,
            poolclass=QueuePool,
            pool_size=pool_size,
            max_overflow=max_overflow,
            pool_pre_ping=True,
            pool_recycle=pool_recycle,
            echo=False,
        )
        print("✓ 引擎创建成功")
        
        # 测试连接
        print(f"\n正在测试数据库连接...")
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1 as test"))
            value = result.scalar()
            print(f"✓ 连接测试成功 (查询结果: {value})")
            
            # 获取数据库版本
            result = conn.execute(text("SELECT VERSION()"))
            version = result.scalar()
            print(f"✓ MySQL版本: {version}")
            
            # 获取当前数据库
            result = conn.execute(text("SELECT DATABASE()"))
            db_name = result.scalar()
            print(f"✓ 当前数据库: {db_name}")
            
            # 测试连接池
            print(f"\n连接池状态:")
            print(f"  - 连接池大小: {engine.pool.size()}")
            print(f"  - 最大溢出: {engine.pool._max_overflow}")
            print(f"  - 当前检出连接数: {engine.pool.checkedout()}")
        
        # 清理
        engine.dispose()
        
        print("\n" + "=" * 60)
        print("数据库连接测试完成")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"\n✗ 连接失败: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    try:
        if test_connection():
            print("\n✓ 所有测试通过")
            sys.exit(0)
        else:
            print("\n✗ 测试失败")
            sys.exit(1)
    except Exception as e:
        print(f"\n✗ 未预期的错误: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
