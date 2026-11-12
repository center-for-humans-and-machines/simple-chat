from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Optional, Tuple

from pymongo import ReturnDocument
from pymongo.errors import DuplicateKeyError
from src.models.message import Conversations
from src.models.models import Project, RateLimitWindow, TokenBudget, TokenUsage

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


# Longest reply a call may generate while a token cap is set. A call near the
# cap gets a shorter limit, so it cannot generate past the cap.
MAX_COMPLETION_TOKENS = 4096
# How often to retry a reservation that lost a race with a concurrent call.
RESERVE_ATTEMPTS = 3


@dataclass
class TokenReservation:
    # (budget key, reserved tokens) for every cap the call counts against
    holds: List[Tuple[str, int]] = field(default_factory=list)
    # passed to the provider as max_tokens; None when no token cap is set
    max_tokens: Optional[int] = None


def project_budget_key(project_id: str) -> str:
    return f"project:{project_id}"


def conversation_budget_key(conversation_id: str) -> str:
    return f"conversation:{conversation_id}"


async def add_recorded_usage(project_id: str, conversation_id: Optional[str], tokens: int):
    """Add newly recorded usage to the budgets of its project and conversation.

    Every existing budget is updated, whether or not its cap is set right now, so
    a cap set later starts from the real usage. A budget that does not exist yet
    is built from TokenUsage on first use and already includes this record.
    """
    keys = [project_budget_key(project_id)]
    if conversation_id is not None:
        keys.append(conversation_budget_key(conversation_id))
    await TokenBudget.get_motor_collection().update_many(
        {"key": {"$in": keys}}, {"$inc": {"tokens": tokens}}
    )


def _token_caps(project: Project, conversation_id: Optional[str]):
    """(budget key, cap, usage query, limit name) for every token cap that applies."""
    limits = project.limits
    caps = []
    if limits.max_tokens_per_project is not None:
        caps.append(
            (
                project_budget_key(project.project_id),
                limits.max_tokens_per_project,
                {"project_id": project.project_id},
                "max_tokens_per_project",
            )
        )
    if conversation_id is not None and limits.max_tokens_per_conversation is not None:
        caps.append(
            (
                conversation_budget_key(conversation_id),
                limits.max_tokens_per_conversation,
                {"conversation_id": conversation_id},
                "max_tokens_per_conversation",
            )
        )
    return caps


async def _budget_tokens(key: str, usage_query: dict) -> int:
    """Current tokens of a budget, creating it from the recorded usage on first use."""
    budget = await TokenBudget.find_one({"key": key})
    if budget is not None:
        return budget.tokens
    try:
        await TokenBudget(key=key, tokens=await used_tokens(usage_query)).insert()
    except DuplicateKeyError:
        pass  # created by a concurrent call
    return (await TokenBudget.find_one({"key": key})).tokens


async def _add_tokens(key: str, amount: int, cap: Optional[int] = None) -> bool:
    """Atomically add tokens to a budget; with a cap, only while the result stays within it."""
    query = {"key": key}
    if cap is not None:
        query["tokens"] = {"$lte": cap - amount}
    result = await TokenBudget.get_motor_collection().find_one_and_update(
        query, {"$inc": {"tokens": amount}}
    )
    return result is not None


async def reserve_tokens(
    project: Project, prompt_tokens: int, conversation_id: Optional[str] = None
) -> Tuple[Optional[TokenReservation], Optional[str]]:
    """Reserve the prompt and a bounded reply against the project and conversation token caps.

    Return the reservation, or the name of the cap that leaves no room for a reply.
    The caller passes reservation.max_tokens to the provider, records the usage of
    the call, and then calls release_tokens.
    """
    caps = _token_caps(project, conversation_id)
    if not caps:
        return TokenReservation(), None

    for _ in range(RESERVE_ATTEMPTS):
        max_tokens = MAX_COMPLETION_TOKENS
        for key, cap, usage_query, reason in caps:
            room = cap - await _budget_tokens(key, usage_query) - prompt_tokens
            if room < 1:
                return None, reason
            max_tokens = min(max_tokens, room)

        amount = prompt_tokens + max_tokens
        holds = []
        for key, cap, _, _ in caps:
            if not await _add_tokens(key, amount, cap):
                break
            holds.append((key, amount))
        else:
            return TokenReservation(holds=holds, max_tokens=max_tokens), None

        # a concurrent call took part of the room: undo and recompute
        for key, held in holds:
            await _add_tokens(key, -held)

    return None, caps[0][3]


