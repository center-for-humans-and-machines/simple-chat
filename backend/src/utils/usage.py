from datetime import datetime
from typing import Dict, List, Optional

from src.models.models import TokenUsage
from src.utils.configs import model_prices
from src.utils.logging import setup_logger

logger = setup_logger(__name__)


async def record_usage(
    project_id: str,
    model: str,
    prompt_tokens: int,
    completion_tokens: int,
    estimated: bool,
    source: str = "chat",
    conversation_id: Optional[str] = None,
    participant_id: Optional[str] = None,
):
    try:
        await TokenUsage(
            project_id=project_id,
            conversation_id=conversation_id,
            participant_id=str(participant_id) if participant_id is not None else None,
            model=model.replace("together_ai-", ""),
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            estimated=estimated,
            source=source,
            created_at=str(datetime.now()),
        ).insert()
    except Exception as e:
        # usage bookkeeping must never break a participant's conversation
        logger.error(f"Failed to record token usage: {e}")


async def record_response_usage(project_id: str, model: str, response, source: str):
    """Record usage of a non-streaming completion that reports `usage`."""
    usage = getattr(response, "usage", None)
    if usage is None:
        return
    await record_usage(
        project_id=project_id,
        model=model,
        prompt_tokens=usage.prompt_tokens,
        completion_tokens=usage.completion_tokens,
        estimated=False,
        source=source,
    )


def estimate_cost(model: str, prompt_tokens: int, completion_tokens: int) -> Optional[float]:
    price = model_prices.get(model)
    if price is None:
        return None
    return (
        prompt_tokens * price["prompt"] + completion_tokens * price["completion"]
    ) / 1_000_000


def _empty_bucket() -> Dict:
    return {
        "prompt_tokens": 0,
        "completion_tokens": 0,
        "total_tokens": 0,
        "estimated_cost_usd": 0.0,
        "calls": 0,
        "has_unpriced_model": False,
        "has_estimated_tokens": False,
    }


def _add(bucket: Dict, record: TokenUsage):
    bucket["prompt_tokens"] += record.prompt_tokens
    bucket["completion_tokens"] += record.completion_tokens
    bucket["total_tokens"] += record.prompt_tokens + record.completion_tokens
    bucket["calls"] += 1
    cost = estimate_cost(record.model, record.prompt_tokens, record.completion_tokens)
    if cost is None:
        bucket["has_unpriced_model"] = True
    else:
        bucket["estimated_cost_usd"] += cost
    if record.estimated:
        bucket["has_estimated_tokens"] = True


def summarize_usage(records: List[TokenUsage]) -> Dict:
    total = _empty_bucket()
    by_model: Dict[str, Dict] = {}
    by_conversation: Dict[str, Dict] = {}

    for record in records:
        _add(total, record)
        _add(by_model.setdefault(record.model, _empty_bucket()), record)

        if record.conversation_id:
            bucket = by_conversation.setdefault(
                record.conversation_id,
                {
                    **_empty_bucket(),
                    "participant_id": record.participant_id,
                    "models": [],
                },
            )
            _add(bucket, record)
            if record.model not in bucket["models"]:
                bucket["models"].append(record.model)

    return {
        "total": total,
        "by_model": [{"model": model, **bucket} for model, bucket in by_model.items()],
        "by_conversation": sorted(
            (
                {"conversation_id": conversation_id, **bucket}
                for conversation_id, bucket in by_conversation.items()
            ),
            key=lambda item: item["total_tokens"],
            reverse=True,
        ),
    }
