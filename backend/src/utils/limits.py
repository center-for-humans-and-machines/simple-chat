from typing import Optional

from src.models.message import Conversations
from src.models.models import Project, TokenUsage

# Messages shown to participants. They deliberately do not say which limit was hit.
NOT_ALLOWED_MESSAGE = "You are not registered for this study, so the chat is not available."
LIMIT_REACHED_MESSAGE = "This conversation has reached its limit and has ended. Thank you for participating."


async def used_tokens(query: dict) -> int:
    result = await TokenUsage.find(query).aggregate(
        [
            {
                "$group": {
                    "_id": None,
                    "tokens": {"$sum": {"$add": ["$prompt_tokens", "$completion_tokens"]}},
                }
            }
        ]
    ).to_list()
    return result[0]["tokens"] if result else 0


async def project_token_cap_reached(project: Project) -> bool:
    cap = project.limits.max_tokens_per_project
    return cap is not None and await used_tokens({"project_id": project.project_id}) >= cap


async def check_start_limits(project: Project, participant_id) -> Optional[str]:
    """Return the reason a participant may not start a conversation, or None."""
    limits = project.limits

    if limits.participant_allowlist and str(participant_id) not in limits.participant_allowlist:
        return "not_allowed"

    # Without a participant_id there is nobody to count conversations for;
    # use the allowlist to require an ID.
    if limits.max_conversations_per_participant is not None and participant_id != -1:
        count = await Conversations.find(
            {"project_id": project.project_id, "participant_id": participant_id}
        ).count()
        if count >= limits.max_conversations_per_participant:
            return "max_conversations_per_participant"

    if await project_token_cap_reached(project):
        return "max_tokens_per_project"

    return None


async def check_conversation_limits(project: Project, conversation: Conversations) -> Optional[str]:
    """Return the reason the participant may not send another message, or None."""
    limits = project.limits

    if limits.max_turns is not None:
        turns = sum(1 for message in conversation.messages if message["role"] == "user")
        if turns >= limits.max_turns:
            return "max_turns"

    if limits.max_tokens_per_conversation is not None:
        tokens = await used_tokens({"conversation_id": conversation.conversation_id})
        if tokens >= limits.max_tokens_per_conversation:
            return "max_tokens_per_conversation"

    if await project_token_cap_reached(project):
        return "max_tokens_per_project"

    return None


def limit_message(reason: str) -> str:
    return NOT_ALLOWED_MESSAGE if reason == "not_allowed" else LIMIT_REACHED_MESSAGE
