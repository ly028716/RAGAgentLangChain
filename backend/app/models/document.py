"""
文档模型

定义Document数据库模型，用于存储知识库中的文档信息。
"""

import enum
from datetime import datetime

from sqlalchemy import (Column, DateTime, Enum, ForeignKey, Index, Integer,
                        String, Text)
from sqlalchemy.orm import relationship

from app.core.database import Base


class DocumentStatus(str, enum.Enum):
    """文档处理状态枚举"""

    PROCESSING = "processing"  # 处理中
    COMPLETED = "completed"  # 已完成
    FAILED = "failed"  # 处理失败


class Document(Base):
    """
    文档模型

    存储知识库中的文档信息，包括文件元数据和处理状态。

    字段说明:
        id: 文档唯一标识
        knowledge_base_id: 所属知识库ID（外键）
        filename: 原始文件名
        file_path: 文件存储路径
        file_size: 文件大小（字节）
        file_type: 文件类型（pdf/docx/txt/md）
        status: 处理状态（processing/completed/failed）
        chunk_count: 分块数量
        error_message: 错误信息（处理失败时）
        created_at: 文档上传时间

    关系:
        knowledge_base: 所属知识库

    索引:
        - knowledge_base_id: 用于快速查询知识库的所有文档
        - status: 用于按状态筛选文档
        - created_at: 用于按时间排序
        - (knowledge_base_id, created_at): 复合索引，优化文档列表查询

    需求引用:
        - 需求3.2: 用户上传文档且文件类型为PDF、Word、TXT或Markdown且文件大小不超过10MB
        - 需求3.6: 文档处理成功，更新文档状态为"已完成"并记录分块数量
        - 需求3.7: 文档处理失败，更新文档状态为"失败"并记录详细错误信息
    """

    __tablename__ = "documents"

    # 主键
    id = Column(Integer, primary_key=True, index=True, comment="文档ID")

    # 外键
    knowledge_base_id = Column(
        Integer,
        ForeignKey("knowledge_bases.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="知识库ID",
    )

    # 文件信息
    filename = Column(String(255), nullable=False, comment="原始文件名")
    file_path = Column(String(500), nullable=False, comment="文件存储路径")
    file_size = Column(Integer, nullable=False, comment="文件大小（字节）")
    file_type = Column(String(50), nullable=False, comment="文件类型")

    # 处理状态
    status = Column(
        Enum(
            DocumentStatus,
            name="documentstatus",
            values_callable=lambda enum_cls: [e.value for e in enum_cls],
        ),
        default=DocumentStatus.PROCESSING,
        nullable=False,
        index=True,
        comment="处理状态",
    )
    chunk_count = Column(Integer, default=0, nullable=False, comment="分块数量")
    error_message = Column(Text, nullable=True, comment="错误信息")

    # 时间戳
    created_at = Column(
        DateTime, default=datetime.utcnow, nullable=False, index=True, comment="创建时间"
    )

    # 关系映射
    knowledge_base = relationship("KnowledgeBase", back_populates="documents")

    # 复合索引
    __table_args__ = (
        Index("idx_doc_kb_created", "knowledge_base_id", "created_at"),
        Index("idx_doc_kb_status", "knowledge_base_id", "status"),
        {"comment": "文档表"},
    )

    def __repr__(self) -> str:
        """字符串表示"""
        return f"<Document(id={self.id}, kb_id={self.knowledge_base_id}, filename='{self.filename}', status={self.status.value})>"

    def __str__(self) -> str:
        """用户友好的字符串表示"""
        return f"Document: {self.filename} [{self.status.value}]"
