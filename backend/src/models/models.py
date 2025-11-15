from typing import Any, Dict, List, Optional

from beanie import Document


class Project(Document):
    project_id: str
    created_at: str
    created_by: str
    system_message: str
    loading_message: Optional[str] = None
    active: bool
    openai_backend: Optional[str] = "azure"


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
