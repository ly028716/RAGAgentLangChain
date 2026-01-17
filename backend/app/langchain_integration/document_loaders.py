"""
文档加载器模块

提供文档加载器工厂类，支持多种文档格式的加载。
支持PDF、Word、TXT、Markdown格式。

需求引用:
    - 需求3.3: 用户上传文档且文件类型为PDF、Word、TXT或Markdown
"""

import logging
import os
from datetime import datetime
from typing import List, Optional, Type

from langchain_core.documents import Document
from langchain_community.document_loaders.pdf import PyPDFLoader
from langchain_community.document_loaders.word_document import Docx2txtLoader
from langchain_community.document_loaders.text import TextLoader
from langchain_community.document_loaders.markdown import UnstructuredMarkdownLoader
from langchain_community.document_loaders.base import BaseLoader

logger = logging.getLogger(__name__)


class DocumentProcessingError(Exception):
    """文档处理异常"""
    pass


class UnsupportedFileTypeError(DocumentProcessingError):
    """不支持的文件类型异常"""
    pass


class DocumentLoaderFactory:
    """
    文档加载器工厂类
    
    根据文件类型返回相应的文档加载器，支持：
    - PDF: 使用PyPDFLoader
    - Word (docx/doc): 使用Docx2txtLoader
    - TXT: 使用TextLoader
    - Markdown (md): 使用UnstructuredMarkdownLoader
    
    使用方式:
        # 获取加载器
        loader = DocumentLoaderFactory.get_loader("/path/to/file.pdf", "pdf")
        documents = loader.load()
        
        # 直接加载文档
        documents = await DocumentLoaderFactory.load_document("/path/to/file.pdf", "pdf")
    """
    
    # 支持的文件类型映射
    SUPPORTED_LOADERS = {
        'pdf': PyPDFLoader,
        'docx': Docx2txtLoader,
        'doc': Docx2txtLoader,
        'txt': TextLoader,
        'md': UnstructuredMarkdownLoader,
        'markdown': UnstructuredMarkdownLoader,
    }
    
    # 文件类型的MIME类型映射
    MIME_TYPE_MAP = {
        'application/pdf': 'pdf',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document': 'docx',
        'application/msword': 'doc',
        'text/plain': 'txt',
        'text/markdown': 'md',
    }
    
    @classmethod
    def get_supported_types(cls) -> List[str]:
        """
        获取支持的文件类型列表
        
        Returns:
            List[str]: 支持的文件类型列表
        """
        return list(cls.SUPPORTED_LOADERS.keys())
    
    @classmethod
    def is_supported(cls, file_type: str) -> bool:
        """
        检查文件类型是否支持
        
        Args:
            file_type: 文件类型（扩展名）
        
        Returns:
            bool: 是否支持该文件类型
        """
        return file_type.lower() in cls.SUPPORTED_LOADERS
    
    @classmethod
    def get_file_type_from_extension(cls, filename: str) -> Optional[str]:
        """
        从文件名获取文件类型
        
        Args:
            filename: 文件名
        
        Returns:
            Optional[str]: 文件类型，不支持则返回None
        """
        if '.' not in filename:
            return None
        
        extension = filename.rsplit('.', 1)[-1].lower()
        
        if extension in cls.SUPPORTED_LOADERS:
            return extension
        
        return None
    
    @classmethod
    def get_file_type_from_mime(cls, mime_type: str) -> Optional[str]:
        """
        从MIME类型获取文件类型
        
        Args:
            mime_type: MIME类型
        
        Returns:
            Optional[str]: 文件类型，不支持则返回None
        """
        return cls.MIME_TYPE_MAP.get(mime_type.lower())
    
    @classmethod
    def get_loader(cls, file_path: str, file_type: str) -> BaseLoader:
        """
        根据文件类型返回相应的加载器
        
        Args:
            file_path: 文件路径
            file_type: 文件类型（扩展名）
        
        Returns:
            BaseLoader: 文档加载器实例
        
        Raises:
            UnsupportedFileTypeError: 不支持的文件类型
            FileNotFoundError: 文件不存在
        """
        # 检查文件是否存在
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"文件不存在: {file_path}")
        
        # 获取加载器类
        file_type_lower = file_type.lower()
        loader_class = cls.SUPPORTED_LOADERS.get(file_type_lower)
        
        if not loader_class:
            supported = ', '.join(cls.get_supported_types())
            raise UnsupportedFileTypeError(
                f"不支持的文件类型: {file_type}。支持的类型: {supported}"
            )
        
        logger.debug(f"创建文档加载器: type={file_type}, loader={loader_class.__name__}")
        
        # 创建加载器实例
        # TextLoader需要指定编码
        if loader_class == TextLoader:
            return loader_class(file_path, encoding='utf-8')
        
        return loader_class(file_path)
    
    @classmethod
    def load_document(
        cls,
        file_path: str,
        file_type: str,
        document_id: Optional[int] = None,
        knowledge_base_id: Optional[int] = None,
    ) -> List[Document]:
        """
        加载文档并返回文档对象列表（同步方法）
        
        Args:
            file_path: 文件路径
            file_type: 文件类型
            document_id: 文档ID（可选，用于添加元数据）
            knowledge_base_id: 知识库ID（可选，用于添加元数据）
        
        Returns:
            List[Document]: 文档对象列表
        
        Raises:
            DocumentProcessingError: 文档加载失败
        """
        try:
            loader = cls.get_loader(file_path, file_type)
            documents = loader.load()
            
            # 添加元数据
            for doc in documents:
                doc.metadata['file_path'] = file_path
                doc.metadata['file_type'] = file_type
                doc.metadata['loaded_at'] = datetime.utcnow().isoformat()
                doc.metadata['source'] = os.path.basename(file_path)
                
                if document_id is not None:
                    doc.metadata['document_id'] = document_id
                
                if knowledge_base_id is not None:
                    doc.metadata['knowledge_base_id'] = knowledge_base_id
            
            logger.info(
                f"文档加载成功: path={file_path}, type={file_type}, "
                f"pages={len(documents)}"
            )
            
            return documents
            
        except (UnsupportedFileTypeError, FileNotFoundError):
            raise
        except Exception as e:
            logger.error(f"文档加载失败: path={file_path}, error={str(e)}")
            raise DocumentProcessingError(f"文档加载失败: {str(e)}")
    
    @classmethod
    async def load_document_async(
        cls,
        file_path: str,
        file_type: str,
        document_id: Optional[int] = None,
        knowledge_base_id: Optional[int] = None,
    ) -> List[Document]:
        """
        异步加载文档并返回文档对象列表
        
        注意：由于底层加载器大多是同步的，这里使用线程池执行
        
        Args:
            file_path: 文件路径
            file_type: 文件类型
            document_id: 文档ID（可选，用于添加元数据）
            knowledge_base_id: 知识库ID（可选，用于添加元数据）
        
        Returns:
            List[Document]: 文档对象列表
        
        Raises:
            DocumentProcessingError: 文档加载失败
        """
        import asyncio
        from concurrent.futures import ThreadPoolExecutor
        
        loop = asyncio.get_event_loop()
        
        with ThreadPoolExecutor() as executor:
            documents = await loop.run_in_executor(
                executor,
                lambda: cls.load_document(
                    file_path, file_type, document_id, knowledge_base_id
                )
            )
        
        return documents
    
    @classmethod
    def get_document_preview(
        cls,
        file_path: str,
        file_type: str,
        max_chars: int = 1000,
    ) -> str:
        """
        获取文档预览内容
        
        返回文档的前N个字符的文本内容。
        
        Args:
            file_path: 文件路径
            file_type: 文件类型
            max_chars: 最大字符数，默认1000
        
        Returns:
            str: 文档预览文本
        
        Raises:
            DocumentProcessingError: 文档加载失败
        
        需求引用:
            - 需求3.8: 用户请求文档预览，返回文档的前1000个字符的文本内容
        """
        try:
            documents = cls.load_document(file_path, file_type)
            
            # 合并所有页面的内容
            full_text = "\n".join(doc.page_content for doc in documents)
            
            # 截取前N个字符
            preview = full_text[:max_chars]
            
            logger.debug(
                f"文档预览: path={file_path}, "
                f"total_length={len(full_text)}, preview_length={len(preview)}"
            )
            
            return preview
            
        except Exception as e:
            logger.error(f"获取文档预览失败: path={file_path}, error={str(e)}")
            raise DocumentProcessingError(f"获取文档预览失败: {str(e)}")
    
    @classmethod
    def validate_file(
        cls,
        file_path: str,
        file_type: str,
        max_size_bytes: Optional[int] = None,
    ) -> bool:
        """
        验证文件是否有效
        
        检查文件是否存在、类型是否支持、大小是否在限制内。
        
        Args:
            file_path: 文件路径
            file_type: 文件类型
            max_size_bytes: 最大文件大小（字节），None表示不限制
        
        Returns:
            bool: 文件是否有效
        
        Raises:
            FileNotFoundError: 文件不存在
            UnsupportedFileTypeError: 不支持的文件类型
            DocumentProcessingError: 文件大小超出限制
        """
        # 检查文件是否存在
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"文件不存在: {file_path}")
        
        # 检查文件类型
        if not cls.is_supported(file_type):
            supported = ', '.join(cls.get_supported_types())
            raise UnsupportedFileTypeError(
                f"不支持的文件类型: {file_type}。支持的类型: {supported}"
            )
        
        # 检查文件大小
        if max_size_bytes is not None:
            file_size = os.path.getsize(file_path)
            if file_size > max_size_bytes:
                max_size_mb = max_size_bytes / (1024 * 1024)
                file_size_mb = file_size / (1024 * 1024)
                raise DocumentProcessingError(
                    f"文件大小超出限制: {file_size_mb:.2f}MB > {max_size_mb:.2f}MB"
                )
        
        return True


# 导出
__all__ = [
    'DocumentLoaderFactory',
    'DocumentProcessingError',
    'UnsupportedFileTypeError',
]
