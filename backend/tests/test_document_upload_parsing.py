import pytest


def test_text_loader_decodes_gbk(tmp_path):
    from app.langchain_integration.document_loaders import DocumentLoaderFactory

    p = tmp_path / "sample.txt"
    content = "中文内容：你好，世界！"
    p.write_bytes(content.encode("gbk"))

    docs = DocumentLoaderFactory.load_document(str(p), "txt")
    assert docs
    assert "你好" in docs[0].page_content


def test_markdown_loader_falls_back_on_decode_error(tmp_path):
    from app.langchain_integration.document_loaders import DocumentLoaderFactory

    p = tmp_path / "sample.md"
    content = "# 标题\n\n中文：你好"
    p.write_bytes(content.encode("gbk"))

    docs = DocumentLoaderFactory.load_document(str(p), "md")
    assert docs
    assert "标题" in docs[0].page_content


@pytest.mark.asyncio
async def test_vector_store_uses_mock_embeddings_when_api_key_placeholder(tmp_path, monkeypatch):
    from app.config import settings
    from app.core.vector_store import DevMockEmbeddings, VectorStoreManager

    monkeypatch.setattr(settings, "debug", False, raising=False)
    monkeypatch.setattr(settings, "environment", "development", raising=False)

    m = VectorStoreManager(
        persist_directory=str(tmp_path / "chroma"),
        api_key="DUMMY_DASHSCOPE_API_KEY",
    )
    assert isinstance(m.embeddings, DevMockEmbeddings)

