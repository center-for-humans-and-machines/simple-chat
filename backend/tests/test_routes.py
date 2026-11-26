from unittest.mock import AsyncMock, Mock

import httpx
import pytest
from fastapi.testclient import TestClient
from src.main import app
from src.models.models import Project


def make_client() -> httpx.AsyncClient:
    """Return an HTTP client that calls the app in process."""
    return httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test")


@pytest.mark.asyncio
async def test_health_endpoint():
    async with make_client() as client:
        response = await client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_startup_initialises_the_database(monkeypatch):
    init_db = AsyncMock()
    monkeypatch.setattr("src.main.init_db", init_db)

    with TestClient(app):
        pass

    init_db.assert_awaited_once()


@pytest.mark.asyncio
async def test_chat_rejects_unknown_project(monkeypatch):
    query = Mock()
    query.to_list = AsyncMock(return_value=[])
    monkeypatch.setattr(Project, "find_many", Mock(return_value=query))

    async with make_client() as client:
        response = await client.post(
            "/llm/call",
            json={
                "project_id": "missing",
                "requested_by": "researcher@example.com",
                "model": "gpt-4o-mini",
                "chat": [{"role": "user", "content": "Hello"}],
            },
        )

    assert response.status_code == 400
    assert response.json() == {"detail": "project not found"}
