import asyncio
from types import SimpleNamespace

import pytest
from src.models.models import TokenBudget
from src.utils import llm_model
from src.utils.limits import MAX_COMPLETION_TOKENS, reserve_tokens, settle_tokens
from src.utils.llm_model import (DEFAULT_IMAGE_TOKENS, IMAGE_TOKENS, call_model,
                                 estimate_prompt_tokens, num_tokens_from_string)
from src.utils.usage import record_usage


async def budget(key):
    return (await TokenBudget.find_one({"key": key})).tokens


async def test_no_cap_reserves_nothing(make_project):
    project = await make_project()
    reservation, reason = await reserve_tokens(project, 50, "conv")
    assert reason is None
    assert reservation.max_tokens is None and reservation.holds == []


async def test_reply_is_bounded_by_the_remaining_budget(make_project):
    project = await make_project(max_tokens_per_project=100)
    await record_usage(project.project_id, "gpt-4o", 80, 10, estimated=True)

    reservation, reason = await reserve_tokens(project, 5)

    assert reason is None
    # 100 - 90 used - 5 prompt
    assert reservation.max_tokens == 5
    assert await budget(f"project:{project.project_id}") == 100


async def test_reply_is_bounded_by_the_default_far_below_the_cap(make_project):
    project = await make_project(max_tokens_per_project=1_000_000)
    reservation, _ = await reserve_tokens(project, 10)
    assert reservation.max_tokens == MAX_COMPLETION_TOKENS


async def test_no_room_for_a_reply_is_refused(make_project):
    project = await make_project(max_tokens_per_project=100)
    await record_usage(project.project_id, "gpt-4o", 80, 10, estimated=True)

    reservation, reason = await reserve_tokens(project, 10)

    assert reservation is None
    assert reason == "max_tokens_per_project"
    assert await budget(f"project:{project.project_id}") == 90


async def test_conversation_cap_is_reserved_together_with_the_project_cap(make_project):
    project = await make_project(max_tokens_per_project=10_000, max_tokens_per_conversation=50)

    reservation, reason = await reserve_tokens(project, 20, "conv")
    assert reason is None and reservation.max_tokens == 30

    # the conversation cap is full, and the project budget is left untouched
    _, reason = await reserve_tokens(project, 1, "conv")
    assert reason == "max_tokens_per_conversation"
    assert await budget(f"project:{project.project_id}") == 50


async def test_settle_replaces_the_reservation_with_the_usage(make_project):
    project = await make_project(max_tokens_per_project=1000)
    reservation, _ = await reserve_tokens(project, 10)

    await settle_tokens(reservation, 25)

    assert await budget(f"project:{project.project_id}") == 25


async def test_concurrent_calls_cannot_pass_the_cap_together(make_project):
    cap = 1000
    project = await make_project(max_tokens_per_project=cap)

    results = await asyncio.gather(*(reserve_tokens(project, 100) for _ in range(30)))
    reservations = [r for r, _ in results if r is not None]

    reserved = sum(amount for r in reservations for _, amount in r.holds)
    assert reservations
    assert reserved <= cap
    assert await budget(f"project:{project.project_id}") == reserved

    # every call uses its whole reply: the total still stays within the cap
    for r in reservations:
        await settle_tokens(r, 100 + r.max_tokens)
    assert await budget(f"project:{project.project_id}") <= cap


class FakeClient:
    """Streams a fixed reply and records the arguments of each call."""

    def __init__(self, reply):
        self.reply = reply
        self.calls = []
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self.create))

    async def create(self, **kwargs):
        self.calls.append(kwargs)

        async def stream():
            for word in self.reply.split(" "):
                delta = SimpleNamespace(content=word + " ")
                yield SimpleNamespace(choices=[SimpleNamespace(delta=delta)])

        return stream()


class FakeSio:
    def __init__(self):
        self.events = []

    async def emit(self, event, data, sid):
        self.events.append(event)


async def chat_call(project, client, sio, session_id="conv", messages=None, model="gpt-4o"):
    return await call_model(
        sio_server=sio,
        sid="sid",
        messages=messages or [{"role": "user", "content": "hello there"}],
        model=model,
        client=client,
        session_id=session_id,
        experiment_id="exp",
        participant_id="p1",
        project_id=project.project_id,
    )


