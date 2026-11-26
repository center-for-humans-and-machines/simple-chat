"""Values that Pydantic 1 coerced and Pydantic 2 rejects are still stored."""

from unittest.mock import AsyncMock

import httpx
import pytest
from conftest import RESEARCHER, make_completion, register_project
from src.models.message import Conversations, Participant
from src.models.models import LlmCall
from src.routes import llm, socket_setup


@pytest.mark.asyncio
async def test_llm_call_stores_the_response(
    client: httpx.AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    await register_project(client, "llm")
    monkeypatch.setattr(
        llm, "call_llm_model", AsyncMock(return_value=make_completion("Hello back"))
    )

    response = await client.post(
        "/llm/call",
        json={
            "project_id": "llm",
            "requested_by": RESEARCHER,
            "model": "gpt-4o",
            "chat": [{"role": "user", "content": "Hello"}],
        },
    )

    assert response.status_code == 200
    assert response.json() == "Hello back"
    stored = await LlmCall.find_one({"project_id": "llm"})
    assert stored is not None
    assert stored.response["choices"][0]["message"]["content"] == "Hello back"


@pytest.mark.asyncio
async def test_initial_message_without_ids_creates_conversation(
    client: httpx.AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    await register_project(client, "socket")
    emit = AsyncMock()
    monkeypatch.setattr(socket_setup.sio_server, "emit", emit)

    await socket_setup.initial_message_to_server(
        "sid", {"session_id": "session", "data": {"pid": "socket"}}
    )

    conversation = await Conversations.find_one({"conversation_id": "session"})
    assert conversation is not None
    assert conversation.participant_id == "-1"
    assert conversation.experiment_id == "-1"
    assert await Participant.find_one({"participant_id": "-1"}) is not None
    emit.assert_any_await("set_participant_id", {"participant_id": "-1"}, "sid")
