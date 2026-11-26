import httpx
import pytest
import pytest_asyncio
from beanie import init_beanie
from mongomock_motor import AsyncMongoMockClient, AsyncMongoMockDatabase
from src.main import app
from src.models import __beanie_models__

RESEARCHER = "researcher@mpib-berlin.mpg.de"

_list_collection_names = AsyncMongoMockDatabase.list_collection_names


async def _list_collection_names_without_server_options(
    self: AsyncMongoMockDatabase,
    *args: object,
    authorizedCollections: bool | None = None,
    nameOnly: bool | None = None,
    **kwargs: object,
) -> list[str]:
    """List collection names, dropping options the in-memory database rejects.

    Beanie 2 calls ``list_collection_names(authorizedCollections=True,
    nameOnly=True)``, PyMongo's async API. mongomock-motor 0.0.36 forwards
    keyword arguments to mongomock, which accepts neither. Both options only
    matter to a real server: one limits the list to collections the user may
    read, the other skips collection metadata. Dropping them returns the same
    names in memory.

    Args:
        self: The in-memory database.
        *args: Positional arguments for mongomock's ``list_collection_names``.
        authorizedCollections: Ignored; a server-only option.
        nameOnly: Ignored; a server-only option.
        **kwargs: Other keyword arguments, passed on unchanged.

    Returns:
        The names of the collections in the database.
    """
    return await _list_collection_names(self, *args, **kwargs)


@pytest_asyncio.fixture
async def client(monkeypatch: pytest.MonkeyPatch):
    """Yield an HTTP client for the app, backed by an in-memory database."""
    monkeypatch.setattr(
        AsyncMongoMockDatabase,
        "list_collection_names",
        _list_collection_names_without_server_options,
    )
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
