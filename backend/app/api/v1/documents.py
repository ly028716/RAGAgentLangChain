"""
文档管理API路由

提供文档上传、查询、预览和删除等端点。

需求引用:
    - 需求3.2: 用户上传文档且文件类型为PDF、Word、TXT或Markdown且文件大小不超过10MB
    - 需求3.3: 用户批量上传多个文档
    - 需求3.8: 用户请求文档预览
    - 需求3.9: 用户删除文档
    - 需求3.10: 用户查询文档处理状态
"""

import logging
from typing import List

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    HTTPException,
    UploadFile,
    status,
)
from sqlalchemy.orm import Session

from app.config import settings
from app.core.database import get_db
from app.dependencies import get_current_user
from app.langchain_integration.document_loaders import (
    DocumentLoaderFactory,
    UnsupportedFileTypeError,
)
from app.models.user import User
from app.schemas.knowledge_base import (
    DocumentResponse,
    DocumentListResponse,
    DocumentStatusResponse,
    DocumentPreviewResponse,
    DocumentUploadResponse,
    BatchUploadResponse,
    MessageResponse,
)
from app.services.rag_service import (
    RAGService,
    KnowledgeBaseNotFoundError,
    DocumentNotFoundError,
    FileUploadError,
)
from app.services.knowledge_base_permission_service import KnowledgeBasePermissionService, PermissionType

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/documents", tags=["文档管理"])


@router.post(
    "/upload",
    response_model=DocumentUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="上传文档",
    description="上传单个文档到指定知识库。支持PDF、Word、TXT、Markdown格式，最大10MB。",
)
async def upload_document(
    knowledge_base_id: int,
    file: UploadFile = File(..., description="要上传的文档文件"),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    上传文档
    
    需求引用:
        - 需求3.2: 用户上传文档且文件类型为PDF、Word、TXT或Markdown且文件大小不超过10MB
    """
    service = RAGService(db)
    
    try:
        document = await service.upload_document(
            kb_id=knowledge_base_id,
            user_id=current_user.id,
            file=file,
            background_tasks=background_tasks,
        )
    except KnowledgeBaseNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="知识库不存在",
        )
    except UnsupportedFileTypeError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except FileUploadError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    
    logger.info(
        f"用户 {current_user.id} 上传文档: id={document.id}, "
        f"filename={document.filename}, kb_id={knowledge_base_id}"
    )
    
    return DocumentUploadResponse(
        id=document.id,
        filename=document.filename,
        file_size=document.file_size,
        status=document.status.value,
        created_at=document.created_at,
    )


@router.post(
    "/upload-batch",
    response_model=BatchUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="批量上传文档",
    description="批量上传多个文档到指定知识库。",
)
async def upload_documents_batch(
    knowledge_base_id: int,
    files: List[UploadFile] = File(..., description="要上传的文档文件列表"),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    批量上传文档
    
    需求引用:
        - 需求3.3: 用户批量上传多个文档
    """
    service = RAGService(db)
    
    kb_permission_service = KnowledgeBasePermissionService(db)
    has_permission, kb = kb_permission_service.check_permission(
        kb_id=knowledge_base_id,
        user_id=current_user.id,
        required_permission=PermissionType.EDITOR.value
    )
    if not kb or not has_permission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="知识库不存在",
        )
    
    documents = []
    errors = []
    
    for file in files:
        try:
            document = await service.upload_document(
                kb_id=knowledge_base_id,
                user_id=current_user.id,
                file=file,
                background_tasks=background_tasks,
            )
            documents.append(DocumentUploadResponse(
                id=document.id,
                filename=document.filename,
                file_size=document.file_size,
                status=document.status.value,
                created_at=document.created_at,
            ))
        except (UnsupportedFileTypeError, FileUploadError) as e:
            errors.append({
                "filename": file.filename,
                "error": str(e),
            })
    
    logger.info(
        f"用户 {current_user.id} 批量上传文档: "
        f"成功={len(documents)}, 失败={len(errors)}, kb_id={knowledge_base_id}"
    )
    
    return BatchUploadResponse(documents=documents, errors=errors)


@router.get(
    "",
    response_model=DocumentListResponse,
    summary="获取文档列表",
    description="获取指定知识库的文档列表，支持分页。",
)
def get_documents(
    knowledge_base_id: int,
    skip: int = 0,
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取文档列表"""
    service = RAGService(db)
    
    try:
        documents, total = service.get_documents(
            kb_id=knowledge_base_id,
            user_id=current_user.id,
            skip=skip,
            limit=limit,
        )
    except KnowledgeBaseNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="知识库不存在",
        )
    
    items = [
        DocumentResponse(
            id=doc.id,
            knowledge_base_id=doc.knowledge_base_id,
            filename=doc.filename,
            file_size=doc.file_size,
            file_type=doc.file_type,
            status=doc.status.value,
            chunk_count=doc.chunk_count,
            error_message=doc.error_message,
            created_at=doc.created_at,
        )
        for doc in documents
    ]
    
    return DocumentListResponse(total=total, items=items)


@router.get(
    "/{document_id}/status",
    response_model=DocumentStatusResponse,
    summary="获取文档处理状态",
    description="获取指定文档的处理状态和进度。",
)
def get_document_status(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    获取文档处理状态
    
    需求引用:
        - 需求3.10: 用户查询文档处理状态
    """
    service = RAGService(db)
    
    try:
        status_response = service.get_document_status(document_id, current_user.id)
    except DocumentNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="文档不存在",
        )
    
    return DocumentStatusResponse(
        document_id=status_response.document_id,
        status=status_response.status,
        progress=status_response.progress,
        chunk_count=status_response.chunk_count,
        error_message=status_response.error_message,
    )


@router.get(
    "/{document_id}/preview",
    response_model=DocumentPreviewResponse,
    summary="获取文档预览",
    description="获取文档的前1000个字符的文本内容预览。",
)
def get_document_preview(
    document_id: int,
    max_chars: int = 1000,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    获取文档预览
    
    需求引用:
        - 需求3.8: 用户请求文档预览，返回文档的前1000个字符的文本内容
    """
    service = RAGService(db)
    
    # 获取文档信息
    try:
        doc_status = service.get_document_status(document_id, current_user.id)
    except DocumentNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="文档不存在",
        )
    
    # 获取预览内容
    try:
        content = service.get_document_preview(
            document_id=document_id,
            user_id=current_user.id,
            max_chars=max_chars,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取文档预览失败: {str(e)}",
        )
    
    # 获取文档详情
    from app.repositories.document_repository import DocumentRepository
    doc_repo = DocumentRepository(db)
    document = doc_repo.get_by_id(document_id)
    
    return DocumentPreviewResponse(
        document_id=document_id,
        filename=document.filename if document else "Unknown",
        content=content,
        total_length=len(content),  # 这里简化处理，实际应该返回完整文档长度
    )


@router.delete(
    "/{document_id}",
    response_model=MessageResponse,
    summary="删除文档",
    description="删除指定文档及其向量数据。",
)
def delete_document(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    删除文档
    
    需求引用:
        - 需求3.9: 用户删除文档，删除文件、数据库记录和向量数据库中的相关向量
    """
    service = RAGService(db)
    
    try:
        success = service.delete_document(document_id, current_user.id)
    except DocumentNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="文档不存在",
        )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="删除文档失败",
        )
    
    logger.info(f"用户 {current_user.id} 删除文档: id={document_id}")
    
    return MessageResponse(message="文档删除成功")


# 导出
__all__ = ['router']
