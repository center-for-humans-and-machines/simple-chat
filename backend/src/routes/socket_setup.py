import uuid
from datetime import datetime

import socketio
from fastapi import HTTPException
from src.models import get_settings
from src.models.message import ConversationMessage, Conversations
from src.models.models import Project
from src.utils.db import create_image, create_message
from src.utils.helpers import (create_system_message_based_on_prev_rounds,
                               get_custom_system_message, get_openai_backend,
                               get_or_create_participant, get_response,
                               store_search_parameters, upload)
from src.utils.llm_model import init_model_endpoint
from src.utils.logging import setup_logger

settings = get_settings()
logger = setup_logger(__name__)

sio_server = socketio.AsyncServer(async_mode="asgi", cors_allowed_origins="*")

sio_app = socketio.ASGIApp(socketio_server=sio_server, socketio_path="/")


@sio_server.event
async def connect(sid, environ, auth):
    logger.info(f"Client is connected with sid : {sid}")
    session_id = uuid.uuid4().hex
    await sio_server.emit("session_id", {"session_id": session_id}, sid)


@sio_server.event
async def initial_message_to_server(sid, data):
    logger.info(f"initial_message_to_server is called with sid : {sid}")

    # check if there is a project with this pid
    project = await Project.find_many({"project_id": data["data"]["pid"]}).to_list()
    if len(project) == 0:
        await sio_server.emit(
            "pid_not_found",
            {"message": f"project with pid {data['data']['pid']} not found."},
            sid,
        )
        return
    else:
        if "active" in project[0].dict():
            if project[0].active == False:
                await sio_server.emit(
                    "pid_not_found",
                    {
                        "message": f"project with pid {data['data']['pid']} is deactivated."
                    },
                    sid,
                )
                return

        else:
            await sio_server.emit(
                "pid_not_found",
                {
                    "message": f"project with pid {data['data']['pid']} is too old to run."
                },
                sid,
            )
            return

    await store_search_parameters(data["data"], data["session_id"])

    system_message = project[0].system_message
    custom_system_message_id = "none"
    custom_system_message = {}
    if "system_message_id" in data["data"]:
        custom_system_message = await get_custom_system_message(
            data["data"]["system_message_id"]
        )
        # logger.info("custom_system_message")
        # logger.info(custom_system_message)
        # logger.info("\n\n\n\n\n")

        if custom_system_message == False:
            # there was no system_message with that id, then use default_system_message
            pass
        else:
            custom_system_message_id = data["data"]["system_message_id"]
            system_message = custom_system_message.system_message

    initial_messages = [
        ConversationMessage(
            content=system_message,
            role="system",
            timestamp=str(datetime.now()),
            type="text",
        )
    ]

    experiment_id_name = (
        data["data"]["experiment_id"] if "experiment_id" in data["data"] else -1
    )
    participant_id = (
        data["data"]["participant_id"]
        if "participant_id" in data["data"]
        else -1  # why we are not putting a random value here?
    )

    await sio_server.emit("set_participant_id", {"participant_id": participant_id}, sid)

    if "model" in data["data"]:
        model = data["data"]["model"]
    else:
        model = settings.openai_default_model

    if model == "deepseekr1":
        model = "together_ai-deepseek-ai/DeepSeek-R1"  # because of the / in the name of the model.

    elif model == "Llama-3.3-70B-Instruct-Turbo":
        model = "together_ai-meta-llama/Llama-3.3-70B-Instruct-Turbo"  # because of the / in the name of the model.

    current_round_number = 0
    if "round" in data["data"]:
        current_round_number = int(data["data"]["round"])
        if current_round_number > 1:
            prev_round_messages = await create_system_message_based_on_prev_rounds(
                data["data"]["pid"],
                experiment_id_name,
                participant_id,
                current_round_number,
            )
            if len(prev_round_messages) > 0:
                initial_messages = prev_round_messages

    new_conversation = Conversations(
        project_id=data["data"]["pid"],  # pid is project_id
        conversation_id=data["session_id"],
        created_at=str(datetime.now()),
        participant_id=participant_id,
        experiment_id=experiment_id_name,
        model=model,
        messages=initial_messages,
        custom_system_message_id=custom_system_message_id,
        multi_rounds=current_round_number,
    )
    await new_conversation.insert()

    logger.info(
        data,
        title=f"participant {participant_id} Received Initial Message",
    )
    message = await create_message(
        content=system_message,
        role="system",
    )

    participant, is_blacklisted = await get_or_create_participant(participant_id)

    if is_blacklisted:
        logger.info(f"Kicking out participant {participant_id}")
        message = await create_message(
            content="The conversation with ChatGPT comes to an end now. Please wait for the end of the timer to progress with the survey",
            role="system",
        )

    await sio_server.emit("message_to_client", message, sid)

    # is assistant first TRUE
    logger.info("custom_system_message")
    logger.info(custom_system_message)
    if custom_system_message:
        if hasattr(custom_system_message, "assistant_first"):
            the_conversation = await Conversations.find_one(
                Conversations.conversation_id == data["session_id"]
            )

            if custom_system_message.assistant_first is True:
                if hasattr(custom_system_message, "first_message"):
                    if len(custom_system_message.first_message) > 0:
                        # first message should be send staticly.
                        new_conversation_message = ConversationMessage(
                            content=custom_system_message.first_message,
                            role="assistant",
                            timestamp=str(datetime.now()),
                            type="text",
                        )
                        the_conversation.messages.append(new_conversation_message)
                        await the_conversation.save()

                        response_data = {
                            "type": "message",
                            "data": await create_message(
                                content=custom_system_message.first_message,
                                role="assistant",
                            ),
                        }

                        await sio_server.emit("message_to_client", response_data, sid)

                    else:
                        # it means the LLM should generate the first message.
                        await generate_llm_response(
                            the_conversation, data, sio_server, sid, model
                        )

                else:
                    # it means the LLM should generate the first message.
                    await generate_llm_response(
                        the_conversation, data, sio_server, sid, model
                    )


