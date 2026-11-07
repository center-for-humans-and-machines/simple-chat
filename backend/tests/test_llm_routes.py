import asyncio
from types import SimpleNamespace

import httpx
import pytest
from fastapi import FastAPI
from src.models.models import TokenBudget
from src.routes import llm
from src.utils.usage import record_usage


@pytest.fixture
def provider(monkeypatch):
    """Fake provider: replies use all of max_tokens and report usage like OpenAI."""
    calls = []

    async def completion(client, **kwargs):
        calls.append(kwargs)
        await asyncio.sleep(0)
        completion_tokens = kwargs.get("max_tokens", 50)
        return SimpleNamespace(
            usage=SimpleNamespace(
                prompt_tokens=llm.estimate_prompt_tokens(kwargs["messages"], kwargs["model"]),
                completion_tokens=completion_tokens,
            ),
            choices=[SimpleNamespace(message=SimpleNamespace(content="ok"))],
            dict=lambda: {},
        )

    async def backend(project_id):
        return "openai"

    monkeypatch.setattr(llm, "completion_with_backoff", completion)
    monkeypatch.setattr(llm, "get_openai_backend", backend)
    monkeypatch.setattr(llm, "init_model_endpoint", lambda model, backend: None)
    monkeypatch.setattr(llm, "LlmCall", FakeLlmCall)
    return calls


class FakeLlmCall:
    def __init__(self, **kwargs):
        pass

    async def insert(self):
        pass


@pytest.fixture
async def api(db):
    app = FastAPI()
    app.include_router(llm.llm_router)
    async with httpx.AsyncClient(app=app, base_url="http://test") as client:
        yield client


def body(project):
    return {
        "project_id": project.project_id,
        "requested_by": project.created_by,
        "model": "gpt-4o",
        "chat": [{"role": "user", "content": "hello"}],
    }


@pytest.mark.parametrize("path", ["/llm/call", "/llm/json_call", "/llm/function_call"])
async def test_calls_are_refused_once_the_project_cap_is_reached(make_project, api, provider, path):
    project = await make_project(max_tokens_per_project=100)
    await record_usage(project.project_id, "gpt-4o", 100, 0, estimated=False)

    payload = body(project)
    if path == "/llm/function_call":
        payload["function"] = {"name": "f", "parameters": {"type": "object"}}
    response = await api.post(path, json=payload)

    assert response.status_code == 429
    assert provider == []


async def test_call_reply_is_bounded_by_the_remaining_cap(make_project, api, provider):
    project = await make_project(max_tokens_per_project=100)

    response = await api.post("/llm/call", json=body(project))

    assert response.status_code == 200
    assert response.json() == "ok"
    assert 0 < provider[0]["max_tokens"] < 100
    # settled to the provider-reported usage
    budget = await TokenBudget.find_one({"key": f"project:{project.project_id}"})
    assert budget.tokens == 100


async def test_concurrent_calls_stay_within_the_project_cap(make_project, api, provider):
    cap = 500
    project = await make_project(max_tokens_per_project=cap)

    responses = await asyncio.gather(*(api.post("/llm/call", json=body(project)) for _ in range(20)))

    assert {r.status_code for r in responses} <= {200, 429}
    budget = await TokenBudget.find_one({"key": f"project:{project.project_id}"})
    assert budget.tokens <= cap


async def test_call_without_a_cap_is_not_bounded(make_project, api, provider):
    project = await make_project()

    response = await api.post("/llm/call", json=body(project))

    assert response.status_code == 200
    assert "max_tokens" not in provider[0]


async def test_image_cost_is_reserved_before_the_call(make_project, api, provider):
    # a text-only estimate (a few tokens) would let this call through
    project = await make_project(max_tokens_per_project=1000)
    payload = body(project)
    payload["chat"] = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "what is this?"},
                {"type": "image_url", "image_url": {"url": "https://example.com/a.jpg"}},
            ],
        }
    ]

    response = await api.post("/llm/call", json=payload)

    assert response.status_code == 429
    assert provider == []
