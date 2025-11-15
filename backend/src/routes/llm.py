# routes.py
from datetime import datetime
from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from src.models.models import LlmCall, Project
from src.utils.helpers import get_openai_backend
from src.utils.llm_model import completion_with_backoff, init_model_endpoint
from src.utils.logging import setup_logger

logger = setup_logger(__name__)

llm_router = APIRouter(prefix="/llm", tags=["llm"])


class LlmCallInput(BaseModel):
    project_id: str
    requested_by: str
    model: str
    chat: List[Dict[str, Any]]


async def call_llm_model(model: str, messages: list, project_id: str):
    openai_backend = await get_openai_backend(project_id)
    client = init_model_endpoint(model, openai_backend)

    response = await completion_with_backoff(
        client,
        model=model,
        messages=messages,
        temperature=0.7,
        stream=False,
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

    response = await call_llm_model(
        model=data.model, messages=data.chat, project_id=data.project_id
    )

    new_llm_call = LlmCall(
        project_id=data.project_id,
        chat=data.chat,
        response=response,
        created_at=str(datetime.now()),
    )

    await new_llm_call.insert()

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

    response = await call_llm_model(
        model=data.model,
        messages=data.chat,
        project_id=data.project_id,
        response_format={"type": "json_object"},
    )

    new_llm_call = LlmCall(
        project_id=data.project_id,
        chat=data.chat,
        response=response,
        created_at=str(datetime.now()),
    )

    await new_llm_call.insert()

    return response.choices[0].message.content


class LlmFunctionCallInput(BaseModel):
    project_id: str
    requested_by: str
    chat: List[Dict[str, Any]]
    function: dict


async def function_call_llm_model(messages: list, project_id: str, function):
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

    response = await function_call_llm_model(
        messages=data.chat, project_id=data.project_id, function=data.function
    )

    new_llm_call = LlmCall(
        project_id=data.project_id,
        chat=data.chat,
        response=response,
        created_at=str(datetime.now()),
    )

    await new_llm_call.insert()

    return response.choices