async def release_tokens(reservation: Optional[TokenReservation]):
    """Give back the reserved tokens once the call's usage is recorded.

    record_usage adds the used tokens to the budgets, so the budget ends up at the
    recorded usage. Recording before releasing keeps the budget from dropping below it.
    """
    if reservation is None:
        return
    for key, held in reservation.holds:
        await _add_tokens(key, -held)


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


async def continues_previous_round(
    project: Project, participant_id, experiment_id, current_round: int
) -> bool:
    """True when this start is round 2, 3, ... of a conversation the participant
    already has, i.e. the previous round exists and the participant wrote in it."""
    if current_round <= 1:
        return False
    previous = await Conversations.find_one(
        {
            "project_id": project.project_id,
            # stored as strings; a missing ID arrives as the integer -1
            "participant_id": str(participant_id),
            "experiment_id": str(experiment_id),
            "multi_rounds": current_round - 1,
            "user_turns": {"$gt": 0},
        }
    )
    return previous is not None


async def check_start_limits(
    project: Project,
    participant_id,
    embed_origin: Optional[str] = None,
    experiment_id=None,
    current_round: int = 0,
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
    # A later round continues the conversation of round 1, which is already
    # counted. Requiring the previous round stops a made-up round number from
    # skipping the cap.
    if (
        limits.max_conversations_per_participant is not None
        and participant_id != -1
        and not await continues_previous_round(
            project, participant_id, experiment_id, current_round
        )
    ):
        count = await Conversations.find(
            {
                "project_id": project.project_id,
                "participant_id": participant_id,
                # page reloads open a new conversation; only count those the
                # participant wrote in
                "user_turns": {"$gt": 0},
                # rounds 2, 3, ... continue the conversation of round 1
                "multi_rounds": {"$not": {"$gt": 1}},
            }
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
        if conversation.user_turns >= limits.max_turns:
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
    # Mongo stores datetimes with millisecond precision
    now = now.replace(microsecond=now.microsecond // 1000 * 1000)
    window = timedelta(seconds=limits.rate_limit_window_seconds)
    window_start = now - window

    # One atomic update drops the events that left the window and appends this
    # one only while there is a free slot, so concurrent requests and replicas
    # cannot all take the same slot.
    update = [
        {
            "$set": {
                "events": {
                    "$filter": {
                        "input": {"$ifNull": ["$events", []]},
                        "cond": {"$gt": ["$$this", window_start]},
                    }
                }
            }
        },
        {"$set": {"admitted": {"$lt": [{"$size": "$events"}, limits.rate_limit_messages]}}},
        {
            "$set": {
                "events": {
                    "$cond": ["$admitted", {"$concatArrays": ["$events", [now]]}, "$events"]
                },
                "expires_at": {
                    "$cond": [
                        "$admitted",
                        now + window,
                        {"$ifNull": ["$expires_at", now + window]},
                    ]
                },
            }
        },
    ]
    query = {"project_id": project.project_id, "key": key}
    collection = RateLimitWindow.get_motor_collection()
    try:
        result = await collection.find_one_and_update(
            query, update, upsert=True, return_document=ReturnDocument.AFTER
        )
    except DuplicateKeyError:
        # a concurrent request created the window first; it exists now
        result = await collection.find_one_and_update(
            query, update, return_document=ReturnDocument.AFTER
        )

    if result["admitted"]:
        return None

    # the oldest counted event leaving the window frees the next slot
    events = sorted(result["events"])
    oldest = events[len(events) - limits.rate_limit_messages]
    wait = oldest - window_start
    return max(1, int(wait.total_seconds()) + 1)
