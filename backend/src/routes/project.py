# routes.py
import re
from datetime import datetime

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from src.models.models import CustomSystemMessage, Project
from src.utils.logging import setup_logger

logger = setup_logger(__name__)

project_router = APIRouter(prefix="/project", tags=["project"])


class ProjectRegisterInput(BaseModel):
    project_id: str
    requested_by: str
    system_message: str


class CustomSystemMessageInput(BaseModel):
    system_message: str
    project_id: str
    requested_by: str
    assistant_first: bool
    first_message: str


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

    new_project = Project(
        project_id=data.project_id,
        created_by=data.requested_by,
        system_message=data.system_message,
        created_at=str(datetime.now()),
        active=True,
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
