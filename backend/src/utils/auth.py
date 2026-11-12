"""Signed tokens for the dashboard.

/dashboard/login returns a token that the dashboard sends back as
`Authorization: Bearer <token>`. The token is signed with
DASHBOARD_TOKEN_SECRET, so only the backend can issue one. It is kept apart
from DASHBOARD_PASSWORD_ADMIN so that a researcher's token cannot be used to
guess the admin password offline.
"""
import asyncio
import base64
import hashlib
import hmac
import json
import os
import re
import secrets
import time
from typing import Optional

from fastapi import Depends, Header, HTTPException
from src.models.models import Project, Researcher

TOKEN_LIFETIME_SECONDS = 7 * 24 * 60 * 60
TOKEN_SECRET_MIN_LENGTH = 32
PASSWORD_MIN_LENGTH = 8  # also in dashboard/src/passwordRules.js
PASSWORD_ITERATIONS = 600_000
# checked for unknown emails, so they take as long as a wrong password; no password matches it
DUMMY_PASSWORD_HASH = f"pbkdf2_sha256${PASSWORD_ITERATIONS}${'0' * 32}${'0' * 64}"


# PBKDF2 takes about half a second, so the async wrappers below run it in a
# worker thread instead of blocking the event loop (and every live chat).
def _hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), PASSWORD_ITERATIONS)
    return f"pbkdf2_sha256${PASSWORD_ITERATIONS}${salt}${digest.hex()}"


def _verify_password(password: str, password_hash: str) -> bool:
    try:
        _, iterations, salt, expected = password_hash.split("$")
        digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), int(iterations))
    except ValueError:
        return False
    return hmac.compare_digest(digest.hex(), expected)


async def hash_password(password: str) -> str:
    return await asyncio.to_thread(_hash_password, password)


async def verify_password(password: str, password_hash: str) -> bool:
    return await asyncio.to_thread(_verify_password, password, password_hash)


def normalize_email(email: str) -> str:
    """Emails are stored and compared trimmed and in lowercase."""
    return email.strip().lower()


def same_email(a: str, b: str) -> bool:
    return normalize_email(a) == normalize_email(b)


def email_query(field: str, email: str) -> dict:
    """Match `field` to the email ignoring case, so records saved before
    emails were lowercased are still found."""
    return {field: {"$regex": f"^{re.escape(normalize_email(email))}$", "$options": "i"}}


def admin_email() -> str:
    return normalize_email(os.environ["DASHBOARD_USERNAME_ADMIN"])


def is_admin_login(email: str, password: str) -> bool:
    return hmac.compare_digest(
        normalize_email(email).encode(), admin_email().encode()
    ) and hmac.compare_digest(password.encode(), os.environ["DASHBOARD_PASSWORD_ADMIN"].encode())


async def authenticate(email: str, password: str) -> Optional[dict]:
    """Return the user for a dashboard login, or None."""
    email = normalize_email(email)
    if is_admin_login(email, password):
        return {"email": email, "admin": True}
    researcher = await Researcher.find_one(email_query("email", email))
    if researcher is None:
        await verify_password(password, DUMMY_PASSWORD_HASH)
        return None
    if await verify_password(password, researcher.password_hash):
        return {"email": email, "admin": False}
    return None


def _secret() -> bytes:
    secret = os.environ.get("DASHBOARD_TOKEN_SECRET", "")
    if len(secret) < TOKEN_SECRET_MIN_LENGTH:
        raise RuntimeError(
            f"DASHBOARD_TOKEN_SECRET must be set to a random value of at least "
            f"{TOKEN_SECRET_MIN_LENGTH} characters, e.g. `openssl rand -hex 32`."
        )
    return secret.encode()


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
    # compare bytes: compare_digest raises TypeError for str with non-ASCII characters
    if not hmac.compare_digest(
        _sign(payload).encode(), signature.encode("utf-8", "surrogateescape")
    ):
        return None
    try:
        data = json.loads(payload)
        expired = data.get("exp", 0) < time.time()
    except (ValueError, TypeError, AttributeError):
        return None
    if expired:
        return None
    return data


def current_user(authorization: Optional[str] = Header(default=None)) -> dict:
    scheme, _, token = (authorization or "").partition(" ")
    user = read_token(token) if scheme.lower() == "bearer" else None
    if user is None:
        raise HTTPException(status_code=401, detail="login required")
    return user


def admin_user(user: dict = Depends(current_user)) -> dict:
    if not user.get("admin"):
        raise HTTPException(status_code=403, detail="admin login required")
    return user


async def project_for_user(project_id: str, user: dict) -> Project:
    """Return the project if the user is the admin or created it."""
    project = await Project.find_one({"project_id": project_id})
    if not project:
        raise HTTPException(status_code=404, detail="project not found")
    if not user.get("admin") and not same_email(project.created_by, user.get("email", "")):
        raise HTTPException(status_code=403, detail="not allowed for this project")
    return project
