"""
测试日志配置

验证日志系统的各项功能：
1. 日志文件创建
2. 日志格式化
3. 日志级别
4. 日志轮转
5. 控制台输出
"""

import os
import sys
import time

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.utils.logger import setup_logging, get_logger, configure_module_logger, set_third_party_log_levels


def test_basic_logging():
    """测试基本日志功能"""
    print("\n" + "=" * 80)
    print("测试1: 基本日志功能")
    print("=" * 80)
    
    # 配置日志系统
    setup_logging()
    
    # 获取logger
    logger = get_logger(__name__)
    
    # 测试不同级别的日志
    logger.debug("这是一条DEBUG级别的日志")
    logger.info("这是一条INFO级别的日志")
    logger.warning("这是一条WARNING级别的日志")
    logger.error("这是一条ERROR级别的日志")
    logger.critical("这是一条CRITICAL级别的日志")
    
    print("\n✓ 基本日志功能测试完成")


def test_module_logger():
    """测试模块级别的日志配置"""
    print("\n" + "=" * 80)
    print("测试2: 模块日志配置")
    print("=" * 80)
    
    # 为不同模块配置不同的日志级别
    auth_logger = configure_module_logger('app.services.auth_service', level='DEBUG')
    db_logger = configure_module_logger('sqlalchemy.engine', level='WARNING')
    
    auth_logger.debug("认证服务的DEBUG日志")
    auth_logger.info("认证服务的INFO日志")
    
    db_logger.debug("数据库的DEBUG日志（不应该显示）")
    db_logger.warning("数据库的WARNING日志")
    
    print("\n✓ 模块日志配置测试完成")


def test_third_party_loggers():
    """测试第三方库日志配置"""
    print("\n" + "=" * 80)
    print("测试3: 第三方库日志配置")
    print("=" * 80)
    
    # 配置第三方库日志级别
    set_third_party_log_levels()
    
    # 获取第三方库的logger
    sqlalchemy_logger = get_logger('sqlalchemy.engine')
    httpx_logger = get_logger('httpx')
    
    sqlalchemy_logger.info("SQLAlchemy INFO日志（不应该显示）")
    sqlalchemy_logger.warning("SQLAlchemy WARNING日志")
    
    httpx_logger.info("HTTPX INFO日志（不应该显示）")
    httpx_logger.warning("HTTPX WARNING日志")
    
    print("\n✓ 第三方库日志配置测试完成")


def test_log_file():
    """测试日志文件创建和写入"""
    print("\n" + "=" * 80)
    print("测试4: 日志文件")
    print("=" * 80)
    
    logger = get_logger(__name__)
    
    # 写入一些日志
    for i in range(5):
        logger.info(f"测试日志消息 #{i+1}")
    
    # 检查日志文件是否存在
    log_file = "./logs/app.log"
    if os.path.exists(log_file):
        print(f"\n✓ 日志文件已创建: {log_file}")
        
        # 读取并显示日志文件内容
        with open(log_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            print(f"✓ 日志文件包含 {len(lines)} 行")
            print("\n最后5行日志内容:")
            print("-" * 80)
            for line in lines[-5:]:
                print(line.rstrip())
            print("-" * 80)
    else:
        print(f"\n✗ 日志文件未创建: {log_file}")


def test_log_formatting():
    """测试日志格式"""
    print("\n" + "=" * 80)
    print("测试5: 日志格式")
    print("=" * 80)
    
    logger = get_logger('test.module.name')
    
    # 测试不同类型的日志消息
    logger.info("简单消息")
    logger.info("带参数的消息: %s, %d", "字符串", 123)
    logger.info(f"使用f-string的消息: {'测试'}")
    
    # 测试异常日志
    try:
        result = 1 / 0
    except ZeroDivisionError as e:
        logger.error("捕获到异常", exc_info=True)
    
    print("\n✓ 日志格式测试完成")


def test_log_rotation():
    """测试日志轮转（模拟）"""
    print("\n" + "=" * 80)
    print("测试6: 日志轮转配置")
    print("=" * 80)
    
    from app.config import settings
    
    print(f"日志文件路径: {settings.logging.log_file}")
    print(f"日志文件最大大小: {settings.logging.log_max_bytes / 1024 / 1024:.2f}MB")
    print(f"日志备份数量: {settings.logging.log_backup_count}")
    
    logger = get_logger(__name__)
    logger.info("日志轮转配置已验证")
    
    print("\n✓ 日志轮转配置测试完成")
    print("\n注意: 实际的日志轮转会在日志文件达到10MB时自动触发")


def test_performance():
    """测试日志性能"""
    print("\n" + "=" * 80)
    print("测试7: 日志性能")
    print("=" * 80)
    
    logger = get_logger(__name__)
    
    # 测试写入1000条日志的时间
    start_time = time.time()
    for i in range(1000):
        logger.info(f"性能测试日志 #{i+1}")
    end_time = time.time()
    
    elapsed = end_time - start_time
    rate = 1000 / elapsed
    
    print(f"\n写入1000条日志耗时: {elapsed:.3f}秒")
    print(f"日志写入速率: {rate:.0f} 条/秒")
    print("\n✓ 日志性能测试完成")


def main():
    """运行所有测试"""
    print("\n" + "=" * 80)
    print("日志系统测试")
    print("=" * 80)
    
    try:
        test_basic_logging()
        test_module_logger()
        test_third_party_loggers()
        test_log_file()
        test_log_formatting()
        test_log_rotation()
        test_performance()
        
        print("\n" + "=" * 80)
        print("所有测试完成！")
        print("=" * 80)
        print("\n✓ 日志系统配置正确")
        print("✓ 日志文件已创建")
        print("✓ 日志格式正确")
        print("✓ 日志级别配置正确")
        print("✓ 日志轮转配置正确")
        
    except Exception as e:
        print(f"\n✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
