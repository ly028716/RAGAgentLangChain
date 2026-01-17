"""
知识库数据访问层（Repository）

封装知识库相关的数据库操作，提供统一的数据访问接口。
实现CRUD操作、分页查询和文档计数功能。

需求引用:
    - 需求3.1: 用户创建知识库且提供名称和描述
"""

from typing import Optional, List, Tuple
from datetime import datetime
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc, func, or_, distinct

from app.models.knowledge_base import KnowledgeBase
from app.models.document import Document
from app.models.knowledge_base_permission import KnowledgeBasePermission


class KnowledgeBaseRepository:
    """
    知识库Repository类
    
    提供知识库数据的CRUD操作和查询功能。
    支持分页查询和文档计数。
    
    使用方式:
        repo = KnowledgeBaseRepository(db)
        kb = repo.create(user_id=1, name="技术文档库", description="存储技术文档")
        kbs, total = repo.get_by_user(user_id=1, skip=0, limit=20)
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
        user_id: int,
        name: str,
        description: Optional[str] = None,
        category: Optional[str] = None
    ) -> KnowledgeBase:
        """
        创建新知识库
        
        Args:
            user_id: 用户ID
            name: 知识库名称
            description: 知识库描述（可选）
            category: 知识库分类（可选）
        
        Returns:
            KnowledgeBase: 创建的知识库对象
        """
        knowledge_base = KnowledgeBase(
            user_id=user_id,
            name=name,
            description=description,
            category=category
        )
        self.db.add(knowledge_base)
        self.db.commit()
        self.db.refresh(knowledge_base)
        return knowledge_base
    
    def get_by_id(self, kb_id: int) -> Optional[KnowledgeBase]:
        """
        根据ID获取知识库
        
        Args:
            kb_id: 知识库ID
        
        Returns:
            Optional[KnowledgeBase]: 知识库对象，不存在则返回None
        """
        return self.db.query(KnowledgeBase).filter(
            KnowledgeBase.id == kb_id
        ).first()
    
    def get_by_id_and_user(
        self,
        kb_id: int,
        user_id: int
    ) -> Optional[KnowledgeBase]:
        """
        根据ID和用户ID获取知识库
        
        Args:
            kb_id: 知识库ID
            user_id: 用户ID
        
        Returns:
            Optional[KnowledgeBase]: 知识库对象，不存在或不属于该用户则返回None
        """
        return self.db.query(KnowledgeBase).filter(
            KnowledgeBase.id == kb_id,
            KnowledgeBase.user_id == user_id
        ).first()
    
    def get_by_user(
        self,
        user_id: int,
        skip: int = 0,
        limit: int = 20
    ) -> Tuple[List[KnowledgeBase], int]:
        """
        获取用户的知识库列表（分页）

        按更新时间倒序排列，返回知识库列表和总数。
        使用 joinedload 预加载文档关系，避免 N+1 查询问题。

        Args:
            user_id: 用户ID
            skip: 跳过的记录数
            limit: 返回的最大记录数

        Returns:
            Tuple[List[KnowledgeBase], int]: (知识库列表, 总数)
        """
        query = self.db.query(KnowledgeBase).filter(
            KnowledgeBase.user_id == user_id
        )

        # 获取总数
        total = query.count()

        # 按更新时间倒序排列并分页，使用 joinedload 预加载文档
        knowledge_bases = query.options(
            joinedload(KnowledgeBase.documents)
        ).order_by(
            desc(KnowledgeBase.updated_at)
        ).offset(skip).limit(limit).all()

        return knowledge_bases, total

    def get_accessible_by_user(
        self,
        user_id: int,
        skip: int = 0,
        limit: int = 20
    ) -> Tuple[List[KnowledgeBase], int]:
        """
        获取用户可访问的知识库列表（分页）

        访问规则：
        - 用户自己创建的知识库
        - visibility=public 的知识库（仅查看）
        - 通过 KnowledgeBasePermission 授权的知识库
        """
        query = self.db.query(KnowledgeBase).outerjoin(
            KnowledgeBasePermission,
            KnowledgeBase.id == KnowledgeBasePermission.knowledge_base_id
        ).filter(
            or_(
                KnowledgeBase.user_id == user_id,
                KnowledgeBase.visibility == "public",
                KnowledgeBasePermission.user_id == user_id
            )
        ).distinct()

        total = query.with_entities(func.count(distinct(KnowledgeBase.id))).scalar() or 0

        knowledge_bases = query.options(
            joinedload(KnowledgeBase.documents)
        ).order_by(
            desc(KnowledgeBase.updated_at)
        ).offset(skip).limit(limit).all()

        return knowledge_bases, total

    def get_accessible_by_id(
        self,
        kb_id: int,
        user_id: int
    ) -> Optional[KnowledgeBase]:
        """
        获取用户可访问的知识库（按ID）
        """
        return self.db.query(KnowledgeBase).outerjoin(
            KnowledgeBasePermission,
            KnowledgeBase.id == KnowledgeBasePermission.knowledge_base_id
        ).filter(
            KnowledgeBase.id == kb_id,
            or_(
                KnowledgeBase.user_id == user_id,
                KnowledgeBase.visibility == "public",
                KnowledgeBasePermission.user_id == user_id
            )
        ).first()

    
    def get_all_by_user(self, user_id: int) -> List[KnowledgeBase]:
        """
        获取用户的所有知识库（不分页）
        
        Args:
            user_id: 用户ID
        
        Returns:
            List[KnowledgeBase]: 知识库列表
        """
        return self.db.query(KnowledgeBase).filter(
            KnowledgeBase.user_id == user_id
        ).order_by(desc(KnowledgeBase.updated_at)).all()
    
    def get_by_category(
        self,
        user_id: int,
        category: str,
        skip: int = 0,
        limit: int = 20
    ) -> Tuple[List[KnowledgeBase], int]:
        """
        根据分类获取用户的知识库列表（分页）
        
        Args:
            user_id: 用户ID
            category: 知识库分类
            skip: 跳过的记录数
            limit: 返回的最大记录数
        
        Returns:
            Tuple[List[KnowledgeBase], int]: (知识库列表, 总数)
        """
        query = self.db.query(KnowledgeBase).filter(
            KnowledgeBase.user_id == user_id,
            KnowledgeBase.category == category
        )
        
        total = query.count()
        
        knowledge_bases = query.order_by(
            desc(KnowledgeBase.updated_at)
        ).offset(skip).limit(limit).all()
        
        return knowledge_bases, total
    
    def update(
        self,
        kb_id: int,
        user_id: int,
        name: Optional[str] = None,
        description: Optional[str] = None,
        category: Optional[str] = None
    ) -> Optional[KnowledgeBase]:
        """
        更新知识库信息
        
        Args:
            kb_id: 知识库ID
            user_id: 用户ID（用于权限验证）
            name: 新名称（可选）
            description: 新描述（可选）
            category: 新分类（可选）
        
        Returns:
            Optional[KnowledgeBase]: 更新后的知识库对象，知识库不存在或不属于该用户则返回None
        """
        knowledge_base = self.get_by_id_and_user(kb_id, user_id)
        if not knowledge_base:
            return None
        
        if name is not None:
            knowledge_base.name = name
        if description is not None:
            knowledge_base.description = description
        if category is not None:
            knowledge_base.category = category
        
        self.db.commit()
        self.db.refresh(knowledge_base)
        return knowledge_base
    
    def delete(
        self,
        kb_id: int,
        user_id: int
    ) -> bool:
        """
        删除知识库
        
        删除知识库及其所有文档（通过级联删除）。
        
        Args:
            kb_id: 知识库ID
            user_id: 用户ID（用于权限验证）
        
        Returns:
            bool: 删除成功返回True，知识库不存在或不属于该用户返回False
        """
        knowledge_base = self.get_by_id_and_user(kb_id, user_id)
        if not knowledge_base:
            return False
        
        self.db.delete(knowledge_base)
        self.db.commit()
        return True
    
    def count_by_user(self, user_id: int) -> int:
        """
        获取用户的知识库总数
        
        Args:
            user_id: 用户ID
        
        Returns:
            int: 知识库总数
        """
        return self.db.query(KnowledgeBase).filter(
            KnowledgeBase.user_id == user_id
        ).count()
    
    def get_document_count(self, kb_id: int) -> int:
        """
        获取知识库的文档数量
        
        Args:
            kb_id: 知识库ID
        
        Returns:
            int: 文档数量
        """
        return self.db.query(Document).filter(
            Document.knowledge_base_id == kb_id
        ).count()
    
    def exists(
        self,
        kb_id: int,
        user_id: int
    ) -> bool:
        """
        检查知识库是否存在且属于指定用户
        
        Args:
            kb_id: 知识库ID
            user_id: 用户ID
        
        Returns:
            bool: 存在返回True，否则返回False
        """
        return self.db.query(KnowledgeBase).filter(
            KnowledgeBase.id == kb_id,
            KnowledgeBase.user_id == user_id
        ).first() is not None
    
    def touch(self, kb_id: int) -> Optional[KnowledgeBase]:
        """
        更新知识库的更新时间
        
        用于在添加新文档后更新知识库的updated_at字段。
        
        Args:
            kb_id: 知识库ID
        
        Returns:
            Optional[KnowledgeBase]: 更新后的知识库对象，知识库不存在则返回None
        """
        knowledge_base = self.get_by_id(kb_id)
        if not knowledge_base:
            return None
        
        knowledge_base.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(knowledge_base)
        return knowledge_base
    
    def search_by_name(
        self,
        user_id: int,
        keyword: str,
        skip: int = 0,
        limit: int = 20
    ) -> Tuple[List[KnowledgeBase], int]:
        """
        根据名称关键字搜索知识库
        
        Args:
            user_id: 用户ID
            keyword: 搜索关键字
            skip: 跳过的记录数
            limit: 返回的最大记录数
        
        Returns:
            Tuple[List[KnowledgeBase], int]: (知识库列表, 总数)
        """
        query = self.db.query(KnowledgeBase).filter(
            KnowledgeBase.user_id == user_id,
            KnowledgeBase.name.ilike(f"%{keyword}%")
        )
        
        total = query.count()
        
        knowledge_bases = query.order_by(
            desc(KnowledgeBase.updated_at)
        ).offset(skip).limit(limit).all()
        
        return knowledge_bases, total


# 导出
__all__ = ['KnowledgeBaseRepository']
