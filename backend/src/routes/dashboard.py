# routes.py
import os
import re
from datetime import datetime

from fastapi import APIRouter, Body, Depends, HTTPException
from pydantic import BaseModel
from src.models.message import Conversations
from src.models.models import Project, ProjectLimits, Researcher, TokenUsage
from src.utils.auth import (PASSWORD_MIN_LENGTH, admin_user, authenticate,
                            create_token, current_user, hash_password,
                            project_for_user)
from src.utils.configs import model_prices
from src.utils.logging import setup_logger
from src.utils.usage import summarize_usage

logger = setup_logger(__name__)

# scheme, host (optionally starting with *.) and port, as allowed in frame-ancestors
EMBED_ORIGIN_PATTERN = re.compile(r"^https?://(\*\.)?[a-z0-9-]+(\.[a-z0-9-]+)*(:\d+)?$")

dashboard_router = APIRouter(prefix="/dashboard", tags=["dashboard"])


class LoginInput(BaseModel):
    email: str
    password: str


@dashboard_router.post("/login")
async def login(data: LoginInput):
    user = await authenticate(data.email.strip(), data.password)
    if user is None:
        raise HTTPException(status_code=401, detail="email or password is wrong.")

    return {
        "status": True,
        "admin": user["admin"],
        "token": create_token(user["email"], user["admin"]),
    }


class PasswordInput(BaseModel):
    password: str


@dashboard_router.get("/researchers")
async def list_of_researchers(user: dict = Depends(admin_user)):
    """Researchers and their projects, including project owners without an account."""
    admin_email = os.environ["DASHBOARD_USERNAME_ADMIN"]
    researchers = {
        r.email: {"email": r.email, "has_account": True, "projects": []}
        for r in await Researcher.find_all().to_list()
    }
    for project in await Project.find_all().to_list():
        if project.created_by == admin_email:
            continue
        researcher = researchers.setdefault(
            project.created_by,
            {"email": project.created_by, "has_account": False, "projects": []},
        )
        researcher["projects"].append(
            {"project_id": project.project_id, "active": project.active}
        )
    return sorted(researchers.values(), key=lambda r: r["email"].lower())


@dashboard_router.put("/researchers/{email}/password")
async def set_researcher_password(
    email: str, data: PasswordInput, user: dict = Depends(admin_user)
):
    """Reset a researcher's password, or create the account for a project owner without one."""
    email = email.strip()
    if email == os.environ["DASHBOARD_USERNAME_ADMIN"]:
        raise HTTPException(
            status_code=400, detail="the admin password is set with DASHBOARD_PASSWORD_ADMIN."
        )
    if len(data.password) < PASSWORD_MIN_LENGTH:
        raise HTTPException(
            status_code=400,
            detail=f"the password must have at least {PASSWORD_MIN_LENGTH} characters.",
        )

    researcher = await Researcher.find_one({"email": email})
    if researcher:
        researcher.password_hash = hash_password(data.password)
        await researcher.save()
    else:
        if not await Project.find_one({"created_by": email}):
            raise HTTPException(status_code=404, detail="researcher not found")
        await Researcher(
            email=email,
            password_hash=hash_password(data.password),
            created_at=str(datetime.now()),
        ).insert()

    return {"status": True, "email": email}


@dashboard_router.get("/researchers/{email}")
async def researcher_exists(email: str, user: dict = Depends(admin_user)):
    """Tell the create-project page whether it needs a password for this email."""
    email = email.strip()
    exists = email == os.environ["DASHBOARD_USERNAME_ADMIN"] or (
        await Researcher.find_one({"email": email}) is not None
    )
    return {"email": email, "exists": exists}


@dashboard_router.get("/projects/{email}")
async def list_of_projects(email: str, user: dict = Depends(current_user)):
    if not user.get("admin") and email != user.get("email"):
        raise HTTPException(status_code=403, detail="not allowed for this email")
    projects = await Project.find_many({"created_by": email}).to_list()
    return projects


@dashboard_router.get("/project/{project_id}")
async def get_project(project_id: str, user: dict = Depends(current_user)):
    return await project_for_user(project_id, user)


@dashboard_router.get("/conversations/{project_id}")
async def list_of_conversations(project_id: str, user: dict = Depends(current_user)):
    await project_for_user(project_id, user)
    conversations = await Conversations.find_many({"project_id": project_id}).to_list()
    return conversations


@dashboard_router.get("/conversation/{conversation_id}")
async def get_conversation(conversation_id: str, user: dict = Depends(current_user)):
    conversation = await Conversations.find_one({"conversation_id": conversation_id})
    if not conversation:
        raise HTTPException(status_code=404, detail="conversation not found")
    await project_for_user(conversation.project_id, user)
    return conversation


@dashboard_router.post("/update_system_message")
async def update_system_message(
    project_id: str = Body(...),
    message: str = Body(...),
    user: dict = Depends(current_user),
):
    project = await project_for_user(project_id, user)
    project.system_message = message
    await project.save()

    return {"status": True}


@dashboard_router.get("/toggle_status/{project_id}/{status}")
async def toggle_status(project_id: str, status: str, user: dict = Depends(current_user)):
    project = await project_for_user(project_id, user)

    if status == "true":
        project.active = True
    else:
        project.active = False

    await project.save()
    return {"status": True}


@dashboard_router.get("/toggle_openai_backend/{project_id}/{backend}")
async def toggle_openai_backend(
    project_id: str, backend: str, user: dict = Depends(current_user)
):
    project = await project_for_user(project_id, user)

    if backend not in ("azure", "openai"):
        raise HTTPException(status_code=501, detail="unvalid backend")

    project.openai_backend = backend

    await project.save()
    return {"status": True}


@dashboard_router.post("/update_loading_message")
async def update_loading_message(
    project_id: str = Body(...),
    loading_message: str = Body(...),
    user: dict = Depends(current_user),
):
    project = await project_for_user(project_id, user)

    project.loading_message = loading_message
    await project.save()

    return {"status": True, "updated_loading_message": project.loading_message}


@dashboard_router.get("/usage/{project_id}")
async def project_usage(project_id: str, user: dict = Depends(current_user)):
    await project_for_user(project_id, user)
    records = await TokenUsage.find_many({"project_id": project_id}).to_list()
    return {"project_id": project_id, "prices": model_prices, **summarize_usage(records)}


@dashboard_router.get("/usage/{project_id}/conversation/{conversation_id}")
async def conversation_usage(
    project_id: str, conversation_id: str, user: dict = Depends(current_user)
):
    await project_for_user(project_id, user)
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
async def get_limits(project_id: str, user: dict = Depends(current_user)):
    project = await project_for_user(project_id, user)
    return project.limits


@dashboard_router.put("/limits/{project_id}")
async def update_limits(
    project_id: str, limits: ProjectLimits, user: dict = Depends(current_user)
):
    project = await project_for_user(project_id, user)

    limits.participant_allowlist = sorted(
        {pid.strip() for pid in limits.participant_allowlist if pid.strip()}
    )
    limits.allowed_embed_origins = sorted(
        {
            origin.strip().lower().rstrip("/")
            for origin in limits.allowed_embed_origins
            if origin.strip()
        }
    )
    for origin in limits.allowed_embed_origins:
        if not EMBED_ORIGIN_PATTERN.match(origin):
            raise HTTPException(
                status_code=400,
                detail=f"invalid embedding origin: {origin} (expected e.g. https://example.com or https://*.example.com)",
            )
    project.limits = limits
    await project.save()

    return project.limits
