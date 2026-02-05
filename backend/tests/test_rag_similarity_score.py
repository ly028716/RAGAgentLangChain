import pytest


@pytest.mark.asyncio
async def test_distance_to_similarity_not_zero_for_large_l2_distance():
    from langchain_core.documents import Document

    from app.langchain_integration.rag_chain import RAGManager

    class _VS:
        async def similarity_search_with_score(self, knowledge_base_id, query, k=5, filter_dict=None):
            doc = Document(page_content="c", metadata={"source": "d"})
            return [(doc, 10000.0)]

    manager = RAGManager(vector_store_manager=_VS())
    chunks = await manager._retrieve_documents([1], "q", 1)
    assert len(chunks) == 1
    assert chunks[0].similarity_score > 0.0

