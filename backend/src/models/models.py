from typing import Any, Dict, List, Optional

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


class Project(Document):
    project_id: str
    created_at: str
    created_by: str
    system_message: str
    loading_message: Optional[str] = None
    active: bool
    openai_backend: Optional[str] = "azure"
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
