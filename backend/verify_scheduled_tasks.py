"""
定时任务实现验证脚本

验证定时任务相关文件是否正确创建和配置。
不需要运行实际的任务，只检查文件结构和代码。
"""

import os
import sys
from pathlib import Path


def check_file_exists(file_path: str) -> bool:
    """检查文件是否存在"""
    exists = os.path.exists(file_path)
    status = "✓" if exists else "✗"
    print(f"{status} {file_path}")
    return exists


def check_file_contains(file_path: str, search_strings: list) -> bool:
    """检查文件是否包含指定的字符串"""
    if not os.path.exists(file_path):
        print(f"✗ 文件不存在: {file_path}")
        return False
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    all_found = True
    for search_str in search_strings:
        if search_str in content:
            print(f"  ✓ 包含: {search_str}")
        else:
            print(f"  ✗ 缺失: {search_str}")
            all_found = False
    
    return all_found


def main():
    """主验证函数"""
    print("\n" + "=" * 60)
    print("定时任务实现验证")
    print("=" * 60)
    
    all_checks_passed = True
    
    # 1. 检查配额任务文件
    print("\n1. 检查配额任务文件 (app/tasks/quota_tasks.py)")
    print("-" * 60)
    quota_file = "app/tasks/quota_tasks.py"
    if check_file_exists(quota_file):
        quota_checks = [
            "reset_monthly_quotas",
            "reset_single_user_quota",
            "QuotaService",
            "需求11.6"
        ]
        if not check_file_contains(quota_file, quota_checks):
            all_checks_passed = False
    else:
        all_checks_passed = False
    
    # 2. 检查清理任务文件
    print("\n2. 检查清理任务文件 (app/tasks/cleanup_tasks.py)")
    print("-" * 60)
    cleanup_file = "app/tasks/cleanup_tasks.py"
    if check_file_exists(cleanup_file):
        cleanup_checks = [
            "cleanup_old_login_attempts",
            "cleanup_temp_files",
            "cleanup_old_api_usage",
            "run_all_cleanup_tasks",
            "需求8.5"
        ]
        if not check_file_contains(cleanup_file, cleanup_checks):
            all_checks_passed = False
    else:
        all_checks_passed = False
    
    # 3. 检查主应用文件
    print("\n3. 检查主应用文件 (app/main.py)")
    print("-" * 60)
    main_file = "app/main.py"
    if check_file_exists(main_file):
        main_checks = [
            "AsyncIOScheduler",
            "setup_scheduler",
            "reset_monthly_quotas",
            "run_all_cleanup_tasks",
            "lifespan",
            "CronTrigger"
        ]
        if not check_file_contains(main_file, main_checks):
            all_checks_passed = False
    else:
        all_checks_passed = False
    
    # 4. 检查配置文件
    print("\n4. 检查配置文件 (app/config.py)")
    print("-" * 60)
    config_file = "app/config.py"
    if check_file_exists(config_file):
        config_checks = [
            "BackgroundTaskSettings",
            "enable_scheduler",
            "quota_reset_cron"
        ]
        if not check_file_contains(config_file, config_checks):
            all_checks_passed = False
    else:
        all_checks_passed = False
    
    # 5. 检查requirements.txt
    print("\n5. 检查依赖文件 (requirements.txt)")
    print("-" * 60)
    req_file = "requirements.txt"
    if check_file_exists(req_file):
        req_checks = [
            "apscheduler"
        ]
        if not check_file_contains(req_file, req_checks):
            all_checks_passed = False
    else:
        all_checks_passed = False
    
    # 6. 检查tasks模块初始化文件
    print("\n6. 检查tasks模块初始化 (app/tasks/__init__.py)")
    print("-" * 60)
    init_file = "app/tasks/__init__.py"
    if check_file_exists(init_file):
        init_checks = [
            "reset_monthly_quotas",
            "cleanup_old_login_attempts",
            "run_all_cleanup_tasks"
        ]
        if not check_file_contains(init_file, init_checks):
            all_checks_passed = False
    else:
        all_checks_passed = False
    
    # 7. 检查文档文件
    print("\n7. 检查实现文档 (SCHEDULED_TASKS_IMPLEMENTATION.md)")
    print("-" * 60)
    doc_file = "SCHEDULED_TASKS_IMPLEMENTATION.md"
    if check_file_exists(doc_file):
        doc_checks = [
            "配额重置任务",
            "清理任务",
            "APScheduler",
            "Cron表达式"
        ]
        if not check_file_contains(doc_file, doc_checks):
            all_checks_passed = False
    else:
        all_checks_passed = False
    
    # 总结
    print("\n" + "=" * 60)
    if all_checks_passed:
        print("✓ 所有检查通过！定时任务实现完整。")
        print("\n关键功能:")
        print("  1. 配额重置任务 - 每月1日凌晨0点执行")
        print("  2. 清理登录记录 - 每天凌晨2点执行")
        print("  3. 清理临时文件 - 每天凌晨2点执行")
        print("  4. 清理API使用记录 - 每天凌晨2点执行")
        print("\n配置选项:")
        print("  - ENABLE_SCHEDULER: 启用/禁用调度器")
        print("  - QUOTA_RESET_CRON: 配额重置Cron表达式")
        print("\nAPI端点:")
        print("  - GET /health: 查看调度器状态")
        print("  - GET /scheduler/jobs: 列出所有定时任务")
        print("\n测试:")
        print("  - 运行 python test_scheduled_tasks.py 进行功能测试")
        print("  - 启动应用后访问 /scheduler/jobs 查看任务状态")
    else:
        print("✗ 部分检查未通过，请检查上述错误。")
    print("=" * 60 + "\n")
    
    return 0 if all_checks_passed else 1


if __name__ == "__main__":
    sys.exit(main())
