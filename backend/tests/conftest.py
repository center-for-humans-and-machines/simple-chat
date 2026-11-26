import httpx
import pytest_asyncio
from beanie import init_beanie
from mongomock_motor import AsyncMongoMockClient
from openai.types.chat import ChatCompletion, ChatCompletionMessage
from openai.types.chat.chat_completion import Choice
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


def make_completion(content: str) -> ChatCompletion:
    """Return an OpenAI chat completion with one assistant message."""
    return ChatCompletion(
        id="completion",
        created=0,
        model="gpt-4o",
        object="chat.completion",
        choices=[
            Choice(
                index=0,
                finish_reason="stop",
                message=ChatCompletionMessage(role="assistant", content=content),
            )
        ],
    )
