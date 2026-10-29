# routes.py
import os

from fastapi import APIRouter, Body, HTTPException
from src.models.message import Conversations
from src.models.models import Project, ProjectLimits, TokenUsage
from src.utils.configs import model_prices
from src.utils.logging import setup_logger
from src.utils.usage import summarize_usage

logger = setup_logger(__name__)

dashboard_router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@dashboard_router.get("/login/{email}/{project_id}")
async def login(email: str, project_id: str):
    if (
        project_id == os.environ["DASHBOARD_PASSWORD_ADMIN"]
        and email == os.environ["DASHBOARD_USERNAME_ADMIN"]
    ):
        return {"status": True, "admin": True}

    project = await Project.find_many(
        {"project_id": project_id, "created_by": email}
    ).to_list()
    if len(project) == 0:
        raise HTTPException(
            status_code=404, detail="project not found or email is wrong."
        )

    return {"status": True, "admin": False}


@dashboard_router.get("/projects/{email}")
async def list_of_projects(email: str):
    projects = await Project.find_many({"created_by": email}).to_list()
    return projects


@dashboard_router.get("/project/{project_id}")
async def list_of_projects(project_id: str):
    projects = await Project.find_many({"project_id": project_id}).to_list()
    return projects[0]


@dashboard_router.get("/conversations/{project_id}")
async def list_of_conversations(project_id: str):
    conversations = await Conversations.find_many({"project_id": project_id}).to_list()
    return conversations


@dashboard_router.get("/conversation/{conversation_id}")
async def list_of_conversations(conversation_id: str):
    conversations = await Conversations.find_many(
        {"conversation_id": conversation_id}
    ).to_list()
    return conversations[0]


@dashboard_router.post("/update_system_message")
async def list_of_conversations(project_id: str = Body(...), message: str = Body(...)):
    project = await Project.find_one({"project_id": project_id})

    if not project:
        raise HTTPException(status_code=404, detail="project not found")

    project.system_message = message
    await project.save()

    return {"status": True}


@dashboard_router.get("/toggle_status/{project_id}/{status}")
async def list_of_conversations(project_id: str, status: str):
    project = await Project.find_one({"project_id": project_id})

    if not project:
        raise HTTPException(status_code=404, detail="project not found")

    if status == "true":
        project.active = True
    else:
        project.active = False

    await project.save()
    return {"status": True}


@dashboard_router.get("/toggle_openai_backend/{project_id}/{backend}")
async def list_of_conversations(project_id: str, backend: str):
    project = await Project.find_one({"project_id": project_id})

    if not project:
        raise HTTPException(status_code=404, detail="project not found")

    if backend not in ("azure", "openai"):
        raise HTTPException(status_code=501, detail="unvalid backend")

    project.openai_backend = backend

    await project.save()
    return {"status": True}


@dashboard_router.post("/update_loading_message")
async def update_loading_message(
    project_id: str = Body(...), loading_message: str = Body(...)
):
    project = await Project.find_one({"project_id": project_id})

    # logger.info(f"Found project: {project}")

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    project.loading_message = loading_message
    await project.save()

    return {"status": True, "updated_loading_message": project.loading_message}


@dashboard_router.get("/usage/{project_id}")
async def project_usage(project_id: str):
    records = await TokenUsage.find_many({"project_id": project_id}).to_list()
    return {"project_id": project_id, "prices": model_prices, **summarize_usage(records)}


@dashboard_router.get("/usage/{project_id}/conversation/{conversation_id}")
async def conversation_usage(project_id: str, conversation_id: str):
    records = await TokenUsage.find_many(
        {"project_id": project_id, "conversation_id": conversation_id}
    ).to_list()
    summary = summarize_usage(records)
    return {
        "conversation_id": conversation_id,
        "total": summary["total"],
        "by_model": summary["by_model"],
    }


@dashboard_router.get("/limits/{project_id}")
async def get_limits(project_id: str):
    project = await Project.find_one({"project_id": project_id})

    if not project:
        raise HTTPException(status_code=404, detail="project not found")

    return project.limits


@dashboard_router.put("/limits/{project_id}")
async def update_limits(project_id: str, limits: ProjectLimits):
    project = await Project.find_one({"project_id": project_id})

    if not project:
        raise HTTPException(status_code=404, detail="project not found")

    limits.participant_allowlist = sorted(
        {pid.strip() for pid in limits.participant_allowlist if pid.strip()}
    )
    project.limits = limits
    await project.save()

    return project.limits
