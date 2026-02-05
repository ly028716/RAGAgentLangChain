"""
RAG服务模块

实现检索增强生成（RAG）服务，提供：
- 知识库管理（创建、查询、删除）
- 文档上传和管理
- 文档处理状态查询
- RAG问答功能

需求引用:
    - 需求3.1: 用户创建知识库且提供名称和描述
    - 需求3.2: 用户上传文档且文件类型为PDF、Word、TXT或Markdown且文件大小不超过10MB
    - 需求3.3: 用户批量上传多个文档
    - 需求3.10: 用户查询文档处理状态
"""

import logging
import os
import re
import shutil
import uuid
from datetime import datetime
from typing import List, Optional, Tuple

from fastapi import BackgroundTasks, UploadFile
from sqlalchemy.orm import Session

from app.config import settings
from app.core.vector_store import get_vector_store_manager
from app.langchain_integration.document_loaders import (
    DocumentLoaderFactory, DocumentProcessingError, UnsupportedFileTypeError)
from app.models.document import Document, DocumentStatus
from app.models.knowledge_base import KnowledgeBase
from app.models.knowledge_base_permission import PermissionType
from app.repositories.document_repository import DocumentRepository
from app.repositories.knowledge_base_repository import KnowledgeBaseRepository
from app.services.knowledge_base_permission_service import (
    KnowledgeBasePermissionService,
)
from app.tasks.document_tasks import process_document_task

logger = logging.getLogger(__name__)

def _sanitize_filename(filename: str) -> str:
    base = os.path.basename(filename or "").strip() or "upload"
    base = base.replace("\x00", "")
    base = re.sub(r"[^A-Za-z0-9._-]+", "_", base)
    if len(base) > 180:
        root, ext = os.path.splitext(base)
        base = f"{root[:160]}{ext[:20]}"
    return base


def _normalize_display_filename(filename: str) -> str:
    base = os.path.basename(filename or "").strip() or "upload"
    base = base.replace("\x00", "")
    base = re.sub(r"[\r\n\t]+", " ", base).strip()
    if len(base) > 180:
        root, ext = os.path.splitext(base)
        base = f"{root[:160]}{ext[:20]}"
    return base


class RAGServiceError(Exception):
    """RAG服务异常"""

    pass


class KnowledgeBaseNotFoundError(RAGServiceError):
    """知识库不存在异常"""

    pass


class DocumentNotFoundError(RAGServiceError):
    """文档不存在异常"""

    pass


class FileUploadError(RAGServiceError):
    """文件上传异常"""

    pass


class DocumentStatusResponse:
    """文档状态响应"""

    def __init__(
        self,
        document_id: int,
        status: str,
        progress: int,
        chunk_count: int,
        error_message: Optional[str] = None,
    ):
        self.document_id = document_id
        self.status = status
        self.progress = progress
        self.chunk_count = chunk_count
        self.error_message = error_message

    def to_dict(self) -> dict:
        return {
            "document_id": self.document_id,
            "status": self.status,
            "progress": self.progress,
            "chunk_count": self.chunk_count,
            "error_message": self.error_message,
        }


