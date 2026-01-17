"""
后台任务模块

提供文档处理、配额重置、数据清理等后台任务功能。
"""

from app.tasks.document_tasks import (
    DocumentProcessingTask,
    DocumentProcessingQueue,
    process_document_task,
    process_document_sync,
    get_document_queue,
)

from app.tasks.quota_tasks import (
    reset_monthly_quotas,
    reset_single_user_quota,
)

from app.tasks.cleanup_tasks import (
    cleanup_old_login_attempts,
    cleanup_temp_files,
    cleanup_old_api_usage,
    run_all_cleanup_tasks,
)

__all__ = [
    # 文档处理任务
    'DocumentProcessingTask',
    'DocumentProcessingQueue',
    'process_document_task',
    'process_document_sync',
    'get_document_queue',
    # 配额任务
    'reset_monthly_quotas',
    'reset_single_user_quota',
    # 清理任务
    'cleanup_old_login_attempts',
    'cleanup_temp_files',
    'cleanup_old_api_usage',
    'run_all_cleanup_tasks',
]
