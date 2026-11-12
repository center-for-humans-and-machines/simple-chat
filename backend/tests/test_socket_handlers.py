import pytest
from src.routes import socket_setup


@pytest.fixture
def emitted(monkeypatch):
    events = []

    async def emit(event, data=None, to=None, **kwargs):
        events.append(event)

    monkeypatch.setattr(socket_setup.sio_server, "emit", emit)
    return events


@pytest.mark.parametrize(
    "handler, content",
    [
        (socket_setup.text_message, {"content": "hi", "role": "user"}),
        (socket_setup.image_message, {"content": {"prompt": "hi", "image": ""}}),
    ],
)
async def test_message_before_the_conversation_exists_is_handed_back(
    db, emitted, handler, content
):
    # the participant pressed Send before initial_message_to_server created the conversation
    await handler("sid", {"session_id": "not-created-yet", "participant_id": "p1", "data": content})

    assert emitted == ["message_not_delivered"]


async def test_conversation_ready_is_sent_once_the_conversation_is_stored(
    make_project, monkeypatch
):
    from src.models.message import Conversations

    project = await make_project()
    stored_when_ready = []

    async def emit(event, data=None, to=None, **kwargs):
        if event == "conversation_ready":
            found = await Conversations.find_one({"conversation_id": data["session_id"]})
            stored_when_ready.append(found is not None)

    async def get_session(sid):
        return {"ip": "1.2.3.4"}

    monkeypatch.setattr(socket_setup.sio_server, "emit", emit)
    monkeypatch.setattr(socket_setup.sio_server, "get_session", get_session)

    await socket_setup.initial_message_to_server(
        "sid",
        {"session_id": "s1", "data": {"pid": project.project_id, "model": "gpt-4o"}},
    )

    assert stored_when_ready == [True]


async def test_image_upload_failure_hands_the_message_back(make_project, emitted, monkeypatch):
    from src.models.message import Conversations

    project = await make_project()
    await Conversations(
        conversation_id="c1",
        project_id=project.project_id,
        participant_id="p1",
        experiment_id="e1",
        model="gpt-4o",
        messages=[],
        created_at="now",
    ).insert()

    async def no_storage(img, message_id):
        raise RuntimeError("Image upload needs object storage: set the S3_* variables.")

    async def get_session(sid):
        return {"ip": "1.2.3.4"}

    monkeypatch.setattr(socket_setup, "upload", no_storage)
    monkeypatch.setattr(socket_setup.sio_server, "get_session", get_session)

    await socket_setup.image_message(
        "sid",
        {"session_id": "c1", "participant_id": "p1", "data": {"content": {"prompt": "hi", "image": ""}}},
    )

    assert emitted == ["message_not_delivered"]
    stored = await Conversations.find_one({"conversation_id": "c1"})
    assert stored.messages == [] and stored.user_turns == 0
