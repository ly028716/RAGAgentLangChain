"""
Redis连接测试脚本

测试Redis连接配置是否正确，验证基本功能。
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

from app.core.redis import get_redis_client, ping_redis, close_redis, RedisKeys


def test_redis_connection():
    """测试Redis连接"""
    print("=" * 50)
    print("测试Redis连接")
    print("=" * 50)
    
    # 测试连接
    print("\n1. 测试Redis连接...")
    if ping_redis():
        print("✓ Redis连接成功")
    else:
        print("✗ Redis连接失败")
        return False
    
    # 获取Redis客户端
    print("\n2. 获取Redis客户端...")
    try:
        client = get_redis_client()
        print(f"✓ Redis客户端创建成功: {client}")
    except Exception as e:
        print(f"✗ Redis客户端创建失败: {e}")
        return False
    
    # 测试基本操作
    print("\n3. 测试基本操作...")
    try:
        # 设置键值
        test_key = "test:connection"
        test_value = "Hello Redis!"
        client.set(test_key, test_value, ex=60)
        print(f"✓ 设置键值: {test_key} = {test_value}")
        
        # 获取键值
        retrieved_value = client.get(test_key)
        print(f"✓ 获取键值: {test_key} = {retrieved_value}")
        
        # 验证值是否正确
        if retrieved_value == test_value:
            print("✓ 值验证成功")
        else:
            print(f"✗ 值验证失败: 期望 {test_value}, 实际 {retrieved_value}")
            return False
        
        # 删除测试键
        client.delete(test_key)
        print(f"✓ 删除测试键: {test_key}")
        
    except Exception as e:
        print(f"✗ 基本操作测试失败: {e}")
        return False
    
    # 测试键命名空间
    print("\n4. 测试键命名空间...")
    try:
        user_id = 123
        user_key = RedisKeys.format_key(RedisKeys.USER_INFO, user_id=user_id)
        print(f"✓ 用户信息键: {user_key}")
        
        quota_key = RedisKeys.format_key(RedisKeys.USER_QUOTA, user_id=user_id)
        print(f"✓ 用户配额键: {quota_key}")
        
        login_key = RedisKeys.format_key(RedisKeys.LOGIN_ATTEMPTS, username="testuser")
        print(f"✓ 登录尝试键: {login_key}")
        
    except Exception as e:
        print(f"✗ 键命名空间测试失败: {e}")
        return False
    
    # 测试连接池
    print("\n5. 测试连接池...")
    try:
        # 获取连接池信息
        pool_info = client.connection_pool
        print(f"✓ 连接池配置:")
        print(f"  - 主机: {pool_info.connection_kwargs.get('host')}")
        print(f"  - 端口: {pool_info.connection_kwargs.get('port')}")
        print(f"  - 数据库: {pool_info.connection_kwargs.get('db')}")
        print(f"  - 最大连接数: {pool_info.max_connections}")
        
    except Exception as e:
        print(f"✗ 连接池测试失败: {e}")
        return False
    
    print("\n" + "=" * 50)
    print("所有测试通过！")
    print("=" * 50)
    return True


def main():
    """主函数"""
    try:
        success = test_redis_connection()
        if success:
            print("\n✓ Redis配置验证成功")
            sys.exit(0)
        else:
            print("\n✗ Redis配置验证失败")
            sys.exit(1)
    except Exception as e:
        print(f"\n✗ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        # 清理连接
        close_redis()
        print("\n已关闭Redis连接")


if __name__ == "__main__":
    main()
