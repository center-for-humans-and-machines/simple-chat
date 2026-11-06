from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

import pymongo
from beanie import Document
from pydantic import BaseModel, Field


class ProjectLimits(BaseModel):
    # None means "no limit"
    max_conversations_per_participant: Optional[int] = Field(default=None, ge=1)
    max_turns: Optional[int] = Field(default=None, ge=1)
    max_tokens_per_conversation: Optional[int] = Field(default=None, ge=1)
    max_tokens_per_project: Optional[int] = Field(default=None, ge=1)
    # empty list means every participant is allowed
    participant_allowlist: List[str] = Field(default_factory=list)
    # at most rate_limit_messages conversation starts and messages per
    # rate_limit_window_seconds, counted per participant_id or per IP address
    rate_limit_messages: Optional[int] = Field(default=None, ge=1)
    rate_limit_window_seconds: int = Field(default=60, ge=1, le=24 * 60 * 60)
    rate_limit_key: Literal["participant", "ip"] = "participant"
    # origins (e.g. https://*.qualtrics.com) allowed to embed the chat in an
    # iframe; empty list means any site may embed it
    allowed_embed_origins: List[str] = Field(default_factory=list)


class Project(Document):
    project_id: str
    created_at: str
    created_by: str
    system_message: str
    loading_message: Optional[str] = None
    active: bool
    openai_backend: Optional[str] = "azure"
    # used when the chat URL has no `model` query parameter
    model: Optional[str] = None
    limits: ProjectLimits = Field(default_factory=ProjectLimits)


class LlmCall(Document):
    project_id: str
    chat: List[Dict[str, Any]]
    response: Dict[str, Any]
    created_at: str


class CustomSystemMessage(Document):
    system_message: str
    first_message: str
    project_id: str
    created_by: str
    assistant_first: bool
    created_at: str


class TokenUsage(Document):
    project_id: str
    conversation_id: Optional[str] = None
    participant_id: Optional[str] = None
    model: str
    prompt_tokens: int
    completion_tokens: int
    # True when counted locally with tiktoken instead of reported by the provider
    estimated: bool = False
    source: str = "chat"  # "chat" (participant conversations) or "llm_api" (/llm/* routes)
    created_at: str


class TokenBudget(Document):
    # "project:<project_id>" or "conversation:<conversation_id>"
    key: str
    # recorded usage plus the tokens reserved by model calls still in flight;
    # only changed with atomic $inc so concurrent calls cannot pass the cap together
    tokens: int = 0

    class Settings:
        indexes = [pymongo.IndexModel([("key", pymongo.ASCENDING)], unique=True)]


class RateLimitEvent(Document):
    project_id: str
    key: str  # "participant:<id>" or "ip:<address>"
    created_at: datetime

    class Settings:
        indexes = [
            [("project_id", pymongo.ASCENDING), ("key", pymongo.ASCENDING), ("created_at", pymongo.ASCENDING)],
            # events are only needed for the length of a window
            pymongo.IndexModel([("created_at", pymongo.ASCENDING)], expireAfterSeconds=24 * 60 * 60),
        ]