class RAGService:
    """
    RAG服务类

    提供知识库管理、文档上传和RAG问答功能。

    使用方式:
        service = RAGService(db)

        # 创建知识库
        kb = service.create_knowledge_base(user_id=1, name="技术文档", description="技术相关文档")

        # 上传文档
        doc = await service.upload_document(kb_id=1, user_id=1, file=upload_file, background_tasks=tasks)

        # 查询文档状态
        status = service.get_document_status(document_id=1, user_id=1)
    """

    def __init__(self, db: Session):
        """
        初始化RAG服务

        Args:
            db: 数据库会话
        """
        self.db = db
        self.kb_repo = KnowledgeBaseRepository(db)
        self.doc_repo = DocumentRepository(db)
        self.kb_permission_service = KnowledgeBasePermissionService(db)
        self.vector_store_manager = get_vector_store_manager()

        # 确保上传目录存在
        self._ensure_upload_dir()

    def _ensure_upload_dir(self) -> None:
        """确保上传目录存在"""
        upload_dir = settings.file_storage.upload_dir
        abs_path = os.path.abspath(upload_dir)
        if not os.path.exists(abs_path):
            os.makedirs(abs_path, exist_ok=True)
            logger.info(f"创建上传目录: {abs_path}")
        else:
            logger.info(f"上传目录已存在: {abs_path}")

    def _require_kb_permission(
        self,
        kb_id: int,
        user_id: int,
        required_permission: str,
    ) -> KnowledgeBase:
        has_permission, kb = self.kb_permission_service.check_permission(
            kb_id, user_id, required_permission
        )
        if not has_permission or kb is None:
            raise KnowledgeBaseNotFoundError(f"知识库不存在: id={kb_id}")
        return kb

    # ==================== 知识库管理 ====================

    def create_knowledge_base(
        self,
        user_id: int,
        name: str,
        description: Optional[str] = None,
        category: Optional[str] = None,
    ) -> KnowledgeBase:
        """
        创建知识库

        Args:
            user_id: 用户ID
            name: 知识库名称
            description: 知识库描述
            category: 知识库分类

        Returns:
            KnowledgeBase: 创建的知识库对象

        需求引用:
            - 需求3.1: 用户创建知识库且提供名称和描述
        """
        logger.info(f"创建知识库: user_id={user_id}, name={name}")

        kb = self.kb_repo.create(
            user_id=user_id,
            name=name,
            description=description,
            category=category,
        )

        logger.info(f"知识库创建成功: id={kb.id}, name={kb.name}")
        return kb

    def get_knowledge_bases(
        self,
        user_id: int,
        skip: int = 0,
        limit: int = 20,
    ) -> Tuple[List[KnowledgeBase], int]:
        """
        获取用户的知识库列表

        Args:
            user_id: 用户ID
            skip: 跳过的记录数
            limit: 返回的最大记录数

        Returns:
            Tuple[List[KnowledgeBase], int]: (知识库列表, 总数)
        """
        return self.kb_repo.get_by_user(user_id, skip, limit)

    def get_knowledge_base(
        self,
        kb_id: int,
        user_id: int,
    ) -> KnowledgeBase:
        """
        获取知识库详情

        Args:
            kb_id: 知识库ID
            user_id: 用户ID

        Returns:
            KnowledgeBase: 知识库对象

        Raises:
            KnowledgeBaseNotFoundError: 知识库不存在
        """
        return self._require_kb_permission(kb_id, user_id, PermissionType.VIEWER.value)

    def get_knowledge_base_for_edit(
        self,
        kb_id: int,
        user_id: int,
    ) -> KnowledgeBase:
        return self._require_kb_permission(kb_id, user_id, PermissionType.EDITOR.value)

    def update_knowledge_base(
        self,
        kb_id: int,
        user_id: int,
        name: Optional[str] = None,
        description: Optional[str] = None,
        category: Optional[str] = None,
    ) -> KnowledgeBase:
        """
        更新知识库信息

        Args:
            kb_id: 知识库ID
            user_id: 用户ID
            name: 新名称
            description: 新描述
            category: 新分类

        Returns:
            KnowledgeBase: 更新后的知识库对象

        Raises:
            KnowledgeBaseNotFoundError: 知识库不存在
        """
        kb = self.kb_repo.update(kb_id, user_id, name, description, category)
        if not kb:
            raise KnowledgeBaseNotFoundError(f"知识库不存在: id={kb_id}")

        logger.info(f"知识库更新成功: id={kb_id}")
        return kb

    def delete_knowledge_base(
        self,
        kb_id: int,
        user_id: int,
    ) -> bool:
        """
        删除知识库

        删除知识库及其所有文档和向量数据。

        Args:
            kb_id: 知识库ID
            user_id: 用户ID

        Returns:
            bool: 是否删除成功

        Raises:
            KnowledgeBaseNotFoundError: 知识库不存在
        """
        # 检查知识库是否存在
        kb = self.kb_repo.get_by_id_and_user(kb_id, user_id)
        if not kb:
            raise KnowledgeBaseNotFoundError(f"知识库不存在: id={kb_id}")

        # 删除向量数据
        try:
            self.vector_store_manager.delete_collection(kb_id)
        except Exception as e:
            logger.warning(f"删除向量集合失败: {str(e)}")

        # 删除文档文件
        for doc in kb.documents:
            try:
                if os.path.exists(doc.file_path):
                    os.remove(doc.file_path)
            except Exception as e:
                logger.warning(f"删除文件失败: {doc.file_path}, error={str(e)}")

        # 删除数据库记录
        success = self.kb_repo.delete(kb_id, user_id)

        if success:
            logger.info(f"知识库删除成功: id={kb_id}")

        return success

    # ==================== 文档管理 ====================

    async def upload_document(
        self,
        kb_id: int,
        user_id: int,
        file: UploadFile,
        background_tasks: BackgroundTasks,
    ) -> Document:
        """
        上传文档

        保存文件并创建后台处理任务。

        Args:
            kb_id: 知识库ID
            user_id: 用户ID
            file: 上传的文件
            background_tasks: FastAPI后台任务

        Returns:
            Document: 创建的文档记录

        Raises:
            KnowledgeBaseNotFoundError: 知识库不存在
            FileUploadError: 文件上传失败
            UnsupportedFileTypeError: 不支持的文件类型

        需求引用:
            - 需求3.2: 用户上传文档且文件类型为PDF、Word、TXT或Markdown且文件大小不超过10MB
        """
        # 验证知识库
        self._require_kb_permission(kb_id, user_id, PermissionType.EDITOR.value)

        # 获取文件类型
        display_filename = _normalize_display_filename(file.filename)
        file_type = DocumentLoaderFactory.get_file_type_from_extension(display_filename)
        
        logger.info(f"开始处理文件上传: filename={display_filename}, type={file_type}")

        if not file_type:
            logger.warning(f"文件类型不支持: {display_filename}")
            raise UnsupportedFileTypeError(
                f"不支持的文件类型: {display_filename}。"
                f"支持的类型: {', '.join(DocumentLoaderFactory.get_supported_types())}"
            )

        # 验证文件大小（在保存文件之前）
        # 读取文件内容以获取大小
        try:
            file_content = await file.read()
            file_size = len(file_content)
            max_size = settings.file_storage.max_upload_size_bytes
            
            logger.info(f"文件大小: {file_size} bytes, 最大允许: {max_size} bytes")

            if file_size > max_size:
                max_size_mb = max_size / (1024 * 1024)
                file_size_mb = file_size / (1024 * 1024)
                logger.warning(f"文件大小超出限制: {file_size_mb:.2f}MB > {max_size_mb:.2f}MB")
                raise FileUploadError(
                    f"文件大小超出限制: {file_size_mb:.2f}MB > {max_size_mb:.2f}MB"
                )
        except Exception as e:
            if isinstance(e, FileUploadError):
                raise
            logger.error(f"读取文件失败: {str(e)}")
            raise FileUploadError(f"读取文件失败: {str(e)}")

        try:
            file_path = await self._save_upload_file(
                file, kb_id, content=file_content, display_filename=display_filename
            )
            logger.info(f"文件保存成功: {file_path}")
        except Exception as e:
            logger.error(f"保存文件失败: {str(e)}")
            raise FileUploadError(f"保存文件失败: {str(e)}")

        try:
            # 创建文档记录
            document = self.doc_repo.create(
                knowledge_base_id=kb_id,
                filename=display_filename,
                file_path=file_path,
                file_size=file_size,
                file_type=file_type,
            )

            # 更新知识库更新时间
            self.kb_repo.touch(kb_id)

            # 添加后台处理任务
            background_tasks.add_task(
                self._process_document_background,
                document.id,
            )

            logger.info(
                f"文档上传成功: id={document.id}, "
                f"filename={document.filename}, kb_id={kb_id}"
            )

            return document

        except Exception as e:
            # 清理已保存的文件
            if os.path.exists(file_path):
                os.remove(file_path)
            raise

    async def upload_documents_batch(
        self,
        kb_id: int,
        user_id: int,
        files: List[UploadFile],
        background_tasks: BackgroundTasks,
    ) -> List[Document]:
        """
        批量上传文档

        Args:
            kb_id: 知识库ID
            user_id: 用户ID
            files: 上传的文件列表
            background_tasks: FastAPI后台任务

        Returns:
            List[Document]: 创建的文档记录列表

        需求引用:
            - 需求3.3: 用户批量上传多个文档
        """
        documents = []
        errors = []

        for file in files:
            try:
                doc = await self.upload_document(
                    kb_id=kb_id,
                    user_id=user_id,
                    file=file,
                    background_tasks=background_tasks,
                )
                documents.append(doc)
            except Exception as e:
                errors.append(
                    {
                        "filename": file.filename,
                        "error": str(e),
                    }
                )
                logger.warning(f"批量上传文件失败: {file.filename}, error={str(e)}")

        if errors:
            logger.warning(f"批量上传部分失败: {len(errors)}/{len(files)}")

        return documents

    async def _save_upload_file(
        self,
        file: UploadFile,
        kb_id: int,
        content: Optional[bytes] = None,
        display_filename: Optional[str] = None,
    ) -> str:
        """
        保存上传的文件

        Args:
            file: 上传的文件
            kb_id: 知识库ID

        Returns:
            str: 保存的文件路径
        """
        # 生成唯一文件名
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        unique_id = uuid.uuid4().hex[:8]
        safe_original = _sanitize_filename(display_filename or file.filename)
        safe_filename = f"{timestamp}_{unique_id}_{safe_original}"

        # 创建知识库目录
        kb_dir = os.path.join(settings.file_storage.upload_dir, f"kb_{kb_id}")
        if not os.path.exists(kb_dir):
            os.makedirs(kb_dir, exist_ok=True)

        # 保存文件
        file_path = os.path.join(kb_dir, safe_filename)

        try:
            with open(file_path, "wb") as buffer:
                if content is None:
                    content = await file.read()
                buffer.write(content)

            logger.debug(f"文件保存成功: {file_path}")
            return file_path

        except Exception as e:
            logger.error(f"文件保存失败: {str(e)}")
            raise FileUploadError(f"文件保存失败: {str(e)}")

    async def _process_document_background(self, document_id: int) -> None:
        """
        后台处理文档

        Args:
            document_id: 文档ID
        """
        try:
            await process_document_task(document_id)
        except Exception as e:
            logger.error(f"后台处理文档失败: document_id={document_id}, error={str(e)}")

    def get_document_status(
        self,
        document_id: int,
        user_id: int,
    ) -> DocumentStatusResponse:
        """
        获取文档处理状态

        Args:
            document_id: 文档ID
            user_id: 用户ID

        Returns:
            DocumentStatusResponse: 文档状态响应

        Raises:
            DocumentNotFoundError: 文档不存在

        需求引用:
            - 需求3.10: 用户查询文档处理状态
        """
        document = self.doc_repo.get_by_id(document_id)

        if not document:
            raise DocumentNotFoundError(f"文档不存在: id={document_id}")

        # 验证用户权限
        try:
            self._require_kb_permission(
                document.knowledge_base_id, user_id, PermissionType.VIEWER.value
            )
        except KnowledgeBaseNotFoundError as e:
            raise DocumentNotFoundError(f"文档不存在: id={document_id}") from e

        # 计算进度
        progress = self._calculate_progress(document.status)

        return DocumentStatusResponse(
            document_id=document.id,
            status=document.status.value,
            progress=progress,
            chunk_count=document.chunk_count,
            error_message=document.error_message,
        )

    def _calculate_progress(self, status: DocumentStatus) -> int:
        """
        根据状态计算进度百分比

        Args:
            status: 文档状态

        Returns:
            int: 进度百分比
        """
        progress_map = {
            DocumentStatus.PROCESSING: 50,
            DocumentStatus.COMPLETED: 100,
            DocumentStatus.FAILED: 0,
        }
        return progress_map.get(status, 0)

    def get_documents(
        self,
        kb_id: int,
        user_id: int,
        skip: int = 0,
        limit: int = 20,
    ) -> Tuple[List[Document], int]:
        """
        获取知识库的文档列表

        Args:
            kb_id: 知识库ID
            user_id: 用户ID
            skip: 跳过的记录数
            limit: 返回的最大记录数

        Returns:
            Tuple[List[Document], int]: (文档列表, 总数)

        Raises:
            KnowledgeBaseNotFoundError: 知识库不存在
        """
        # 验证知识库
        self._require_kb_permission(kb_id, user_id, PermissionType.VIEWER.value)

        return self.doc_repo.get_by_knowledge_base(kb_id, skip, limit)

    def get_document_preview(
        self,
        document_id: int,
        user_id: int,
        max_chars: int = 1000,
    ) -> str:
        """
        获取文档预览

        Args:
            document_id: 文档ID
            user_id: 用户ID
            max_chars: 最大字符数

        Returns:
            str: 文档预览文本

        Raises:
            DocumentNotFoundError: 文档不存在

        需求引用:
            - 需求3.8: 用户请求文档预览，返回文档的前1000个字符的文本内容
        """
        document = self.doc_repo.get_by_id(document_id)

        if not document:
            raise DocumentNotFoundError(f"文档不存在: id={document_id}")

        # 验证用户权限
        try:
            self._require_kb_permission(
                document.knowledge_base_id, user_id, PermissionType.VIEWER.value
            )
        except KnowledgeBaseNotFoundError as e:
            raise DocumentNotFoundError(f"文档不存在: id={document_id}") from e

        # 获取预览
        return DocumentLoaderFactory.get_document_preview(
            file_path=document.file_path,
            file_type=document.file_type,
            max_chars=max_chars,
        )

    def get_document_preview_with_length(
        self,
        document_id: int,
        user_id: int,
        max_chars: int = 1000,
    ) -> Tuple[str, int]:
        document = self.doc_repo.get_by_id(document_id)
        if not document:
            raise DocumentNotFoundError(f"文档不存在: id={document_id}")

        try:
            self._require_kb_permission(
                document.knowledge_base_id, user_id, PermissionType.VIEWER.value
            )
        except KnowledgeBaseNotFoundError as e:
            raise DocumentNotFoundError(f"文档不存在: id={document_id}") from e

        return DocumentLoaderFactory.get_document_preview_with_length(
            file_path=document.file_path,
            file_type=document.file_type,
            max_chars=max_chars,
        )

    def get_document_file(
        self,
        document_id: int,
        user_id: int,
    ) -> Tuple[str, str]:
        document = self.doc_repo.get_by_id(document_id)
        if not document:
            raise DocumentNotFoundError(f"文档不存在: id={document_id}")

        try:
            self._require_kb_permission(
                document.knowledge_base_id, user_id, PermissionType.VIEWER.value
            )
        except KnowledgeBaseNotFoundError as e:
            raise DocumentNotFoundError(f"文档不存在: id={document_id}") from e

        if not os.path.exists(document.file_path):
            raise DocumentNotFoundError(f"文件不存在: path={document.file_path}")

        return document.file_path, document.filename

    async def retry_document_processing(
        self,
        document_id: int,
        user_id: int,
        background_tasks: BackgroundTasks,
    ) -> Document:
        document = self.doc_repo.get_by_id(document_id)
        if not document:
            raise DocumentNotFoundError(f"文档不存在: id={document_id}")

        try:
            self._require_kb_permission(
                document.knowledge_base_id, user_id, PermissionType.EDITOR.value
            )
        except KnowledgeBaseNotFoundError as e:
            raise DocumentNotFoundError(f"文档不存在: id={document_id}") from e

        try:
            await self.vector_store_manager.delete_by_document_id(
                document.knowledge_base_id, document_id
            )
        except Exception as e:
            logger.warning(f"重试前删除向量数据失败: {str(e)}")

        document = self.doc_repo.update_status(
            document_id,
            DocumentStatus.PROCESSING,
            chunk_count=0,
        )
        if document:
            document.error_message = None
            self.db.commit()
            self.db.refresh(document)

        background_tasks.add_task(self._process_document_background, document.id)
        return document

    async def delete_document(
        self,
        document_id: int,
        user_id: int,
    ) -> bool:
        """
        删除文档

        删除文档文件、数据库记录和向量数据。

        Args:
            document_id: 文档ID
            user_id: 用户ID

        Returns:
            bool: 是否删除成功

        Raises:
            DocumentNotFoundError: 文档不存在

        需求引用:
            - 需求3.9: 用户删除文档，删除文件、数据库记录和向量数据库中的相关向量
        """
        document = self.doc_repo.get_by_id(document_id)

        if not document:
            raise DocumentNotFoundError(f"文档不存在: id={document_id}")

        # 验证用户权限
        try:
            self._require_kb_permission(
                document.knowledge_base_id, user_id, PermissionType.EDITOR.value
            )
        except KnowledgeBaseNotFoundError as e:
            raise DocumentNotFoundError(f"文档不存在: id={document_id}") from e

        kb_id = document.knowledge_base_id
        file_path = document.file_path

        try:
            await self.vector_store_manager.delete_by_document_id(kb_id, document_id)
        except Exception as e:
            logger.warning(f"删除向量数据失败: {str(e)}")

        # 删除文件
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception as e:
            logger.warning(f"删除文件失败: {file_path}, error={str(e)}")

        # 删除数据库记录
        success = self.doc_repo.delete(document_id)

        if success:
            logger.info(f"文档删除成功: id={document_id}")

        return success


# 导出
__all__ = [
    "RAGService",
    "RAGServiceError",
    "KnowledgeBaseNotFoundError",
    "DocumentNotFoundError",
    "FileUploadError",
    "DocumentStatusResponse",
]
