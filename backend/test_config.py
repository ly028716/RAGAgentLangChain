"""
配置模块测试脚本
用于验证配置加载和验证功能
"""

import sys
import os

# 添加app目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from app.config import settings


def test_config_loading():
    """测试配置加载"""
    print("=" * 60)
    print("配置模块测试")
    print("=" * 60)
    
    # 测试应用配置
    print("\n[应用配置]")
    print(f"应用名称: {settings.app.app_name}")
    print(f"应用版本: {settings.app.app_version}")
    print(f"运行环境: {settings.app.environment}")
    print(f"调试模式: {settings.app.debug}")
    print(f"服务器地址: {settings.app.host}:{settings.app.port}")
    
    # 测试数据库配置
    print("\n[数据库配置]")
    print(f"数据库URL: {settings.database.database_url}")
    print(f"连接池大小: {settings.database.db_pool_size}")
    print(f"最大溢出: {settings.database.db_max_overflow}")
    print(f"连接回收时间: {settings.database.db_pool_recycle}秒")
    
    # 测试Redis配置
    print("\n[Redis配置]")
    print(f"Redis主机: {settings.redis.redis_host}")
    print(f"Redis端口: {settings.redis.redis_port}")
    print(f"Redis数据库: {settings.redis.redis_db}")
    print(f"Redis URL: {settings.redis.redis_url}")
    
    # 测试JWT配置
    print("\n[JWT配置]")
    print(f"算法: {settings.jwt.algorithm}")
    print(f"访问令牌有效期: {settings.jwt.access_token_expire_days}天")
    print(f"刷新令牌有效期: {settings.jwt.refresh_token_expire_days}天")
    print(f"密钥长度: {len(settings.jwt.secret_key)}字符")
    
    # 测试安全配置
    print("\n[安全配置]")
    print(f"Bcrypt工作因子: {settings.security.bcrypt_rounds}")
    print(f"最大登录尝试: {settings.security.max_login_attempts}次")
    print(f"账户锁定时长: {settings.security.account_lockout_minutes}分钟")
    
    # 测试通义千问配置
    print("\n[通义千问配置]")
    print(f"模型名称: {settings.tongyi.tongyi_model_name}")
    print(f"温度参数: {settings.tongyi.tongyi_temperature}")
    print(f"最大tokens: {settings.tongyi.tongyi_max_tokens}")
    print(f"嵌入模型: {settings.tongyi.embedding_model}")
    
    # 测试文件存储配置
    print("\n[文件存储配置]")
    print(f"上传目录: {settings.file_storage.upload_dir}")
    print(f"最大上传大小: {settings.file_storage.max_upload_size_mb}MB")
    print(f"最大上传大小(字节): {settings.file_storage.max_upload_size_bytes}")
    
    # 测试文档处理配置
    print("\n[文档处理配置]")
    print(f"分块大小: {settings.document_processing.chunk_size}")
    print(f"分块重叠: {settings.document_processing.chunk_overlap}")
    
    # 测试RAG配置
    print("\n[RAG配置]")
    print(f"检索文档数: {settings.rag.rag_top_k}")
    print(f"相似度阈值: {settings.rag.rag_similarity_threshold}")
    
    # 测试配额配置
    print("\n[配额配置]")
    print(f"默认月度配额: {settings.quota.default_monthly_quota} tokens")
    
    # 测试速率限制配置
    print("\n[速率限制配置]")
    print(f"普通API限制: {settings.rate_limit.rate_limit_per_minute}次/分钟")
    print(f"登录API限制: {settings.rate_limit.rate_limit_login_per_minute}次/分钟")
    print(f"LLM调用限制: {settings.rate_limit.rate_limit_llm_per_minute}次/分钟")
    
    # 测试日志配置
    print("\n[日志配置]")
    print(f"日志级别: {settings.logging.log_level}")
    print(f"日志文件: {settings.logging.log_file}")
    print(f"日志最大大小: {settings.logging.log_max_bytes / 1024 / 1024}MB")
    print(f"日志备份数: {settings.logging.log_backup_count}")
    
    # 测试CORS配置
    print("\n[CORS配置]")
    print(f"允许的源: {settings.cors.origins_list}")
    print(f"允许凭证: {settings.cors.cors_allow_credentials}")
    
    # 测试配置摘要
    print("\n[配置摘要]")
    summary = settings.get_config_summary()
    for key, value in summary.items():
        print(f"{key}: {value}")
    
    # 测试配置验证
    print("\n[配置验证]")
    is_valid = settings.validate_all()
    print(f"配置验证结果: {'通过' if is_valid else '失败'}")
    
    print("\n" + "=" * 60)
    print("配置模块测试完成")
    print("=" * 60)


if __name__ == "__main__":
    try:
        test_config_loading()
    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
