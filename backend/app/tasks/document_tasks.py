"""
文档处理后台任务模块

实现文档处理的异步任务，包括：
- 文档加载
- 文本分块
- 向量化
- 存储到向量数据库
- 更新文档状态和进度

需求引用:
    - 需求3.3: 用户上传文档且文件类型为PDF、Word、TXT或Markdown
    - 需求3.4: 文档上传完成，异步提取文本内容并使用RecursiveCharacterTextSplitter进行分块处理
    - 需求3.5: 文档分块完成，使用DashScopeEmbeddings生成向量嵌入并存储到向量数据库
    - 需求3.6: 文档处理成功，更新文档状态为"已完成"并记录分块数量
"""

import logging
import asyncio
from typing import Optional, Callable, Any
from concurrent.futures import ThreadPoolExecutor

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.documents import Document as LangchainDocument
from sqlalchemy.orm import Session

from app.config import settings
from app.core.database import SessionLocal
from app.core.vector_store import get_vector_store_manager
from app.langchain_integration.document_loaders import (
    DocumentLoaderFactory,
    DocumentProcessingError,
)
from app.models.document import Document, DocumentStatus
from app.repositories.document_repository import DocumentRepository
from app.websocket.connection_manager import connection_manager

logger = logging.getLogger(__name__)


