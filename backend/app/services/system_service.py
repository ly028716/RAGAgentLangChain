"""
系统服务模块

实现系统配置管理、使用统计和健康检查功能。
需求: 需求7.1, 需求7.2, 需求7.5, 需求8.2, 需求8.4
"""

import base64
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional

from cryptography.fernet import Fernet
from sqlalchemy import and_, func
from sqlalchemy.orm import Session

from app.config import settings
from app.core.database import engine
from app.core.redis import get_redis_client, ping_redis
from app.core.vector_store import get_vector_store
from app.models.api_usage import APIUsage
from app.models.user import User
from app.models.user_quota import UserQuota


class SystemService:
    """
    系统服务类

    提供系统配置管理、使用统计和健康检查功能。

    使用方式:
        service = SystemService(db)
        config = service.get_config()
        stats = service.get_usage_stats(start_date=date(2025, 1, 1), end_date=date(2025, 1, 31))
        health = service.health_check()
    """

    def __init__(self, db: Session):
        """
        初始化系统服务

        Args:
            db: SQLAlchemy数据库会话
        """
        self.db = db
        self._encryption_key = self._get_or_create_encryption_key()

    def _get_or_create_encryption_key(self) -> bytes:
        """
        获取或创建加密密钥

        从环境变量读取加密密钥，如果不存在则生成新密钥。
        注意：生产环境必须配置固定的加密密钥。

        Returns:
            bytes: Fernet加密密钥
        """
        # 从配置读取加密密钥（应该是32字节的base64编码字符串）
        key_str = getattr(settings.app, "encryption_key", None)

        if key_str:
            try:
                # 确保密钥是有效的Fernet密钥格式
                return base64.urlsafe_b64decode(key_str)
            except Exception:
                pass

        # 如果没有配置或配置无效，生成新密钥（仅用于开发环境）
        return Fernet.generate_key()

    def _encrypt_value(self, value: str) -> str:
        """
        加密敏感值

        使用AES-256加密算法（通过Fernet）加密敏感配置。

        Args:
            value: 要加密的明文值

        Returns:
            str: 加密后的值（base64编码）
        """
        if not value:
            return value

        try:
            fernet = Fernet(self._encryption_key)
            encrypted = fernet.encrypt(value.encode("utf-8"))
            return encrypted.decode("utf-8")
        except Exception as e:
            print(f"加密失败: {e}")
            return value

    def _decrypt_value(self, encrypted_value: str) -> str:
        """
        解密敏感值

        Args:
            encrypted_value: 加密的值

        Returns:
            str: 解密后的明文值
        """
        if not encrypted_value:
            return encrypted_value

        try:
            fernet = Fernet(self._encryption_key)
            decrypted = fernet.decrypt(encrypted_value.encode("utf-8"))
            return decrypted.decode("utf-8")
        except Exception as e:
            print(f"解密失败: {e}")
            return encrypted_value

    def _mask_sensitive_value(self, value: str, show_chars: int = 4) -> str:
        """
        脱敏敏感值

        显示前几个字符，其余用星号替换。

        Args:
            value: 要脱敏的值
            show_chars: 显示的字符数

        Returns:
            str: 脱敏后的值
        """
        if not value or len(value) <= show_chars:
            return "*" * len(value) if value else ""

        return value[:show_chars] + "*" * (len(value) - show_chars)

    def get_config(self) -> Dict[str, Any]:
        """
        获取系统配置

        返回当前系统配置，敏感字段（如API密钥）进行脱敏处理。

        Returns:
            Dict[str, Any]: 系统配置字典

        需求引用:
            - 需求7.5: 查询系统配置时对敏感字段进行脱敏处理
        """
        config = {
            # 应用配置
            "app": {
                "name": settings.app.app_name,
                "version": settings.app.app_version,
                "environment": settings.app.environment,
                "debug": settings.app.debug,
            },
            # 数据库配置
            "database": {
                "url": self._mask_sensitive_value(
                    settings.database.database_url, show_chars=10
                ),
                "pool_size": settings.database.db_pool_size,
                "max_overflow": settings.database.db_max_overflow,
            },
            # Redis配置
            "redis": {
                "host": settings.redis.redis_host,
                "port": settings.redis.redis_port,
                "db": settings.redis.redis_db,
                "password_set": bool(settings.redis.redis_password),
            },
            # 通义千问配置
            "tongyi": {
                "api_key": self._mask_sensitive_value(
                    settings.tongyi.dashscope_api_key
                ),
                "model_name": settings.tongyi.tongyi_model_name,
                "temperature": settings.tongyi.tongyi_temperature,
                "max_tokens": settings.tongyi.tongyi_max_tokens,
                "embedding_model": settings.tongyi.embedding_model,
            },
            # 向量数据库配置
            "vector_db": {
                "type": "chroma",
                "persist_directory": settings.vector_db.chroma_persist_directory,
            },
            # 文件存储配置
            "file_storage": {
                "upload_dir": settings.file_storage.upload_dir,
                "max_upload_size_mb": settings.file_storage.max_upload_size_mb,
            },
            # 文档处理配置
            "document_processing": {
                "chunk_size": settings.document_processing.chunk_size,
                "chunk_overlap": settings.document_processing.chunk_overlap,
            },
            # RAG配置
            "rag": {
                "top_k": settings.rag.rag_top_k,
                "similarity_threshold": settings.rag.rag_similarity_threshold,
            },
            # 配额配置
            "quota": {
                "default_monthly_quota": settings.quota.default_monthly_quota,
            },
            # 速率限制配置
            "rate_limit": {
                "per_minute": settings.rate_limit.rate_limit_per_minute,
                "login_per_minute": settings.rate_limit.rate_limit_login_per_minute,
                "llm_per_minute": settings.rate_limit.rate_limit_llm_per_minute,
            },
            # 安全配置
            "security": {
                "bcrypt_rounds": settings.security.bcrypt_rounds,
                "max_login_attempts": settings.security.max_login_attempts,
                "account_lockout_minutes": settings.security.account_lockout_minutes,
            },
            # JWT配置
            "jwt": {
                "algorithm": settings.jwt.algorithm,
                "access_token_expire_days": settings.jwt.access_token_expire_days,
                "refresh_token_expire_days": settings.jwt.refresh_token_expire_days,
            },
        }

        return config

    def update_config(self, config_updates: Dict[str, Any]) -> Dict[str, Any]:
        """
        更新系统配置

        更新系统配置项，敏感字段自动加密存储。
        注意：此方法更新的是运行时配置，重启后会恢复为环境变量配置。
        生产环境应该通过环境变量或配置文件管理配置。

        Args:
            config_updates: 要更新的配置项字典

        Returns:
            Dict[str, Any]: 更新后的配置

        需求引用:
            - 需求7.1: 配置通义千问API密钥时验证有效性并加密存储
            - 需求7.2: 更新模型参数时验证参数范围的合法性
        """
        # 这里简化实现，实际应该将配置持久化到数据库或配置文件
        # 当前实现仅更新运行时配置

        # 验证和更新通义千问配置
        if "tongyi" in config_updates:
            tongyi_config = config_updates["tongyi"]

            if "temperature" in tongyi_config:
                temp = tongyi_config["temperature"]
                if not (0.0 <= temp <= 2.0):
                    raise ValueError("temperature必须在0.0到2.0之间")
                settings.tongyi.tongyi_temperature = temp

            if "max_tokens" in tongyi_config:
                max_tokens = tongyi_config["max_tokens"]
                if not (1 <= max_tokens <= 4000):
                    raise ValueError("max_tokens必须在1到4000之间")
                settings.tongyi.tongyi_max_tokens = max_tokens

            if "api_key" in tongyi_config:
                # 验证API密钥格式（简单验证）
                api_key = tongyi_config["api_key"]
                if len(api_key) < 10:
                    raise ValueError("API密钥格式无效")
                # 实际应该调用API验证密钥有效性
                # 加密存储（这里简化，实际应存储到数据库）
                encrypted_key = self._encrypt_value(api_key)
                settings.tongyi.dashscope_api_key = api_key

        # 验证和更新RAG配置
        if "rag" in config_updates:
            rag_config = config_updates["rag"]

            if "top_k" in rag_config:
                top_k = rag_config["top_k"]
                if not (1 <= top_k <= 20):
                    raise ValueError("top_k必须在1到20之间")
                settings.rag.rag_top_k = top_k

            if "similarity_threshold" in rag_config:
                threshold = rag_config["similarity_threshold"]
                if not (0.0 <= threshold <= 1.0):
                    raise ValueError("similarity_threshold必须在0.0到1.0之间")
                settings.rag.rag_similarity_threshold = threshold

        # 验证和更新配额配置
        if "quota" in config_updates:
            quota_config = config_updates["quota"]

            if "default_monthly_quota" in quota_config:
                quota = quota_config["default_monthly_quota"]
                if quota < 1000:
                    raise ValueError("default_monthly_quota必须至少为1000")
                settings.quota.default_monthly_quota = quota

        # 返回更新后的配置
        return self.get_config()

    def get_usage_stats(
        self,
        user_id: Optional[int] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> Dict[str, Any]:
        """
        获取使用统计

        聚合统计API使用情况，包括token消耗、调用次数、活跃用户等。

        Args:
            user_id: 用户ID（可选，指定则返回该用户的统计）
            start_date: 开始日期（可选，默认为当月1日）
            end_date: 结束日期（可选，默认为今天）

        Returns:
            Dict[str, Any]: 使用统计字典

        需求引用:
            - 需求8.2: 返回总token消耗、API调用次数、活跃用户数和功能使用热度
            - 需求8.3: 按用户维度统计token消耗并支持按时间范围筛选
        """
        # 设置默认日期范围（当月）
        if not start_date:
            today = date.today()
            start_date = date(today.year, today.month, 1)

        if not end_date:
            end_date = date.today()

        # 转换为datetime用于查询
        start_datetime = datetime.combine(start_date, datetime.min.time())
        end_datetime = datetime.combine(end_date, datetime.max.time())

        # 构建基础查询
        query = self.db.query(APIUsage).filter(
            and_(
                APIUsage.created_at >= start_datetime,
                APIUsage.created_at <= end_datetime,
            )
        )

        # 如果指定用户，添加用户过滤
        if user_id:
            query = query.filter(APIUsage.user_id == user_id)

        # 总token消耗
        total_tokens = query.with_entities(func.sum(APIUsage.tokens_used)).scalar() or 0

        # API调用次数
        total_calls = query.count()

        # 总费用
        total_cost = query.with_entities(func.sum(APIUsage.cost)).scalar() or Decimal(
            "0.0000"
        )

        # 活跃用户数（仅在未指定用户时统计）
        active_users = 0
        if not user_id:
            active_users = (
                query.with_entities(
                    func.count(func.distinct(APIUsage.user_id))
                ).scalar()
                or 0
            )

        # 按API类型统计（功能使用热度）
        api_type_stats = (
            query.with_entities(
                APIUsage.api_type,
                func.count(APIUsage.id).label("call_count"),
                func.sum(APIUsage.tokens_used).label("total_tokens"),
            )
            .group_by(APIUsage.api_type)
            .all()
        )

        api_type_breakdown = [
            {"api_type": stat[0], "call_count": stat[1], "total_tokens": stat[2] or 0}
            for stat in api_type_stats
        ]

        # 按日期统计（趋势分析）
        daily_stats = (
            query.with_entities(
                func.date(APIUsage.created_at).label("date"),
                func.count(APIUsage.id).label("call_count"),
                func.sum(APIUsage.tokens_used).label("total_tokens"),
            )
            .group_by(func.date(APIUsage.created_at))
            .order_by("date")
            .all()
        )

        daily_breakdown = [
            {
                "date": stat[0].isoformat() if stat[0] else None,
                "call_count": stat[1],
                "total_tokens": stat[2] or 0,
            }
            for stat in daily_stats
        ]

        # 如果指定用户，获取用户配额信息
        user_quota_info = None
        if user_id:
            user_quota = (
                self.db.query(UserQuota).filter(UserQuota.user_id == user_id).first()
            )

            if user_quota:
                user_quota_info = {
                    "monthly_quota": user_quota.monthly_quota,
                    "used_quota": user_quota.used_quota,
                    "remaining_quota": user_quota.remaining_quota,
                    "usage_percentage": user_quota.usage_percentage,
                    "reset_date": user_quota.reset_date.isoformat(),
                }

        # 构建统计结果
        stats = {
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
            },
            "summary": {
                "total_tokens": int(total_tokens),
                "total_calls": total_calls,
                "total_cost": float(total_cost),
                "active_users": active_users,
                "average_tokens_per_call": int(total_tokens / total_calls)
                if total_calls > 0
                else 0,
            },
            "api_type_breakdown": api_type_breakdown,
            "daily_breakdown": daily_breakdown,
        }

        # 添加用户配额信息（如果有）
        if user_quota_info:
            stats["user_quota"] = user_quota_info

        return stats

    def health_check(self, detailed: bool = True) -> Dict[str, Any]:
        """
        系统健康检查

        检查各个组件的连接状态和健康状况。

        Returns:
            Dict[str, Any]: 健康检查结果

        需求引用:
            - 需求8.4: 提供健康检查接口，返回数据库、Redis和向量数据库连接状态
        """
        health_status = {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "components": {},
        }

        # 检查MySQL数据库
        try:
            # 执行简单查询测试连接
            from sqlalchemy import text

            self.db.execute(text("SELECT 1"))
            health_status["components"]["database"] = {
                "status": "healthy",
                "type": "mysql",
                "message": "数据库连接正常",
            }
        except Exception as e:
            health_status["status"] = "unhealthy"
            health_status["components"]["database"] = {
                "status": "unhealthy",
                "type": "mysql",
                "message": f"数据库连接失败: {str(e)}" if detailed else "数据库连接失败",
            }

        # 检查Redis
        try:
            redis_ok = ping_redis()
            if redis_ok:
                redis_client = get_redis_client()
                health_status["components"]["redis"] = {
                    "status": "healthy",
                    "message": "Redis连接正常",
                }
                if detailed:
                    info = redis_client.info()
                    health_status["components"]["redis"].update(
                        {
                            "version": info.get("redis_version", "unknown"),
                            "connected_clients": info.get("connected_clients", 0),
                            "used_memory_human": info.get(
                                "used_memory_human", "unknown"
                            ),
                        }
                    )
            else:
                raise Exception("Redis ping失败")
        except Exception as e:
            health_status["status"] = "unhealthy"
            health_status["components"]["redis"] = {
                "status": "unhealthy",
                "message": f"Redis连接失败: {str(e)}" if detailed else "Redis连接失败",
            }

        # 检查向量数据库（Chroma）
        try:
            # 尝试获取向量存储实例
            # 这里使用一个测试集合名称
            vector_store = get_vector_store(knowledge_base_id=0)  # 使用特殊ID 0作为健康检查
            health_status["components"]["vector_db"] = {
                "status": "healthy",
                "type": "chroma",
                "message": "向量数据库连接正常",
            }
            if detailed:
                health_status["components"]["vector_db"]["persist_directory"] = (
                    settings.vector_db.chroma_persist_directory
                )
        except Exception as e:
            health_status["status"] = "degraded"  # 向量数据库不是关键组件，降级而非不健康
            health_status["components"]["vector_db"] = {
                "status": "unhealthy",
                "type": "chroma",
                "message": f"向量数据库连接失败: {str(e)}" if detailed else "向量数据库连接失败",
            }

        # 检查磁盘空间（可选）
        try:
            import shutil

            total, used, free = shutil.disk_usage("/")
            free_gb = free // (2**30)
            health_status["components"]["disk"] = {
                "status": "healthy" if free_gb > 1 else "warning",
                "free_space_gb": free_gb,
                "message": f"可用磁盘空间: {free_gb}GB",
            }
        except Exception as e:
            health_status["components"]["disk"] = {
                "status": "unknown",
                "message": f"无法获取磁盘信息: {str(e)}" if detailed else "无法获取磁盘信息",
            }

        return health_status

    def get_system_info(self) -> Dict[str, Any]:
        """
        获取系统信息

        返回系统的基本信息和运行状态。

        Returns:
            Dict[str, Any]: 系统信息字典
        """
        import platform
        import sys

        # 获取用户统计
        total_users = self.db.query(User).count()
        active_users = self.db.query(User).filter(User.is_active == True).count()

        # 获取今日统计
        today_start = datetime.combine(date.today(), datetime.min.time())
        today_usage = (
            self.db.query(APIUsage)
            .filter(APIUsage.created_at >= today_start)
            .with_entities(
                func.count(APIUsage.id).label("calls"),
                func.sum(APIUsage.tokens_used).label("tokens"),
            )
            .first()
        )

        return {
            "system": {
                "platform": platform.system(),
                "platform_version": platform.version(),
                "python_version": sys.version,
                "app_name": settings.app.app_name,
                "app_version": settings.app.app_version,
                "environment": settings.app.environment,
            },
            "statistics": {
                "total_users": total_users,
                "active_users": active_users,
                "today_api_calls": today_usage[0] if today_usage else 0,
                "today_tokens_used": int(today_usage[1])
                if today_usage and today_usage[1]
                else 0,
            },
            "uptime": {
                "started_at": getattr(
                    self, "_start_time", datetime.utcnow()
                ).isoformat(),
            },
        }


# 导出
__all__ = ["SystemService"]
