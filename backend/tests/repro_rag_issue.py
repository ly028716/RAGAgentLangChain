
import asyncio
import os
import sys
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.vector_store import get_vector_store_manager
from app.langchain_integration.rag_chain import get_rag_manager
from langchain_core.documents import Document

async def repro_rag():
    # 1. 准备测试数据
    kb_id = 9999  # 使用一个测试ID
    manager = get_vector_store_manager()
    
    # 清理旧数据
    try:
        manager.delete_collection(kb_id)
    except:
        pass
        
    # 添加测试文档
    docs = [
        Document(page_content="Python是一种解释型、面向对象、动态数据类型的高级程序设计语言。", metadata={"source": "test_doc.txt", "chunk_index": 0}),
        Document(page_content="FastAPI 是一个用于构建 API 的现代、快速（高性能）的 web 框架，使用 Python 3.6+ 并基于标准的 Python 类型提示。", metadata={"source": "test_doc.txt", "chunk_index": 1})
    ]
    
    print(f"正在向知识库 {kb_id} 添加文档...")
    await manager.add_documents(kb_id, docs, document_id=1)
    
    # 2. 测试 RAG 检索
    rag_manager = get_rag_manager()
    question = "什么是FastAPI？"
    
    print(f"正在执行 RAG 查询: {question}")
    
    # 测试普通查询
    response = await rag_manager.query(
        knowledge_base_ids=[kb_id],
        question=question,
        top_k=2
    )
    
    print("\n=== 普通查询结果 ===")
    print(f"Answer: {response.answer}")
    print(f"Sources count: {len(response.sources)}")
    for source in response.sources:
        print(f"- {source.document_name} (score: {source.similarity_score}): {source.content[:50]}...")
        
    # 测试流式查询
    print("\n=== 流式查询结果 ===")
    async for chunk in rag_manager.stream_query(
        knowledge_base_ids=[kb_id],
        question=question,
        top_k=2
    ):
        if chunk["type"] == "sources":
            print(f"Sources received: {len(chunk['sources'])}")
        elif chunk["type"] == "token":
            print(chunk["content"], end="", flush=True)
        elif chunk["type"] == "done":
            print("\nDone.")
            
    # 清理
    manager.delete_collection(kb_id)

if __name__ == "__main__":
    asyncio.run(repro_rag())
