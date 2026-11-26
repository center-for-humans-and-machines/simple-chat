"""Values that Pydantic 1 coerced and Pydantic 2 rejects are still stored."""

from unittest.mock import AsyncMock

import httpx
import pytest
from conftest import RESEARCHER, make_completion, register_project
from src.models.message import Conversations, Participant
from src.models.models import LlmCall
from src.routes import llm, socket_setup
from src.utils.helpers import get_or_create_participant


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


@pytest.mark.asyncio
async def test_initial_message_with_numeric_ids_creates_conversation(
    client: httpx.AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    await register_project(client, "numeric")
    emit = AsyncMock()
    monkeypatch.setattr(socket_setup.sio_server, "emit", emit)

    await socket_setup.initial_message_to_server(
        "sid",
        {
            "session_id": "numeric-session",
            "data": {"pid": "numeric", "participant_id": 7, "experiment_id": 3},
        },
    )

    conversation = await Conversations.find_one({"conversation_id": "numeric-session"})
    assert conversation is not None
    assert conversation.participant_id == "7"
    assert conversation.experiment_id == "3"
    emit.assert_any_await("set_participant_id", {"participant_id": "7"}, "sid")


@pytest.mark.asyncio
async def test_numeric_participant_id_finds_the_stored_participant(
    client: httpx.AsyncClient,
) -> None:
    await Participant(participant_id="7", black_listed=True).insert()

    participant, is_blacklisted = await get_or_create_participant(7)

    assert participant.participant_id == "7"
    assert is_blacklisted is True
    assert await Participant.find({"participant_id": "7"}).count() == 1


@pytest.mark.asyncio
async def test_second_round_with_numeric_ids_continues_the_first(
    client: httpx.AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    await register_project(client, "rounds")
    monkeypatch.setattr(socket_setup.sio_server, "emit", AsyncMock())
    ids = {"pid": "rounds", "participant_id": 7, "experiment_id": 3}
    await socket_setup.initial_message_to_server(
        "sid", {"session_id": "round-1", "data": {**ids, "round": 1}}
    )
    first = await Conversations.find_one({"conversation_id": "round-1"})
    first.messages.append(
        {"content": "From round one", "role": "user", "timestamp": "t", "type": "text"}
    )
    await first.save()

    await socket_setup.initial_message_to_server(
        "sid", {"session_id": "round-2", "data": {**ids, "round": 2}}
    )

    second = await Conversations.find_one({"conversation_id": "round-2"})
    assert [message["content"] for message in second.messages] == ["hi", "From round one"]


@pytest.mark.asyncio
async def test_conversation_stored_with_numeric_ids_still_loads(
    client: httpx.AsyncClient,
) -> None:
    await Conversations.get_pymongo_collection().insert_one(
        {
            "conversation_id": "stored-with-numbers",
            "created_at": "2024-01-01 00:00:00",
            "participant_id": -1,
            "experiment_id": 12,
            "model": "gpt-4o",
            "project_id": "numeric",
            "messages": [],
        }
    )

    response = await client.get("/dashboard/conversation/stored-with-numbers")

    assert response.status_code == 200
    assert response.json()["participant_id"] == "-1"
    assert response.json()["experiment_id"] == "12"


@pytest.mark.asyncio
async def test_conversation_rejects_a_boolean_id(client: httpx.AsyncClient) -> None:
    with pytest.raises(ValueError, match="participant_id"):
        Conversations(
            conversation_id="boolean",
            created_at="2024-01-01 00:00:00",
            participant_id=True,
            experiment_id="experiment",
            model="gpt-4o",
            project_id="numeric",
        )
