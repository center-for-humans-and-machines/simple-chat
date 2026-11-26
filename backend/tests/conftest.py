import httpx
import pytest_asyncio
from beanie import init_beanie
from mongomock_motor import AsyncMongoMockClient
from src.main import app
from src.models import __beanie_models__

RESEARCHER = "researcher@mpib-berlin.mpg.de"


@pytest_asyncio.fixture
async def client():
    """Yield an HTTP client for the app, backed by an in-memory database."""
    database = AsyncMongoMockClient()["test"]
    await init_beanie(database=database, document_models=__beanie_models__)
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as http:
        yield http


async def register_project(client: httpx.AsyncClient, project_id: str) -> httpx.Response:
    """Register a project owned by RESEARCHER through the API."""
    return await client.post(
        "/project/register",
        json={"project_id": project_id, "requested_by": RESEARCHER, "system_message": "hi"},
    )