class DocumentProcessingTask:
    """
    文档处理任务类
    
    封装文档处理的完整流程：
    1. 加载文档
    2. 文本分块
    3. 向量化并存储
    4. 更新状态
    
    使用方式:
        task = DocumentProcessingTask(document_id=1)
        await task.process()
        
        # 或使用便捷函数
        await process_document_task(document_id=1)
    """
    
    def __init__(
        self,
        document_id: int,
        chunk_size: Optional[int] = None,
        chunk_overlap: Optional[int] = None,
        progress_callback: Optional[Callable[[int, str], Any]] = None,
    ):
        """
        初始化文档处理任务
        
        Args:
            document_id: 文档ID
            chunk_size: 分块大小，默认从配置读取
            chunk_overlap: 分块重叠大小，默认从配置读取
            progress_callback: 进度回调函数，接收(progress, status)参数
        """
        self.document_id = document_id
        self.chunk_size = chunk_size or settings.document_processing.chunk_size
        self.chunk_overlap = chunk_overlap or settings.document_processing.chunk_overlap
        self.progress_callback = progress_callback
        
        # 文本分块器
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", "。", "！", "？", ".", "!", "?", " ", ""],
        )
        
        # 向量存储管理器
        self.vector_store_manager = get_vector_store_manager()
    
    async def _update_progress(self, progress: int, status: str = "processing") -> None:
        """
        更新处理进度
        
        Args:
            progress: 进度百分比 (0-100)
            status: 状态描述
        """
        if self.progress_callback:
            try:
                await self.progress_callback(progress, status)
            except Exception as e:
                logger.warning(f"进度回调失败: {str(e)}")
        
        logger.debug(f"文档 {self.document_id} 处理进度: {progress}% - {status}")
        
        # 通过WebSocket发送进度更新（需要获取用户ID）
        # 注意：这里需要从文档记录中获取用户ID
        try:
            db = self._get_db_session()
            repo = DocumentRepository(db)
            document = repo.get_by_id(self.document_id)
            if document and document.knowledge_base:
                user_id = document.knowledge_base.user_id
                await connection_manager.send_personal_message(user_id, {
                    "type": "document_status",
                    "data": {
                        "document_id": self.document_id,
                        "status": status,
                        "progress": progress,
                        "timestamp": asyncio.get_event_loop().time()
                    }
                })
            db.close()
        except Exception as e:
            logger.warning(f"WebSocket通知失败: {str(e)}")
    
    def _get_db_session(self) -> Session:
        """获取数据库会话"""
        return SessionLocal()
    
    async def process(self) -> bool:
        """
        执行文档处理任务
        
        Returns:
            bool: 处理是否成功
        """
        db = self._get_db_session()
        
        try:
            repo = DocumentRepository(db)
            
            # 获取文档记录
            document = repo.get_by_id(self.document_id)
            if not document:
                logger.error(f"文档不存在: document_id={self.document_id}")
                return False
            
            logger.info(
                f"开始处理文档: id={document.id}, "
                f"filename={document.filename}, type={document.file_type}"
            )
            
            # 更新状态为处理中
            repo.update_status(self.document_id, DocumentStatus.PROCESSING)
            await self._update_progress(10, "开始处理")
            
            # 步骤1: 加载文档
            await self._update_progress(20, "加载文档")
            langchain_docs = await self._load_document(document)
            
            if not langchain_docs:
                raise DocumentProcessingError("文档加载失败：未提取到任何内容")
            
            await self._update_progress(40, "文档加载完成")
            
            # 步骤2: 文本分块
            await self._update_progress(50, "文本分块")
            chunks = await self._split_documents(langchain_docs, document)
            
            if not chunks:
                raise DocumentProcessingError("文档分块失败：未生成任何分块")
            
            await self._update_progress(60, f"分块完成，共{len(chunks)}个分块")
            
            # 步骤3: 向量化并存储
            await self._update_progress(70, "向量化存储")
            await self._store_vectors(chunks, document)
            
            await self._update_progress(90, "向量存储完成")
            
            # 步骤4: 更新文档状态为完成
            repo.mark_completed(self.document_id, len(chunks))
            await self._update_progress(100, "处理完成")
            
            # 通过WebSocket通知文档处理完成
            try:
                if document and document.knowledge_base:
                    user_id = document.knowledge_base.user_id
                    await connection_manager.send_personal_message(user_id, {
                        "type": "document_completed",
                        "data": {
                            "document_id": document.id,
                            "filename": document.filename,
                            "chunk_count": len(chunks),
                            "status": "completed",
                            "timestamp": asyncio.get_event_loop().time()
                        }
                    })
            except Exception as e:
                logger.warning(f"WebSocket完成通知失败: {str(e)}")
            
            logger.info(
                f"文档处理完成: id={document.id}, "
                f"filename={document.filename}, chunks={len(chunks)}"
            )
            
            return True
            
        except Exception as e:
            logger.error(
                f"文档处理失败: document_id={self.document_id}, error={str(e)}"
            )
            
            # 更新状态为失败
            try:
                repo = DocumentRepository(db)
                repo.mark_failed(self.document_id, str(e))
                
                # 通过WebSocket通知文档处理失败
                document = repo.get_by_id(self.document_id)
                if document and document.knowledge_base:
                    user_id = document.knowledge_base.user_id
                    await connection_manager.send_personal_message(user_id, {
                        "type": "document_failed",
                        "data": {
                            "document_id": self.document_id,
                            "filename": document.filename,
                            "error": str(e),
                            "status": "failed",
                            "timestamp": asyncio.get_event_loop().time()
                        }
                    })
            except Exception as update_error:
                logger.error(f"更新失败状态失败: {str(update_error)}")
            
            return False
            
        finally:
            db.close()
    
    async def _load_document(self, document: Document) -> list[LangchainDocument]:
        """
        加载文档
        
        Args:
            document: 文档数据库记录
        
        Returns:
            list[LangchainDocument]: LangChain文档对象列表
        """
        logger.debug(f"加载文档: path={document.file_path}, type={document.file_type}")
        
        # 使用异步加载
        docs = await DocumentLoaderFactory.load_document_async(
            file_path=document.file_path,
            file_type=document.file_type,
            document_id=document.id,
            knowledge_base_id=document.knowledge_base_id,
        )
        
        logger.debug(f"文档加载完成: pages={len(docs)}")
        return docs
    
    async def _split_documents(
        self,
        documents: list[LangchainDocument],
        document: Document,
    ) -> list[LangchainDocument]:
        """
        文本分块
        
        Args:
            documents: LangChain文档对象列表
            document: 文档数据库记录
        
        Returns:
            list[LangchainDocument]: 分块后的文档列表
        """
        logger.debug(f"开始文本分块: chunk_size={self.chunk_size}, overlap={self.chunk_overlap}")
        
        # 在线程池中执行分块（避免阻塞事件循环）
        loop = asyncio.get_event_loop()
        
        with ThreadPoolExecutor() as executor:
            chunks = await loop.run_in_executor(
                executor,
                lambda: self.text_splitter.split_documents(documents)
            )
        
        # 为每个分块添加元数据
        for i, chunk in enumerate(chunks):
            chunk.metadata['chunk_index'] = i
            chunk.metadata['document_id'] = document.id
            chunk.metadata['knowledge_base_id'] = document.knowledge_base_id
            chunk.metadata['source'] = document.filename
        
        logger.debug(f"文本分块完成: chunks={len(chunks)}")
        return chunks
    
    async def _store_vectors(
        self,
        chunks: list[LangchainDocument],
        document: Document,
    ) -> None:
        """
        向量化并存储到向量数据库
        
        Args:
            chunks: 分块后的文档列表
            document: 文档数据库记录
        """
        logger.debug(f"开始向量化存储: kb_id={document.knowledge_base_id}, chunks={len(chunks)}")
        
        # 使用向量存储管理器添加文档
        await self.vector_store_manager.add_documents(
            knowledge_base_id=document.knowledge_base_id,
            documents=chunks,
            document_id=document.id,
        )
        
        logger.debug(f"向量化存储完成")


