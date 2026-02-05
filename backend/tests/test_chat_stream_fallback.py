import json


class _FailingPrivateStreamLLM:
    async def _astream(self, prompt, **kwargs):
        raise TypeError("Additional kwargs key output_tokens already exists")
        if False:
            yield ""

    async def ainvoke(self, prompt, **kwargs):
        return "fallback-ok"


class _FailingPublicStreamLLM:
    async def astream(self, prompt, **kwargs):
        raise TypeError("Additional kwargs key output_tokens already exists")
        if False:
            yield ""

    async def ainvoke(self, prompt, **kwargs):
        return "fallback-ok"


class _Wrapper:
    def __init__(self, llm):
        self._llm = llm

    @property
    def llm(self):
        return self._llm


def _collect_sse_events(resp):
    events = []
    for line in resp.iter_lines():
        if not line:
            continue
        if line.startswith("data: "):
            data = line[6:].strip()
            if data == "[DONE]":
                break
            events.append(json.loads(data))
    return events


def test_chat_stream_falls_back_to_invoke_when_private_stream_fails(
    client, auth_headers, monkeypatch
):
    from app.config import settings
    from app.core.llm import clear_llm_cache
    from app.langchain_integration.chains import ConversationManager

    monkeypatch.setattr(settings, "debug", True, raising=False)
    monkeypatch.setattr(settings, "environment", "development", raising=False)
    monkeypatch.setattr(
        settings.tongyi, "dashscope_api_key", "DUMMY_DASHSCOPE_API_KEY", raising=False
    )
    clear_llm_cache()

    monkeypatch.setattr(
        ConversationManager,
        "_get_llm",
        lambda self, config, streaming=False: _Wrapper(_FailingPrivateStreamLLM()),
        raising=True,
    )

    payload = {"conversation_id": None, "content": "你好", "config": {}}
    with client.stream("POST", "/api/v1/chat/stream", headers=auth_headers, json=payload) as resp:
        assert resp.status_code == 200
        events = _collect_sse_events(resp)

    token_text = "".join(e.get("content", "") for e in events if e.get("type") == "token")
    assert "fallback-ok" in token_text
    assert any(e.get("type") == "done" for e in events)


def test_chat_stream_falls_back_to_invoke_when_public_stream_fails(
    client, auth_headers, monkeypatch
):
    from app.config import settings
    from app.core.llm import clear_llm_cache
    from app.langchain_integration.chains import ConversationManager

    monkeypatch.setattr(settings, "debug", True, raising=False)
    monkeypatch.setattr(settings, "environment", "development", raising=False)
    monkeypatch.setattr(
        settings.tongyi, "dashscope_api_key", "DUMMY_DASHSCOPE_API_KEY", raising=False
    )
    clear_llm_cache()

    monkeypatch.setattr(
        ConversationManager,
        "_get_llm",
        lambda self, config, streaming=False: _Wrapper(_FailingPublicStreamLLM()),
        raising=True,
    )

    payload = {"conversation_id": None, "content": "你好", "config": {}}
    with client.stream("POST", "/api/v1/chat/stream", headers=auth_headers, json=payload) as resp:
        assert resp.status_code == 200
        events = _collect_sse_events(resp)

    token_text = "".join(e.get("content", "") for e in events if e.get("type") == "token")
    assert "fallback-ok" in token_text
    assert any(e.get("type") == "done" for e in events)

