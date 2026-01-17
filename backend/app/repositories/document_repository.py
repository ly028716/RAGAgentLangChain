"""
文档数据访问层（Repository）

封装文档相关的数据库操作，提供统一的数据访问接口。
实现CRUD操作、状态更新和查询功能。

需求引用:
    - 需求3.2: 用户上传文档且文件类型为PDF、Word、TXT或Markdown且文件大小不超过10MB
    - 需求3.10: 用户查询文档处理状态，返回文档的当前状态、处理进度百分比和错误信息
"""

from typing import Optional, List, Tuple
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.models.document import Document, DocumentStatus


class DocumentRepository:
    """
    文档Repository类
    
    提供文档数据的CRUD操作和查询功能。
    支持状态更新、分页查询和按状态筛选。
    
    使用方式:
        repo = DocumentRepository(db)
        doc = repo.create(
            knowledge_base_id=1,
            filename="document.pdf",
            file_path="/uploads/document.pdf",
            file_size=1024000,
            file_type="pdf"
        )
        repo.update_status(doc.id, DocumentStatus.COMPLETED, chunk_count=50)
    """
    
    def __init__(self, db: Session):
        """
        初始化Repository
        
        Args:
            db: SQLAlchemy数据库会话
        """
        self.db = db
    
    def create(
        self,
        knowledge_base_id: int,
        filename: str,
        file_path: str,
        file_size: int,
        file_type: str
    ) -> Document:
        """
        创建新文档记录
        
        创建时状态默认为"处理中"。
        
        Args:
            knowledge_base_id: 知识库ID
            filename: 原始文件名
            file_path: 文件存储路径
            file_size: 文件大小（字节）
            file_type: 文件类型（pdf/docx/txt/md）
        
        Returns:
            Document: 创建的文档对象
        """
        document = Document(
            knowledge_base_id=knowledge_base_id,
            filename=filename,
            file_path=file_path,
            file_size=file_size,
            file_type=file_type,
            status=DocumentStatus.PROCESSING
        )
        self.db.add(document)
        self.db.commit()
        self.db.refresh(document)
        return document
    
    def get_by_id(self, document_id: int) -> Optional[Document]:
        """
        根据ID获取文档
        
        Args:
            document_id: 文档ID
        
        Returns:
            Optional[Document]: 文档对象，不存在则返回None
        """
        return self.db.query(Document).filter(
            Document.id == document_id
        ).first()
    
    def get_by_id_and_kb(
        self,
        document_id: int,
        knowledge_base_id: int
    ) -> Optional[Document]:
        """
        根据ID和知识库ID获取文档
        
        Args:
            document_id: 文档ID
            knowledge_base_id: 知识库ID
        
        Returns:
            Optional[Document]: 文档对象，不存在或不属于该知识库则返回None
        """
        return self.db.query(Document).filter(
            Document.id == document_id,
            Document.knowledge_base_id == knowledge_base_id
        ).first()

    
    def get_by_knowledge_base(
        self,
        knowledge_base_id: int,
        skip: int = 0,
        limit: int = 20
    ) -> Tuple[List[Document], int]:
        """
        获取知识库的文档列表（分页）
        
        按创建时间倒序排列，返回文档列表和总数。
        
        Args:
            knowledge_base_id: 知识库ID
            skip: 跳过的记录数
            limit: 返回的最大记录数
        
        Returns:
            Tuple[List[Document], int]: (文档列表, 总数)
        """
        query = self.db.query(Document).filter(
            Document.knowledge_base_id == knowledge_base_id
        )
        
        # 获取总数
        total = query.count()
        
        # 按创建时间倒序排列并分页
        documents = query.order_by(
            desc(Document.created_at)
        ).offset(skip).limit(limit).all()
        
        return documents, total
    
    def get_all_by_knowledge_base(
        self,
        knowledge_base_id: int
    ) -> List[Document]:
        """
        获取知识库的所有文档（不分页）
        
        Args:
            knowledge_base_id: 知识库ID
        
        Returns:
            List[Document]: 文档列表
        """
        return self.db.query(Document).filter(
            Document.knowledge_base_id == knowledge_base_id
        ).order_by(desc(Document.created_at)).all()
    
    def get_by_status(
        self,
        knowledge_base_id: int,
        status: DocumentStatus,
        skip: int = 0,
        limit: int = 20
    ) -> Tuple[List[Document], int]:
        """
        根据状态获取知识库的文档列表（分页）
        
        Args:
            knowledge_base_id: 知识库ID
            status: 文档状态
            skip: 跳过的记录数
            limit: 返回的最大记录数
        
        Returns:
            Tuple[List[Document], int]: (文档列表, 总数)
        """
        query = self.db.query(Document).filter(
            Document.knowledge_base_id == knowledge_base_id,
            Document.status == status
        )
        
        total = query.count()
        
        documents = query.order_by(
            desc(Document.created_at)
        ).offset(skip).limit(limit).all()
        
        return documents, total
    
    def get_processing_documents(
        self,
        skip: int = 0,
        limit: int = 100
    ) -> List[Document]:
        """
        获取所有处理中的文档
        
        用于后台任务查询需要处理的文档。
        
        Args:
            skip: 跳过的记录数
            limit: 返回的最大记录数
        
        Returns:
            List[Document]: 处理中的文档列表
        """
        return self.db.query(Document).filter(
            Document.status == DocumentStatus.PROCESSING
        ).order_by(Document.created_at).offset(skip).limit(limit).all()
    
    def update_status(
        self,
        document_id: int,
        status: DocumentStatus,
        chunk_count: Optional[int] = None,
        error_message: Optional[str] = None
    ) -> Optional[Document]:
        """
        更新文档处理状态
        
        Args:
            document_id: 文档ID
            status: 新状态
            chunk_count: 分块数量（处理完成时设置）
            error_message: 错误信息（处理失败时设置）
        
        Returns:
            Optional[Document]: 更新后的文档对象，文档不存在则返回None
        """
        document = self.get_by_id(document_id)
        if not document:
            return None
        
        document.status = status
        
        if chunk_count is not None:
            document.chunk_count = chunk_count
        
        if error_message is not None:
            document.error_message = error_message
        
        self.db.commit()
        self.db.refresh(document)
        return document
    
    def mark_completed(
        self,
        document_id: int,
        chunk_count: int
    ) -> Optional[Document]:
        """
        标记文档处理完成
        
        Args:
            document_id: 文档ID
            chunk_count: 分块数量
        
        Returns:
            Optional[Document]: 更新后的文档对象，文档不存在则返回None
        """
        return self.update_status(
            document_id,
            DocumentStatus.COMPLETED,
            chunk_count=chunk_count
        )
    
    def mark_failed(
        self,
        document_id: int,
        error_message: str
    ) -> Optional[Document]:
        """
        标记文档处理失败
        
        Args:
            document_id: 文档ID
            error_message: 错误信息
        
        Returns:
            Optional[Document]: 更新后的文档对象，文档不存在则返回None
        """
        return self.update_status(
            document_id,
            DocumentStatus.FAILED,
            error_message=error_message
        )

    
    def delete(self, document_id: int) -> bool:
        """
        删除文档
        
        Args:
            document_id: 文档ID
        
        Returns:
            bool: 删除成功返回True，文档不存在返回False
        """
        document = self.get_by_id(document_id)
        if not document:
            return False
        
        self.db.delete(document)
        self.db.commit()
        return True
    
    def delete_by_kb(
        self,
        document_id: int,
        knowledge_base_id: int
    ) -> bool:
        """
        删除指定知识库中的文档
        
        Args:
            document_id: 文档ID
            knowledge_base_id: 知识库ID（用于权限验证）
        
        Returns:
            bool: 删除成功返回True，文档不存在或不属于该知识库返回False
        """
        document = self.get_by_id_and_kb(document_id, knowledge_base_id)
        if not document:
            return False
        
        self.db.delete(document)
        self.db.commit()
        return True
    
    def count_by_knowledge_base(self, knowledge_base_id: int) -> int:
        """
        获取知识库的文档总数
        
        Args:
            knowledge_base_id: 知识库ID
        
        Returns:
            int: 文档总数
        """
        return self.db.query(Document).filter(
            Document.knowledge_base_id == knowledge_base_id
        ).count()
    
    def count_by_status(
        self,
        knowledge_base_id: int,
        status: DocumentStatus
    ) -> int:
        """
        获取知识库中指定状态的文档数量
        
        Args:
            knowledge_base_id: 知识库ID
            status: 文档状态
        
        Returns:
            int: 文档数量
        """
        return self.db.query(Document).filter(
            Document.knowledge_base_id == knowledge_base_id,
            Document.status == status
        ).count()
    
    def exists(
        self,
        document_id: int,
        knowledge_base_id: int
    ) -> bool:
        """
        检查文档是否存在且属于指定知识库
        
        Args:
            document_id: 文档ID
            knowledge_base_id: 知识库ID
        
        Returns:
            bool: 存在返回True，否则返回False
        """
        return self.db.query(Document).filter(
            Document.id == document_id,
            Document.knowledge_base_id == knowledge_base_id
        ).first() is not None
    
    def get_total_chunk_count(self, knowledge_base_id: int) -> int:
        """
        获取知识库的总分块数量
        
        只统计已完成处理的文档。
        
        Args:
            knowledge_base_id: 知识库ID
        
        Returns:
            int: 总分块数量
        """
        from sqlalchemy import func
        
        result = self.db.query(func.sum(Document.chunk_count)).filter(
            Document.knowledge_base_id == knowledge_base_id,
            Document.status == DocumentStatus.COMPLETED
        ).scalar()
        
        return result or 0
    
    def get_completed_documents(
        self,
        knowledge_base_id: int
    ) -> List[Document]:
        """
        获取知识库中所有已完成处理的文档
        
        用于RAG查询时获取可用文档。
        
        Args:
            knowledge_base_id: 知识库ID
        
        Returns:
            List[Document]: 已完成处理的文档列表
        """
        return self.db.query(Document).filter(
            Document.knowledge_base_id == knowledge_base_id,
            Document.status == DocumentStatus.COMPLETED
        ).order_by(desc(Document.created_at)).all()
    
    def get_by_filename(
        self,
        knowledge_base_id: int,
        filename: str
    ) -> Optional[Document]:
        """
        根据文件名获取文档
        
        用于检查是否存在同名文档。
        
        Args:
            knowledge_base_id: 知识库ID
            filename: 文件名
        
        Returns:
            Optional[Document]: 文档对象，不存在则返回None
        """
        return self.db.query(Document).filter(
            Document.knowledge_base_id == knowledge_base_id,
            Document.filename == filename
        ).first()
    
    def filename_exists(
        self,
        knowledge_base_id: int,
        filename: str,
        exclude_document_id: Optional[int] = None
    ) -> bool:
        """
        检查文件名是否已存在于知识库中
        
        Args:
            knowledge_base_id: 知识库ID
            filename: 要检查的文件名
            exclude_document_id: 排除的文档ID（用于更新时排除自己）
        
        Returns:
            bool: 文件名已存在返回True，否则返回False
        """
        query = self.db.query(Document).filter(
            Document.knowledge_base_id == knowledge_base_id,
            Document.filename == filename
        )
        if exclude_document_id is not None:
            query = query.filter(Document.id != exclude_document_id)
        return query.first() is not None


# 导出
__all__ = ['DocumentRepository']