async def process_document_task(
    document_id: int,
    chunk_size: Optional[int] = None,
    chunk_overlap: Optional[int] = None,
    progress_callback: Optional[Callable[[int, str], Any]] = None,
) -> bool:
    """
    处理文档的便捷函数
    
    Args:
        document_id: 文档ID
        chunk_size: 分块大小
        chunk_overlap: 分块重叠大小
        progress_callback: 进度回调函数
    
    Returns:
        bool: 处理是否成功
    """
    task = DocumentProcessingTask(
        document_id=document_id,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        progress_callback=progress_callback,
    )
    return await task.process()


def process_document_sync(
    document_id: int,
    chunk_size: Optional[int] = None,
    chunk_overlap: Optional[int] = None,
) -> bool:
    """
    同步处理文档（用于后台任务调度器）
    
    Args:
        document_id: 文档ID
        chunk_size: 分块大小
        chunk_overlap: 分块重叠大小
    
    Returns:
        bool: 处理是否成功
    """
    return asyncio.run(
        process_document_task(
            document_id=document_id,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )
    )


class DocumentProcessingQueue:
    """
    文档处理队列
    
    管理待处理文档的队列，支持并发处理。
    
    使用方式:
        queue = DocumentProcessingQueue(max_workers=3)
        await queue.add_document(document_id=1)
        await queue.process_all()
    """
    
    def __init__(self, max_workers: int = 3):
        """
        初始化处理队列
        
        Args:
            max_workers: 最大并发处理数
        """
        self.max_workers = max_workers
        self._queue: asyncio.Queue = asyncio.Queue()
        self._processing = False
    
    async def add_document(self, document_id: int) -> None:
        """
        添加文档到处理队列
        
        Args:
            document_id: 文档ID
        """
        await self._queue.put(document_id)
        logger.debug(f"文档 {document_id} 已添加到处理队列")
    
    async def process_all(self) -> dict:
        """
        处理队列中的所有文档
        
        Returns:
            dict: 处理结果统计
        """
        if self._processing:
            logger.warning("队列正在处理中")
            return {"status": "already_processing"}
        
        self._processing = True
        results = {"success": 0, "failed": 0, "total": 0}
        
        try:
            tasks = []
            
            while not self._queue.empty():
                document_id = await self._queue.get()
                results["total"] += 1
                
                task = asyncio.create_task(
                    self._process_with_semaphore(document_id, results)
                )
                tasks.append(task)
                
                # 限制并发数
                if len(tasks) >= self.max_workers:
                    await asyncio.gather(*tasks)
                    tasks = []
            
            # 处理剩余任务
            if tasks:
                await asyncio.gather(*tasks)
            
            return results
            
        finally:
            self._processing = False
    
    async def _process_with_semaphore(
        self,
        document_id: int,
        results: dict,
    ) -> None:
        """
        使用信号量限制并发处理
        
        Args:
            document_id: 文档ID
            results: 结果统计字典
        """
        try:
            success = await process_document_task(document_id)
            if success:
                results["success"] += 1
            else:
                results["failed"] += 1
        except Exception as e:
            logger.error(f"处理文档 {document_id} 失败: {str(e)}")
            results["failed"] += 1


# 全局处理队列实例
_document_queue: Optional[DocumentProcessingQueue] = None


def get_document_queue(max_workers: int = 3) -> DocumentProcessingQueue:
    """
    获取全局文档处理队列实例
    
    Args:
        max_workers: 最大并发处理数
    
    Returns:
        DocumentProcessingQueue: 处理队列实例
    """
    global _document_queue
    
    if _document_queue is None:
        _document_queue = DocumentProcessingQueue(max_workers=max_workers)
    
    return _document_queue


# 导出
__all__ = [
    'DocumentProcessingTask',
    'DocumentProcessingQueue',
    'process_document_task',
    'process_document_sync',
    'get_document_queue',
]
