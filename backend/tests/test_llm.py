"""The LLM endpoints send the right request to the model and store its reply."""

from unittest.mock import AsyncMock, Mock

import httpx
import pytest
from conftest import RESEARCHER, make_completion, register_project
from src.models.models import LlmCall
from src.routes import llm

JSON_OBJECT_FORMAT = {"type": "json_object"}
JSON_REPLY = '{"greeting": "Hello"}'


def mock_completion(monkeypatch: pytest.MonkeyPatch, content: str) -> AsyncMock:
    """Replace the model call with a mock that answers with `content`.

    Args:
        monkeypatch: The pytest fixture used to patch the LLM route module.
        content: The assistant message the mocked model returns.

    Returns:
        The mock that stands in for `completion_with_backoff`.
    """
    completion = AsyncMock(return_value=make_completion(content))
    monkeypatch.setattr(llm, "init_model_endpoint", Mock(return_value=Mock()))
    monkeypatch.setattr(llm, "completion_with_backoff", completion)
    return completion


def llm_request(project_id: str) -> dict:
    """Return the request body for an LLM call by the owner of `project_id`."""
    return {
        "project_id": project_id,
        "requested_by": RESEARCHER,
        "model": "gpt-4o",
        "chat": [{"role": "user", "content": "Say hello in JSON"}],
    }


@pytest.mark.asyncio
async def test_json_call_requests_a_json_object_and_stores_the_response(
    client: httpx.AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    await register_project(client, "json")
    completion = mock_completion(monkeypatch, JSON_REPLY)
    request = llm_request("json")

    response = await client.post("/llm/json_call", json=request)

    assert response.status_code == 200
    assert response.json() == JSON_REPLY
    completion.assert_awaited_once()
    sent = completion.await_args.kwargs
    assert sent["response_format"] == JSON_OBJECT_FORMAT
    assert sent["model"] == request["model"]
    assert sent["messages"] == request["chat"]
    stored = await LlmCall.find_one({"project_id": "json"})
    assert stored is not None
    assert stored.response["choices"][0]["message"]["content"] == JSON_REPLY


@pytest.mark.asyncio
async def test_call_does_not_request_a_response_format(
    client: httpx.AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    await register_project(client, "text")
    completion = mock_completion(monkeypatch, "Hello back")

    response = await client.post("/llm/call", json=llm_request("text"))

    assert response.status_code == 200
    assert response.json() == "Hello back"
    completion.assert_awaited_once()
    assert "response_format" not in completion.await_args.kwargs
