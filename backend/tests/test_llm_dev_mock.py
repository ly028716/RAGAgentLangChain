import pytest


@pytest.mark.asyncio
async def test_streaming_llm_uses_dev_mock_when_api_key_placeholder(monkeypatch):
    from app.config import settings
    from app.core.llm import clear_llm_cache, get_streaming_llm

    monkeypatch.setattr(settings, "debug", True, raising=False)
    monkeypatch.setattr(settings, "environment", "development", raising=False)
    monkeypatch.setattr(settings.tongyi, "dashscope_api_key", "DUMMY_DASHSCOPE_API_KEY", raising=False)

    clear_llm_cache()

    llm = get_streaming_llm()
    chunks = []
    async for chunk in llm.llm.astream("用户: 你好"):
        chunks.append(chunk)

    text = "".join(chunks)
    assert "模拟回复" in text
    assert "你好" in text

