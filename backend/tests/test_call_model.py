from types import SimpleNamespace

import pytest
from src.models.models import TokenBudget, TokenUsage
from src.utils import llm_model
from src.utils.llm_model import call_model, count_prompt_tokens, num_tokens_from_string

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
    prompt = count_prompt_tokens(MESSAGES, "gpt-4o")
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


def stream_with_usage(text, usage):
    async def stream():
        yield chunk(text)
        # with stream_options.include_usage the last chunk has no choices, only usage
        yield SimpleNamespace(choices=[], usage=usage)

    return stream()


@pytest.mark.parametrize(
    "usage",
    [SimpleNamespace(prompt_tokens=7, completion_tokens=900), {"prompt_tokens": 7, "completion_tokens": 900}],
)
async def test_provider_usage_is_recorded_instead_of_the_estimate(make_project, monkeypatch, usage):
    project = await make_project(max_tokens_per_project=100_000)
    sent = []

    async def completion(client, **kwargs):
        sent.append(kwargs)
        return stream_with_usage("short reply", usage)

    monkeypatch.setattr(llm_model, "completion_with_backoff", completion)

    await run(project)

    [record] = await TokenUsage.find_many({"project_id": project.project_id}).to_list()
    # 900 completion tokens include hidden reasoning that tiktoken cannot see
    assert (record.prompt_tokens, record.completion_tokens, record.estimated) == (7, 900, False)
    budget = await TokenBudget.find_one({"key": f"project:{project.project_id}"})
    assert budget.tokens == 907


async def test_busy_budget_is_not_reported_as_a_reached_cap(make_project, monkeypatch):
    project = await make_project(max_tokens_per_project=100_000)

    async def busy(*args, **kwargs):
        return None, llm_model.BUSY

    monkeypatch.setattr(llm_model, "reserve_tokens", busy)

    result, events = await run(project)

    assert result == "ExceptionError"
    assert "limit_reached" not in events
    assert events == ["message_to_client", "message_end"]


class RecordingCompletions:
    def __init__(self):
        self.calls = []

    async def create(self, **kwargs):
        self.calls.append(kwargs)
        return SimpleNamespace()


def fake_client():
    completions = RecordingCompletions()
    return SimpleNamespace(chat=SimpleNamespace(completions=completions)), completions.calls


async def test_reasoning_models_get_max_completion_tokens():
    client, calls = fake_client()

    await llm_model.completion_with_backoff(
        client, model="gpt-5.1", messages=MESSAGES, temperature=0.7, stream=True, max_tokens=500
    )

    [kwargs] = calls
    assert "max_tokens" not in kwargs and "temperature" not in kwargs
    assert kwargs["extra_body"]["max_completion_tokens"] == 500
    assert kwargs["extra_body"]["stream_options"] == {"include_usage": True}


async def test_other_models_keep_max_tokens():
    client, calls = fake_client()

    await llm_model.completion_with_backoff(
        client, model="gpt-4o", messages=MESSAGES, temperature=0.7, stream=False, max_tokens=500
    )

    [kwargs] = calls
    assert kwargs["max_tokens"] == 500
    assert "extra_body" not in kwargs


def test_old_azure_versions_are_not_asked_for_stream_usage(monkeypatch):
    from openai import AsyncAzureOpenAI

    client = AsyncAzureOpenAI(api_key="x", azure_endpoint="https://x.test", api_version="2024-02-01")
    monkeypatch.setattr(llm_model.settings, "azure_openai_api_version", "2024-02-01")
    assert not llm_model.reports_stream_usage(client)
    monkeypatch.setattr(llm_model.settings, "azure_openai_api_version", "2024-10-21")
    assert llm_model.reports_stream_usage(client)
