"""Tests run against a real MongoDB, because the limits rely on its atomic updates.

Start one with `docker run --rm -p 27017:27017 mongo` and set TEST_MONGO_URL
(default mongodb://localhost:27017). Each test uses a fresh database.
"""
import os
import uuid

os.environ.setdefault("MONGO_URL", "mongodb://localhost:27017")
os.environ.setdefault("DATABASE_NAME", "simplechat_test")

import motor.motor_asyncio
import pytest
from beanie import init_beanie
from pymongo.errors import ServerSelectionTimeoutError

TEST_MONGO_URL = os.environ.get("TEST_MONGO_URL", "mongodb://localhost:27017")


@pytest.fixture
async def db():
    from src.models import __beanie_models__

    client = motor.motor_asyncio.AsyncIOMotorClient(
        TEST_MONGO_URL, serverSelectionTimeoutMS=2000
    )
    try:
        await client.admin.command("ping")
    except ServerSelectionTimeoutError:
        pytest.skip(f"no MongoDB at {TEST_MONGO_URL}")

    name = f"simplechat_test_{uuid.uuid4().hex[:8]}"
    await init_beanie(database=client[name], document_models=__beanie_models__)
    yield client[name]
    await client.drop_database(name)
    client.close()


@pytest.fixture
def make_project(db):
    from src.models.models import Project, ProjectLimits

    async def make(**limits):
        project = Project(
            project_id=uuid.uuid4().hex,
            created_at="now",
            created_by="tester",
            system_message="You are a test.",
            active=True,
            limits=ProjectLimits(**limits),
        )
        await project.insert()
        return project

    return make
