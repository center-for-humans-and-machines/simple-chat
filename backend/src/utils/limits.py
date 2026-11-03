from datetime import datetime, timedelta
from typing import List, Optional

from src.models.message import Conversations
from src.models.models import Project, RateLimitEvent, TokenUsage

# Messages shown to participants. They deliberately do not say which limit was hit.
NOT_ALLOWED_MESSAGE = "You are not registered for this study, so the chat is not available."
LIMIT_REACHED_MESSAGE = "This conversation has reached its limit and has ended. Thank you for participating."
EMBED_NOT_ALLOWED_MESSAGE = "This chat cannot be used on this website."
RATE_LIMITED_MESSAGE = "You are sending messages too quickly. Please wait a moment and try again."


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


def origin_allowed(origin: str, allowed_origins: List[str]) -> bool:
    """Match an origin against entries like https://example.com or https://*.example.com."""
    origin = origin.lower().rstrip("/")
    for allowed in allowed_origins:
        if origin == allowed:
            return True
        scheme, wildcard, domain = allowed.partition("://*.")
        if wildcard and origin.startswith(scheme + "://") and origin.endswith("." + domain):
            return True
    return False


def frame_ancestors_policy(project: Project) -> Optional[str]:
    if not project.limits.allowed_embed_origins:
        return None
    return "frame-ancestors " + " ".join(project.limits.allowed_embed_origins)


async def check_start_limits(
    project: Project, participant_id, embed_origin: Optional[str] = None
) -> Optional[str]:
    """Return the reason a participant may not start a conversation, or None."""
    limits = project.limits

    # The browser enforces frame-ancestors where the frontend sends it; this
    # check covers other deployments and shows a message instead of a blank frame.
    # embed_origin is None when the chat is not in an iframe or the browser hides the parent.
    if (
        limits.allowed_embed_origins
        and embed_origin
        and not origin_allowed(embed_origin, limits.allowed_embed_origins)
    ):
        return "embed_origin_not_allowed"

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
    if reason == "not_allowed":
        return NOT_ALLOWED_MESSAGE
    if reason == "embed_origin_not_allowed":
        return EMBED_NOT_ALLOWED_MESSAGE
    return LIMIT_REACHED_MESSAGE


def rate_limit_key(project: Project, participant_id, ip: Optional[str]) -> Optional[str]:
    # without a participant_id the IP address is the only thing to count by
    if project.limits.rate_limit_key == "participant" and participant_id not in (None, -1, "-1"):
        return f"participant:{participant_id}"
    if ip:
        return f"ip:{ip}"
    return None


async def check_rate_limit(project: Project, participant_id, ip: Optional[str]) -> Optional[int]:
    """Record one conversation start or message.

    Return the seconds to wait when the rate limit is exceeded, or None.
    """
    limits = project.limits
    if limits.rate_limit_messages is None:
        return None

    key = rate_limit_key(project, participant_id, ip)
    if key is None:
        return None

    now = datetime.utcnow()
    window_start = now - timedelta(seconds=limits.rate_limit_window_seconds)
    events = (
        await RateLimitEvent.find(
            {"project_id": project.project_id, "key": key, "created_at": {"$gt": window_start}}
        )
        .sort("created_at")
        .to_list()
    )

    if len(events) >= limits.rate_limit_messages:
        # the oldest counted event leaving the window frees the next slot
        oldest = events[len(events) - limits.rate_limit_messages]
        wait = oldest.created_at - window_start
        return max(1, int(wait.total_seconds()) + 1)

    await RateLimitEvent(project_id=project.project_id, key=key, created_at=now).insert()
    return None