async def test_chat_call_passes_the_bound_and_settles_to_recorded_usage(make_project):
    project = await make_project(max_tokens_per_project=1000)
    client = FakeClient("hi back")

    reply = await chat_call(project, client, FakeSio())

    assert reply.strip() == "hi back"
    max_tokens = client.calls[0]["max_tokens"]
    assert 0 < max_tokens <= 1000
    # the budget holds exactly the recorded (estimated) usage, not the reservation
    assert await budget(f"project:{project.project_id}") < 20


async def test_chat_call_is_not_made_without_room_for_a_reply(make_project):
    project = await make_project(max_tokens_per_project=100)
    await record_usage(project.project_id, "gpt-4o", 98, 0, estimated=True)
    client, sio = FakeClient("unused"), FakeSio()

    reply = await chat_call(project, client, sio)

    assert reply == "ExceptionError"
    assert client.calls == []
    assert sio.events == ["limit_reached"]


IMAGE_MESSAGE = {
    "role": "user",
    "content": [
        {"type": "text", "text": "what is this?"},
        {"type": "image_url", "image_url": {"url": "https://example.com/a.jpg"}},
    ],
}


@pytest.fixture
def no_image_download(monkeypatch):
    # calculate_limits downloads images to check their size
    monkeypatch.setattr(
        llm_model.requests, "get", lambda url: SimpleNamespace(status_code=200, content=b"x")
    )


def test_estimate_counts_message_overhead_and_images():
    text = estimate_prompt_tokens([{"role": "user", "content": "hello"}], "gpt-4")
    assert text == num_tokens_from_string("hello") + 4 + 3

    with_image = estimate_prompt_tokens([IMAGE_MESSAGE], "gpt-4o")
    assert with_image >= IMAGE_TOKENS["gpt-4o"] + num_tokens_from_string("what is this?")
    # gpt-4o-mini bills images at a much higher token rate
    assert estimate_prompt_tokens([IMAGE_MESSAGE], "gpt-4o-mini") > with_image
    assert estimate_prompt_tokens([IMAGE_MESSAGE], "together_ai-x") >= DEFAULT_IMAGE_TOKENS


def test_estimate_adds_a_margin_for_other_tokenizers():
    messages = [{"role": "user", "content": "word " * 400}]
    exact = estimate_prompt_tokens(messages, "gpt-4")
    assert estimate_prompt_tokens(messages, "gpt-4o") > exact
    assert estimate_prompt_tokens(
        messages, "together_ai-meta-llama/Llama-3.3-70B-Instruct-Turbo"
    ) > estimate_prompt_tokens(messages, "gpt-4o")


async def test_image_chat_call_is_refused_when_the_image_does_not_fit(
    make_project, no_image_download
):
    # the text alone is a few tokens: a text-only estimate would allow this call
    project = await make_project(max_tokens_per_project=1000)
    client, sio = FakeClient("unused"), FakeSio()

    reply = await chat_call(project, client, sio, messages=[IMAGE_MESSAGE])

    assert reply == "ExceptionError"
    assert client.calls == []
    assert sio.events == ["limit_reached"]


async def test_image_chat_call_reserves_and_records_the_image(make_project, no_image_download):
    project = await make_project(max_tokens_per_project=2000)
    client = FakeClient("a cat")

    await chat_call(project, client, FakeSio(), messages=[IMAGE_MESSAGE])

    prompt = estimate_prompt_tokens([IMAGE_MESSAGE], "gpt-4o")
    assert client.calls[0]["max_tokens"] == 2000 - prompt
    # usage is recorded and settled with the same estimate that was reserved
    assert await budget(f"project:{project.project_id}") == prompt + num_tokens_from_string(
        "a cat "
    )


async def test_prompt_of_many_short_messages_is_not_underestimated(make_project):
    # 60 one-token messages: text alone is ~60 tokens, the provider counts ~300
    messages = [{"role": "user", "content": "hi"}] * 60
    project = await make_project(max_tokens_per_project=150)
    client, sio = FakeClient("unused"), FakeSio()

    reply = await chat_call(project, client, sio, messages=messages)

    assert reply == "ExceptionError"
    assert client.calls == []


async def test_reply_counted_longer_than_max_tokens_stays_within_the_cap(make_project):
    # the provider stops at max_tokens; a tiktoken count of the reply can be
    # higher when the tokenizers differ, which must not push the budget past the cap
    project = await make_project(max_tokens_per_project=60)
    client = FakeClient("word " * 200)  # ignores max_tokens

    await chat_call(project, client, FakeSio())

    assert await budget(f"project:{project.project_id}") == 60
