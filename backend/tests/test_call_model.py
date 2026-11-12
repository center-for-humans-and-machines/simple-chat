from types import SimpleNamespace

import pytest
from src.models.models import TokenBudget, TokenUsage
from src.utils import llm_model
from src.utils.llm_model import call_model, estimate_prompt_tokens, num_tokens_from_string

MESSAGES = [{"role": "user", "content": "hello"}]


class FakeServer:
    def __init__(self):
        self.events = []

    async def emit(self, event, data=None, to=None, **kwargs):
        self.events.append(event)


def chunk(text):
    return SimpleNamespace(choices=[SimpleNamespace(delta=SimpleNamespace(content=text))])


async def broken_stream():
    yield chunk("part one ")
    yield chunk("part two")
    raise ConnectionError("stream dropped")


@pytest.fixture
def provider(monkeypatch):
    calls = []

    async def completion(client, **kwargs):
        calls.append(kwargs)
        if client == "refused":
            raise RuntimeError("provider refused the request")
        return broken_stream()

    monkeypatch.setattr(llm_model, "completion_with_backoff", completion)
    return calls


async def run(project, client="ok"):
    server = FakeServer()
    result = await call_model(
        server, "sid", MESSAGES, "gpt-4o", client, "conv", "exp",
        participant_id="p1", project_id=project.project_id,
    )
    return result, server.events


async def test_failed_stream_records_the_tokens_the_provider_billed(make_project, provider):
    project = await make_project(max_tokens_per_project=100_000)

    result, events = await run(project)

    assert result == "ExceptionError"
    assert events[-1] == "message_end"
    usage = await TokenUsage.find_many({"project_id": project.project_id}).to_list()
    prompt = estimate_prompt_tokens(MESSAGES, "gpt-4o")
    completion = num_tokens_from_string("part one part two")
    assert [(u.prompt_tokens, u.completion_tokens) for u in usage] == [(prompt, completion)]
    # the budget keeps the billed tokens instead of releasing the whole reservation
    budget = await TokenBudget.find_one({"key": f"project:{project.project_id}"})
    assert budget.tokens == prompt + completion


async def test_refused_request_records_nothing(make_project, provider):
    project = await make_project(max_tokens_per_project=100_000)

    result, _ = await run(project, client="refused")

    assert result == "ExceptionError"
    assert await TokenUsage.find_many({"project_id": project.project_id}).count() == 0
    budget = await TokenBudget.find_one({"key": f"project:{project.project_id}"})
    assert budget.tokens == 0
