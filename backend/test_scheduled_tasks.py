"""
定时任务测试脚本

测试配额重置和清理任务的功能。
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.tasks.quota_tasks import reset_monthly_quotas, reset_single_user_quota
from app.tasks.cleanup_tasks import (
    cleanup_old_login_attempts,
    cleanup_temp_files,
    cleanup_old_api_usage,
    run_all_cleanup_tasks
)


def test_quota_reset():
    """测试配额重置任务"""
    print("\n" + "=" * 60)
    print("测试配额重置任务")
    print("=" * 60)
    
    try:
        result = reset_monthly_quotas()
        print(f"执行结果: {result}")
        
        if result['success']:
            print(f"✓ 成功重置 {result['reset_count']} 个用户的配额")
        else:
            print(f"✗ 重置失败: {result.get('message', '未知错误')}")
    except Exception as e:
        print(f"✗ 测试失败: {str(e)}")


def test_cleanup_login_attempts():
    """测试清理登录记录任务"""
    print("\n" + "=" * 60)
    print("测试清理登录记录任务")
    print("=" * 60)
    
    try:
        result = cleanup_old_login_attempts(days_to_keep=30)
        print(f"执行结果: {result}")
        
        if result['success']:
            print(f"✓ 成功删除 {result['deleted_count']} 条登录记录")
        else:
            print(f"✗ 清理失败: {result.get('message', '未知错误')}")
    except Exception as e:
        print(f"✗ 测试失败: {str(e)}")


def test_cleanup_temp_files():
    """测试清理临时文件任务"""
    print("\n" + "=" * 60)
    print("测试清理临时文件任务")
    print("=" * 60)
    
    try:
        result = cleanup_temp_files(days_to_keep=7)
        print(f"执行结果: {result}")
        
        if result['success']:
            print(f"✓ 成功删除 {result['deleted_files']} 个文件，释放 {result['deleted_size_mb']} MB")
        else:
            print(f"✗ 清理失败: {result.get('message', '未知错误')}")
    except Exception as e:
        print(f"✗ 测试失败: {str(e)}")


def test_cleanup_api_usage():
    """测试清理API使用记录任务"""
    print("\n" + "=" * 60)
    print("测试清理API使用记录任务")
    print("=" * 60)
    
    try:
        result = cleanup_old_api_usage(days_to_keep=90)
        print(f"执行结果: {result}")
        
        if result['success']:
            print(f"✓ 成功删除 {result['deleted_count']} 条API使用记录")
        else:
            print(f"✗ 清理失败: {result.get('message', '未知错误')}")
    except Exception as e:
        print(f"✗ 测试失败: {str(e)}")


def test_all_cleanup_tasks():
    """测试运行所有清理任务"""
    print("\n" + "=" * 60)
    print("测试运行所有清理任务")
    print("=" * 60)
    
    try:
        result = run_all_cleanup_tasks()
        print(f"执行结果: {result}")
        
        if result['all_success']:
            print(f"✓ 所有清理任务成功 ({result['success_count']}/{result['total_count']})")
        else:
            print(f"⚠ 部分任务失败 ({result['success_count']}/{result['total_count']})")
        
        # 打印各任务详情
        for task_name, task_result in result['tasks'].items():
            status = "✓" if task_result.get('success', False) else "✗"
            print(f"  {status} {task_name}: {task_result.get('message', 'N/A')}")
    except Exception as e:
        print(f"✗ 测试失败: {str(e)}")


def main():
    """主测试函数"""
    print("\n" + "=" * 60)
    print("定时任务功能测试")
    print("=" * 60)
    
    # 测试配额重置
    test_quota_reset()
    
    # 测试清理任务
    test_cleanup_login_attempts()
    test_cleanup_temp_files()
    test_cleanup_api_usage()
    
    # 测试运行所有清理任务
    test_all_cleanup_tasks()
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)


if __name__ == "__main__":
    main()
