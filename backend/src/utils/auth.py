"""Signed tokens for the dashboard.

/dashboard/login returns a token that the dashboard sends back as
`Authorization: Bearer <token>`. The token is signed with
DASHBOARD_PASSWORD_ADMIN, so only the backend can issue one.
"""
import base64
import hashlib
import hmac
import json
import os
import time
from typing import Optional

from fastapi import Header, HTTPException
from src.models.models import Project

TOKEN_LIFETIME_SECONDS = 7 * 24 * 60 * 60


def _secret() -> bytes:
    return os.environ["DASHBOARD_PASSWORD_ADMIN"].encode()


def _sign(payload: bytes) -> str:
    return hmac.new(_secret(), payload, hashlib.sha256).hexdigest()


def create_token(email: str, admin: bool) -> str:
    payload = json.dumps(
        {"email": email, "admin": admin, "exp": int(time.time()) + TOKEN_LIFETIME_SECONDS}
    ).encode()
    return base64.urlsafe_b64encode(payload).decode() + "." + _sign(payload)


def read_token(token: str) -> Optional[dict]:
    try:
        encoded, signature = token.split(".", 1)
        payload = base64.urlsafe_b64decode(encoded.encode())
    except (ValueError, TypeError):
        return None
    if not hmac.compare_digest(_sign(payload), signature):
        return None
    data = json.loads(payload)
    if data.get("exp", 0) < time.time():
        return None
    return data


def current_user(authorization: Optional[str] = Header(default=None)) -> dict:
    scheme, _, token = (authorization or "").partition(" ")
    user = read_token(token) if scheme.lower() == "bearer" else None
    if user is None:
        raise HTTPException(status_code=401, detail="login required")
    return user


async def project_for_user(project_id: str, user: dict) -> Project:
    """Return the project if the user is the admin or created it."""
    project = await Project.find_one({"project_id": project_id})
    if not project:
        raise HTTPException(status_code=404, detail="project not found")
    if not user.get("admin") and project.created_by != user.get("email"):
        raise HTTPException(status_code=403, detail="not allowed for this project")
    return project
