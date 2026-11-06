# routes.py
import re
from datetime import datetime
from typing import Optional
from urllib.parse import parse_qs, urlparse

from fastapi import APIRouter, Header, HTTPException, Response
from pydantic import BaseModel
from src.models import get_settings
from src.models.models import CustomSystemMessage, Project
from src.utils.configs import available_models
from src.utils.limits import frame_ancestors_policy
from src.utils.logging import setup_logger

logger = setup_logger(__name__)

settings = get_settings()

project_router = APIRouter(prefix="/project", tags=["project"])


class ProjectRegisterInput(BaseModel):
    project_id: str
    requested_by: str
    system_message: str
    model: Optional[str] = None


class CustomSystemMessageInput(BaseModel):
    system_message: str
    project_id: str
    requested_by: str
    assistant_first: bool
    first_message: str


@project_router.get("/models")
async def available_models():
    return {
        "models": available_models,
        "default": settings.openai_default_model,
    }


@project_router.get("/embed-policy")
async def embed_policy(
    response: Response,
    pid: Optional[str] = None,
    x_original_uri: Optional[str] = Header(default=None),
):
    """Set the chat page's Content-Security-Policy for a project.

    The frontend nginx calls this with auth_request and forwards the header;
    it passes the chat URL in X-Original-URI.
    """
    if pid is None and x_original_uri:
        pid = parse_qs(urlparse(x_original_uri).query).get("pid", [None])[0]

    project = await Project.find_one({"project_id": pid}) if pid else None
    policy = frame_ancestors_policy(project) if project else None
    if policy:
        response.headers["Content-Security-Policy"] = policy

    return {}


@project_router.post("/register")
async def send_message(data: ProjectRegisterInput):
    email_pattern = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")

    if not email_pattern.match(data.requested_by):
        raise HTTPException(
            status_code=400, detail="the value of requested_by is not valid."
        )

    project = await Project.find_many({"project_id": data.project_id}).to_list()

    if len(project) > 0:
        raise HTTPException(
            status_code=400, detail="there is already a project with this project_id"
        )

    if data.model and data.model not in available_models:
        raise HTTPException(status_code=400, detail=f"unknown model: {data.model}")

    new_project = Project(
        project_id=data.project_id,
        created_by=data.requested_by,
        system_message=data.system_message,
        created_at=str(datetime.now()),
        active=True,
        openai_backend=settings.openai_backend,
        model=data.model or None,
    )

    await new_project.insert()

    return {"status": True, "doc_id": new_project.id, "project": new_project}


@project_router.post("/custom_system_message")
async def custom_system_message(data: CustomSystemMessageInput):
    if not data.requested_by.endswith("@mpib-berlin.mpg.de"):
        raise HTTPException(
            status_code=400, detail="the value of requested_by is not valid."
        )

    project = await Project.find_many({"project_id": data.project_id}).to_list()
    if len(project) == 0:
        raise HTTPException(status_code=400, detail="project_id not found.")

    if len(data.system_message) < 10:
        raise HTTPException(status_code=401, detail="system_message is not valid")

    new_custom_system_message = CustomSystemMessage(
        project_id=data.project_id,
        created_by=data.requested_by,
        system_message=data.system_message,
        assistant_first=data.assistant_first,
        created_at=str(datetime.now()),
        first_message=data.first_message,
    )

    await new_custom_system_message.insert()

    return {"status": True, "system_message_id": new_custom_system_message.id}
