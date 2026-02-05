import json


def test_chat_stream_returns_mock_response_when_api_key_placeholder(
    client, auth_headers, monkeypatch
):
    from app.config import settings
    from app.core.llm import clear_llm_cache

    monkeypatch.setattr(settings, "debug", True, raising=False)
    monkeypatch.setattr(settings, "environment", "development", raising=False)
    monkeypatch.setattr(
        settings.tongyi, "dashscope_api_key", "DUMMY_DASHSCOPE_API_KEY", raising=False
    )
    clear_llm_cache()

    payload = {"conversation_id": None, "content": "你好", "config": {}}

    events = []
    with client.stream(
        "POST", "/api/v1/chat/stream", headers=auth_headers, json=payload
    ) as resp:
        assert resp.status_code == 200
        for line in resp.iter_lines():
            if not line:
                continue
            if line.startswith("data: "):
                data = line[6:].strip()
                if data == "[DONE]":
                    break
                events.append(json.loads(data))

    token_text = "".join(e.get("content", "") for e in events if e.get("type") == "token")
    assert "模拟回复" in token_text
    assert any(e.get("type") == "done" for e in events)

