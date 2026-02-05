import pytest

from app.repositories.agent_repository import AgentExecutionRepository
from app.services.agent_service import AgentService


def test_agent_tools_total_is_full_count(client, auth_headers):
    for i in range(3):
        resp = client.post(
            "/api/v1/agent/tools",
            headers=auth_headers,
            json={"name": f"t_total_{i}", "description": "d", "config": {"i": i}},
        )
        assert resp.status_code == 201

    resp = client.get("/api/v1/agent/tools", headers=auth_headers, params={"limit": 1})
    assert resp.status_code == 200
    payload = resp.json()
    assert payload["total"] == 3
    assert len(payload["items"]) == 1


def test_agent_tools_total_respects_filters(client, auth_headers):
    tool_ids = []
    for i in range(3):
        resp = client.post(
            "/api/v1/agent/tools",
            headers=auth_headers,
            json={"name": f"t_enabled_{i}", "description": "d", "config": None},
        )
        assert resp.status_code == 201
        tool_ids.append(resp.json()["id"])

    resp = client.put(
        f"/api/v1/agent/tools/{tool_ids[0]}",
        headers=auth_headers,
        json={"is_enabled": False},
    )
    assert resp.status_code == 200

    resp = client.get(
        "/api/v1/agent/tools", headers=auth_headers, params={"is_enabled": True, "limit": 1}
    )
    assert resp.status_code == 200
    payload = resp.json()
    assert payload["total"] == 2
    assert len(payload["items"]) == 1


def test_add_step_is_idempotent(db, test_user):
    repo = AgentExecutionRepository(db)
    execution = repo.create(user_id=test_user.id, task="t")
    step = {
        "step_number": 1,
        "thought": "x",
        "action": "calculator",
        "action_input": {"expression": "1+1"},
        "observation": "2",
        "timestamp": "2026-01-01T00:00:00Z",
    }

    repo.add_step(execution.id, step)
    repo.add_step(execution.id, step)

    execution = repo.get_by_id(execution.id)
    assert execution is not None
    assert len(execution.steps) == 1


@pytest.mark.asyncio
async def test_stream_error_does_not_leak_internal_message(db, test_user):
    class DummyAgentManager:
        async def stream_execute_task(self, task, tool_ids=None, max_iterations=10):
            yield {"type": "error", "data": {"message": "INTERNAL_SECRET"}}

    service = AgentService(db)
    service.agent_manager = DummyAgentManager()

    events = []
    async for event in service.stream_execute_task(user_id=test_user.id, task="t"):
        events.append(event)
        if event["type"] == "error":
            break

    assert any(
        e["type"] == "error" and e["data"]["message"] == "任务执行失败" for e in events
    )