async def generate_llm_response(the_conversation, data, sio_server, sid, model):
    openai_backend = await get_openai_backend(the_conversation.project_id)
    client = init_model_endpoint(model, openai_backend)

    response_message = await get_response(
        session_id=data["session_id"],
        experiment_id=the_conversation.experiment_id,
        messages=the_conversation.messages,
        client=client,
        model=the_conversation.model,
        participant_id=the_conversation.participant_id,
        sio_server=sio_server,
        sid=sid,
    )

    new_message = ConversationMessage(
        content=response_message["content"],
        role=response_message["role"],
        timestamp=response_message["timestamp"],
        type=response_message["type"],
    )
    the_conversation.messages.append(new_message)

    if response_message["content"] != "ExceptionError":
        await the_conversation.save()


@sio_server.event
async def text_message(sid, data):
    participant, is_blacklisted = await get_or_create_participant(
        data["participant_id"]
    )

    if is_blacklisted:
        logger.info(f"Kicking out participant {data['participant_id']}")
        message = await create_message(
            content="The conversation with ChatGPT comes to an end now. Please wait for the end of the timer to progress with the survey",
            role="system",
        )

    logger.info(data, title=f"participant {data['participant_id']} Received Message")

    new_conversation_message = ConversationMessage(
        content=data["data"]["content"],
        role=data["data"]["role"],
        timestamp=str(datetime.now()),
        type="text",
    )
    the_conversation = await Conversations.find_one(
        Conversations.conversation_id == data["session_id"]
    )
    the_conversation.messages.append(new_conversation_message)
    await the_conversation.save()

    message = await create_message(
        content=data["data"]["content"], role=data["data"]["role"]
    )

    for message in the_conversation.messages:
        logger.info(message, title=f"session  {data['session_id']} all messages")

    openai_backend = await get_openai_backend(the_conversation.project_id)
    client = init_model_endpoint(the_conversation.model, openai_backend)

    response_message = await get_response(
        session_id=data["session_id"],
        experiment_id=the_conversation.experiment_id,
        messages=the_conversation.messages,
        client=client,
        model=the_conversation.model,
        participant_id=the_conversation.participant_id,
        sio_server=sio_server,
        sid=sid,
    )

    new_conversation_message = ConversationMessage(
        content=response_message["content"],
        role=response_message["role"],
        timestamp=response_message["timestamp"],
        type=response_message["type"],
    )

    the_conversation.messages.append(new_conversation_message)

    if response_message["content"] != "ExceptionError":
        # the message is sent to user by chunks
        # here we just save the response.
        await the_conversation.save()


@sio_server.event
async def image_message(sid, data):
    message = create_image(
        content="",
    )

    url = await upload(data["data"]["content"]["image"], str(uuid.uuid4()))

    message["content"] = [
        {"type": "text", "text": data["data"]["content"]["prompt"]},
        {"type": "image_url", "image_url": {"url": url}},
    ]

    new_conversation_message = ConversationMessage(
        content=message["content"],
        role="user",
        timestamp=str(datetime.now()),
        type="image",
    )
    the_conversation = await Conversations.find_one(
        Conversations.conversation_id == data["session_id"]
    )
    the_conversation.messages.append(new_conversation_message)
    await the_conversation.save()

    messages = the_conversation.messages

    if len(messages) >= 20:
        raise HTTPException(status_code=400, detail="Too many messages in this session")

    openai_backend = await get_openai_backend(the_conversation.project_id)

    client = init_model_endpoint(the_conversation.model, openai_backend)

    response_message = await get_response(
        session_id=data["session_id"],
        experiment_id=the_conversation.experiment_id,
        messages=the_conversation.messages,
        client=client,
        model=the_conversation.model,
        participant_id=the_conversation.participant_id,
        sio_server=sio_server,
        sid=sid,
    )

    new_conversation_message = ConversationMessage(
        content=response_message["content"],
        role=response_message["role"],
        timestamp=response_message["timestamp"],
        type=response_message["type"],
    )
    the_conversation.messages.append(new_conversation_message)

    if response_message["content"] != "ExceptionError":
        # the message is sent to user by chunks
        # here we just save the response.
        await the_conversation.save()


@sio_server.event
async def fetch_project_info(sid, data):
    project_id = data.get("project_id")

    project = await Project.find_one({"project_id": project_id})
    if not project:
        await sio_server.emit(
            "project_info",
            {"error": f"Project with ID {project_id} not found."},
            to=sid,
        )
        return

    await sio_server.emit(
        "project_info",
        {
            "project_id": project.project_id,
            "system_message": project.system_message,
            "loading_message": project.loading_message,
            "active": project.active,
        },
        to=sid,
    )
