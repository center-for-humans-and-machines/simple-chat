# routes.py
import json
from datetime import datetime
from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from src.models.models import LlmCall, Project
from src.utils.helpers import get_openai_backend
from src.utils.limits import reserve_tokens, settle_tokens
from src.utils.llm_model import (completion_with_backoff, init_model_endpoint,
                                 num_tokens_from_string)
from src.utils.logging import setup_logger
from src.utils.usage import record_response_usage

logger = setup_logger(__name__)

llm_router = APIRouter(prefix="/llm", tags=["llm"])


class LlmCallInput(BaseModel):
    project_id: str
    requested_by: str
    model: str
    chat: List[Dict[str, Any]]


# tokens a provider adds per message and per reply, and a generous count per image
MESSAGE_OVERHEAD_TOKENS = 4
REPLY_OVERHEAD_TOKENS = 3
IMAGE_TOKENS = 1105


def estimate_prompt_tokens(messages: list, extra: str = "") -> int:
    tokens = REPLY_OVERHEAD_TOKENS + num_tokens_from_string(extra)
    for message in messages:
        tokens += MESSAGE_OVERHEAD_TOKENS
        content = message.get("content") or ""
        if isinstance(content, list):
            for part in content:
                if part.get("type") == "text":
                    tokens += num_tokens_from_string(part.get("text", ""))
                elif part.get("type") == "image_url":
                    tokens += IMAGE_TOKENS
        else:
            tokens += num_tokens_from_string(str(content))
    return tokens


async def call_within_token_cap(project: Project, messages: list, call, extra_prompt: str = ""):
    """Run a non-streaming completion within the project's token cap.

    `call` gets the completion kwargs that bound the reply (max_tokens) and returns the response.
    """
    reservation, reason = await reserve_tokens(
        project, estimate_prompt_tokens(messages, extra_prompt)
    )
    if reason:
        raise HTTPException(status_code=429, detail="project token limit reached")

    kwargs = {}
    if reservation.max_tokens is not None:
        kwargs["max_tokens"] = reservation.max_tokens

    used = 0
    try:
        response = await call(**kwargs)
        usage = getattr(response, "usage", None)
        if usage is not None:
            used = usage.prompt_tokens + usage.completion_tokens
        return response
    finally:
        # keep the budget equal to the recorded usage
        await settle_tokens(reservation, used)


async def call_llm_model(model: str, messages: list, project_id: str, **kwargs):
    openai_backend = await get_openai_backend(project_id)
    client = init_model_endpoint(model, openai_backend)

    response = await completion_with_backoff(
        client,
        model=model,
        messages=messages,
        temperature=0.7,
        stream=False,
        **kwargs,
    )

    return response


@llm_router.post("/call")
async def send_message(data: LlmCallInput):
    project = await Project.find_many({"project_id": data.project_id}).to_list()
    if len(project) == 0:
        raise HTTPException(status_code=400, detail="project not found")
    else:
        if "active" in project[0].dict():
            if project[0].active == False:
                raise HTTPException(status_code=401, detail="project is deactivated")

        else:
            raise HTTPException(status_code=402, detail="project is too old to run")

    if data.requested_by != project[0].created_by:
        raise HTTPException(status_code=400, detail="inputs are not compatible")

    response = await call_within_token_cap(
        project[0],
        data.chat,
        lambda **kwargs: call_llm_model(
            model=data.model, messages=data.chat, project_id=data.project_id, **kwargs
        ),
    )

    new_llm_call = LlmCall(
        project_id=data.project_id,
        chat=data.chat,
        response=response,
        created_at=str(datetime.now()),
    )

    await new_llm_call.insert()
    await record_response_usage(data.project_id, data.model, response, source="llm_api")

    return response.choices[0].message.content


@llm_router.post("/json_call")
async def send_message(data: LlmCallInput):
    project = await Project.find_many({"project_id": data.project_id}).to_list()
    if len(project) == 0:
        raise HTTPException(status_code=400, detail="project not found")
    else:
        if "active" in project[0].dict():
            if project[0].active == False:
                raise HTTPException(status_code=401, detail="project is deactivated")

        else:
            raise HTTPException(status_code=402, detail="project is too old to run")

    if data.requested_by != project[0].created_by:
        raise HTTPException(status_code=400, detail="inputs are not compatible")

    response = await call_within_token_cap(
        project[0],
        data.chat,
        lambda **kwargs: call_llm_model(
            model=data.model,
            messages=data.chat,
            project_id=data.project_id,
            response_format={"type": "json_object"},
            **kwargs,
        ),
    )

    new_llm_call = LlmCall(
        project_id=data.project_id,
        chat=data.chat,
        response=response,
        created_at=str(datetime.now()),
    )

    await new_llm_call.insert()
    await record_response_usage(data.project_id, data.model, response, source="llm_api")

    return response.choices[0].message.content


class LlmFunctionCallInput(BaseModel):
    project_id: str
    requested_by: str
    chat: List[Dict[str, Any]]
    function: dict


async def function_call_llm_model(messages: list, project_id: str, function, **kwargs):
    openai_backend = await get_openai_backend(project_id)
    client = init_model_endpoint("gpt-4o-mini", openai_backend)

    response = await completion_with_backoff(
        client,
        model="gpt-4o-mini",
        messages=messages,
        temperature=0.7,
        stream=False,
        tools=[{"type": "function", "function": function}],
        tool_choice={"type": "function", "function": {"name": function["name"]}},
        **kwargs,
    )

    return response


@llm_router.post("/function_call")
async def function_call(data: LlmFunctionCallInput):
    project = await Project.find_many({"project_id": data.project_id}).to_list()
    if len(project) == 0:
        raise HTTPException(status_code=400, detail="project not found")
    else:
        if "active" in project[0].dict():
            if project[0].active == False:
                raise HTTPException(status_code=401, detail="project is deactivated")

        else:
            raise HTTPException(status_code=402, detail="project is too old to run")

    if data.requested_by != project[0].created_by:
        raise HTTPException(status_code=400, detail="inputs are not compatible")

    response = await call_within_token_cap(
        project[0],
        data.chat,
        lambda **kwargs: function_call_llm_model(
            messages=data.chat, project_id=data.project_id, function=data.function, **kwargs
        ),
        extra_prompt=json.dumps(data.function),
    )

    new_llm_call = LlmCall(
        project_id=data.project_id,
        chat=data.chat,
        response=response,
        created_at=str(datetime.now()),
    )

    await new_llm_call.insert()
    await record_response_usage(data.project_id, "gpt-4o-mini", response, source="llm_api")

    return response.choices
