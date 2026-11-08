from unittest.mock import AsyncMock, Mock

import httpx
import pytest
from src.main import app
from src.models.models import Project


@pytest.mark.asyncio
async def test_health_endpoint():
    async with httpx.AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_chat_rejects_unknown_project(monkeypatch):
    query = Mock()
    query.to_list = AsyncMock(return_value=[])
    monkeypatch.setattr(Project, "find_many", Mock(return_value=query))

    async with httpx.AsyncClient(app=app, base_url="http://test") as client:
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
