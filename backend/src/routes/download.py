# routes.py
import io

import pandas as pd
from fastapi import APIRouter, Body, HTTPException, Response
from src.models.message import Conversations, MessageDocument
from src.utils.db import get_param
from src.utils.logging import setup_logger
from starlette.responses import StreamingResponse

logger = setup_logger(__name__)

download_router = APIRouter(prefix="/download", tags=["download"])


# REST API endpoint to fetch messages for a given session ID
@download_router.get("/conversation/messages/json/{session_id}")
async def read_messages(session_id: str):
    conversation_doc = await Conversations.find_one(
        Conversations.conversation_id == session_id
    )
    if conversation_doc == None:
        raise HTTPException(
            status_code=404,
            detail=f"Conversation not found with session_id {session_id}",
        )
    return conversation_doc.messages


async def make_table_for_one_conversation(session_id):
    conversation_doc = await Conversations.find_one(
        Conversations.conversation_id == session_id
    )
    if conversation_doc == None:
        raise HTTPException(
            status_code=404,
            detail=f"Conversation not found with session_id {session_id}",
        )

    search_param_data = await get_param(session_id=session_id)
    search_parameters = search_param_data[0].search_parameters
    search_params_data = {
        key: search_parameters.get(key, None) for key in search_parameters.keys()
    }

    table = []
    for message in conversation_doc.messages:
        if message["type"] == "image":
            row = {
                "type": "image",
                "role": message["role"],
                "message": message["content"][0]["text"],
                "image_url": message["content"][1]["image_url"]["url"],
                "timestamp": message["timestamp"],
            }

        elif message["type"] == "text":
            row = {
                "type": "text",
                "role": message["role"],
                "message": message["content"],
                "image_url": "",
                "timestamp": message["timestamp"],
            }
        temp = {"session_id": conversation_doc.conversation_id}
        temp.update(search_params_data)
        temp.update(row)
        table.append(temp)

    return table


@download_router.get("/conversation/{session_id}")
async def download_csv(session_id: str, response: Response):
    table = await make_table_for_one_conversation(session_id=session_id)
    df = pd.DataFrame(table)

    stream = io.StringIO()
    df.to_csv(stream, index=False)

    response = StreamingResponse(iter([stream.getvalue()]), media_type="text/csv")
    response.headers["Content-Disposition"] = (
        f"attachment; filename=conversation_session_id_{session_id}.csv"
    )

    return response


@download_router.get("/experiment/{project_id}/{experiment_id}")
async def download_csv_experiment(
    project_id: str, experiment_id: str, response: Response
):
    conversations = await Conversations.find_many(
        {"project_id": project_id, "experiment_id": experiment_id}
    ).to_list()

    table = []
    for conversation in conversations:
        temp = await make_table_for_one_conversation(conversation.conversation_id)
        # logger.info(temp)
        table += temp

    df = pd.DataFrame(table)

    stream = io.StringIO()
    df.to_csv(stream, index=False)

    response = StreamingResponse(iter([stream.getvalue()]), media_type="text/csv")
    response.headers["Content-Disposition"] = (
        f"attachment; filename=experiment_id_{experiment_id}.csv"
    )

    return response


@download_router.get("/chat/{project_id}/{experiment_id}/{participant_id}")
async def download_chat_in_json(
    project_id: str, experiment_id: str, participant_id: str, response: Response
):
    filters = {
        "project_id": project_id,
        "experiment_id": experiment_id,
        "participant_id": participant_id,
    }
    conversations = await Conversations.find_many(filters).to_list()

    conversation = conversations[-1]
    messages = conversation.messages

    messages_to_send = []

    for message in messages:
        messages_to_send.append(
            {
                "role": message["role"],
                "content": message["content"],
            }
        )

    return {
        "document_id": conversation.id,
        "conversation_id": conversation.conversation_id,
        "chat": messages_to_send,
    }
