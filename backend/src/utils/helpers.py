import base64
from datetime import datetime
from typing import List

import boto3
from botocore.client import Config
from bson import ObjectId
from openai import AsyncAzureOpenAI, AsyncOpenAI
from src.models import get_settings
from src.models.message import (Conversations, MessageDocument, Participant,
                                SearchParameters, parse_from_openai,
                                parse_to_openai)
from src.models.models import CustomSystemMessage, Project
from src.utils.llm_model import call_model
from src.utils.logging import setup_logger

logger = setup_logger(__name__)

settings = get_settings()
s3_session = boto3.session.Session()
s3 = s3_session.client(
    service_name="s3",
    aws_access_key_id=settings.s3_access_key,
    aws_secret_access_key=settings.s3_secret_key,
    endpoint_url=settings.s3_endpoint,
    config=Config(signature_version="s3v4"),
    region_name=settings.s3_region_name,
)


async def store_search_parameters(search_params_data, session_id):
    search_params = SearchParameters(
        session_id=session_id,
        timestamp=str(datetime.now()),
        search_parameters=search_params_data,
    )
    await search_params.insert()


async def get_or_create_participant(participant_id: str) -> (Participant, bool):
    # Check if the participant exists
    participant = await Participant.find_one({"participant_id": participant_id})

    # If not, create a new participant
    if not participant:
        participant = Participant(participant_id=participant_id)
        await participant.insert()

    # Check if the participant is blacklisted
    is_blacklisted = participant.black_listed

    logger.debug(f"created participant {participant}")

    return participant, is_blacklisted


async def get_response(
    sio_server,
    sid,
    session_id: str,
    experiment_id: str,
    messages: List[MessageDocument],
    client: AsyncOpenAI | AsyncAzureOpenAI,
    model: str,
    participant_id: str = None,
) -> MessageDocument:
    omessages = [parse_to_openai(message) for message in messages]
    full_response = await call_model(
        messages=omessages,
        model=model,
        client=client,
        session_id=session_id,
        experiment_id=experiment_id,
        participant_id=participant_id,
        sio_server=sio_server,
        sid=sid,
    )

    res_message = parse_from_openai(full_response)

    return res_message


async def upload(img, message_id):
    # Decode the base64 string
    img = base64.b64decode(img)
    s3_file_name = f"{message_id}.jpg"
    s3.put_object(Body=img, Bucket=settings.s3_bucket_name, Key=s3_file_name)
    url = s3.generate_presigned_url(
        "get_object",
        Params={"Bucket": settings.s3_bucket_name, "Key": s3_file_name},
        ExpiresIn=3600,
    )
    return url


async def get_custom_system_message(system_message_id):
    custom_system_message = await CustomSystemMessage.find_one(
        {"_id": ObjectId(system_message_id)}
    )

    if not custom_system_message:
        return False

    return custom_system_message


async def create_system_message_based_on_prev_rounds(
    pid, experiment_id, participant_id, current_round
):
    looking_for_round = current_round - 1

    prev_converation = (
        await Conversations.find(
            {
                "experiment_id": experiment_id,
                "participant_id": participant_id,
                "multi_rounds": looking_for_round,
            }
        )
        .sort("-_id")  # Sort by _id descending to get the latest
        .limit(1)
        .to_list()
    )

    if len(prev_converation) == 0:
        return []

    return prev_converation[0].messages


async def get_openai_backend(project_id):
    projects = await Project.find_many({"project_id": project_id}).to_list()

    if len(projects) == 0:
        return "not found"

    project = projects[0]

    if "openai_backend" in project:
        return project.openai_backend

    else:
        return "azure"  # default mode
