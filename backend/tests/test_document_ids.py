"""Routes return MongoDB document ids as strings, as they did with Pydantic 1."""

import httpx
import pytest
from bson import ObjectId
from src.models.message import Conversations
from src.models.models import CustomSystemMessage

from conftest import RESEARCHER, register_project


@pytest.mark.asyncio
async def test_register_returns_doc_id_as_string(client: httpx.AsyncClient) -> None:
    response = await register_project(client, "ids")

    assert response.status_code == 200
    body = response.json()
    assert ObjectId.is_valid(body["doc_id"])
    assert body["doc_id"] == body["project"]["_id"]


@pytest.mark.asyncio
async def test_custom_system_message_id_finds_the_message(client: httpx.AsyncClient) -> None:
    await register_project(client, "ids")

    response = await client.post(
        "/project/custom_system_message",
        json={
            "system_message": "You are a helpful assistant.",
            "project_id": "ids",
            "requested_by": RESEARCHER,
            "assistant_first": False,
            "first_message": "Hello",
        },
    )

    assert response.status_code == 200
    system_message_id = response.json()["system_message_id"]
    assert isinstance(system_message_id, str)
    stored = await CustomSystemMessage.find_one({"_id": ObjectId(system_message_id)})
    assert stored is not None
    assert stored.system_message == "You are a helpful assistant."


@pytest.mark.asyncio
async def test_chat_download_returns_document_id_as_string(client: httpx.AsyncClient) -> None:
    conversation = Conversations(
        conversation_id="session",
        created_at="2026-11-26",
        participant_id="participant",
        experiment_id="experiment",
        model="gpt-4o",
        project_id="ids",
    )
    await conversation.insert()

    response = await client.get("/download/chat/ids/experiment/participant")

    assert response.status_code == 200
    assert response.json()["document_id"] == str(conversation.id)
