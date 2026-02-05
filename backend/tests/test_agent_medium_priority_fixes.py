import pytest

from app.repositories.agent_repository import AgentExecutionRepository
from app.services.agent_service import AgentService
from app.models.agent_execution import ExecutionStatus


def test_tools_pagination_is_stable_and_ordered(client, auth_headers):
    created = []
    for i in range(3):
        resp = client.post(
            "/api/v1/agent/tools",
            headers=auth_headers,
            json={"name": f"t_page_{i}", "description": "d", "config": {"i": i}},
        )
        assert resp.status_code == 201
        created.append(resp.json())

    resp = client.get(
        "/api/v1/agent/tools", headers=auth_headers, params={"skip": 0, "limit": 2}
    )
    assert resp.status_code == 200
    page1 = resp.json()["items"]

    resp = client.get(
        "/api/v1/agent/tools", headers=auth_headers, params={"skip": 1, "limit": 2}
    )
    assert resp.status_code == 200
    page2 = resp.json()["items"]

    assert page1[1]["id"] == page2[0]["id"]
    assert page1[0]["id"] < page1[1]["id"]
    assert page2[0]["id"] < page2[1]["id"]


def test_invalid_tool_type_returns_422(client, auth_headers):
    resp = client.get(
        "/api/v1/agent/tools", headers=auth_headers, params={"tool_type": "invalid"}
    )
    assert resp.status_code == 422


def test_invalid_execution_status_returns_422(client, auth_headers):
    resp = client.get(
        "/api/v1/agent/executions", headers=auth_headers, params={"status": "invalid"}
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_execute_task_updates_execution_in_single_update(db, test_user):
    class DummyAgentManager:
        async def execute_task(self, task, tool_ids=None, max_iterations=10):
            return {
                "result": "ok",
                "steps": [
                    {
                        "step_number": 1,
                        "thought": "x",
                        "action": "calculator",
                        "action_input": {"expression": "1+1"},
                        "observation": "2",
                        "timestamp": "2026-01-01T00:00:00Z",
                    }
                ],
                "status": "completed",
                "error": None,
            }

    service = AgentService(db)
    service.agent_manager = DummyAgentManager()

    result = await service.execute_task(user_id=test_user.id, task="t")
    assert result["status"] == ExecutionStatus.COMPLETED.value
    assert result["result"] == "ok"
    assert len(result["steps"]) == 1
    assert result["completed_at"] is not None

    repo = AgentExecutionRepository(db)
    execution = repo.get_by_id(result["execution_id"])
    assert execution is not None
    assert execution.status == ExecutionStatus.COMPLETED
    assert execution.completed_at is not None
    assert execution.result == "ok"
    assert isinstance(execution.steps, list) and len(execution.steps) == 1

