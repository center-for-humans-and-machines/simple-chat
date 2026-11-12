from src.models.message import Conversations
from src.models.models import TokenUsage
from src.utils import limits
from src.utils.limits import check_conversation_limits, project_token_cap_reached
from src.utils.usage import estimate_cost, record_usage, summarize_usage


async def test_summary_sums_usage_in_mongo(make_project):
    project = await make_project()
    pid = project.project_id
    await record_usage(pid, "gpt-4o", 100, 10, estimated=True, conversation_id="c1", participant_id="p1")
    await record_usage(pid, "gpt-4o", 200, 20, estimated=False, conversation_id="c1", participant_id="p1")
    await record_usage(pid, "gpt-4o-mini", 50, 5, estimated=False, conversation_id="c2", participant_id="p2")
    await record_usage(pid, "gpt-4o", 1, 1, estimated=False, source="llm_api")

    summary = await summarize_usage({"project_id": pid})

    total = summary["total"]
    assert (total["prompt_tokens"], total["completion_tokens"], total["calls"]) == (351, 36, 4)
    assert total["has_estimated_tokens"] is True
    expected_cost = estimate_cost("gpt-4o", 301, 31) + estimate_cost("gpt-4o-mini", 50, 5)
    assert abs(total["estimated_cost_usd"] - expected_cost) < 1e-12

    by_model = {m["model"]: m for m in summary["by_model"]}
    assert by_model["gpt-4o"]["calls"] == 3 and by_model["gpt-4o-mini"]["total_tokens"] == 55

    c1, c2 = summary["by_conversation"]
    assert (c1["conversation_id"], c1["participant_id"], c1["total_tokens"]) == ("c1", "p1", 330)
    assert c1["models"] == ["gpt-4o"] and c1["has_estimated_tokens"] is True
    assert (c2["conversation_id"], c2["models"], c2["has_estimated_tokens"]) == ("c2", ["gpt-4o-mini"], False)


async def test_limit_checks_read_the_budget_not_the_usage_records(make_project, monkeypatch):
    project = await make_project(max_tokens_per_project=1000, max_tokens_per_conversation=100)
    conversation = Conversations(
        conversation_id="c1", project_id=project.project_id, participant_id="p1",
        experiment_id="e1", model="gpt-4o", messages=[], created_at="now",
    )
    await record_usage(project.project_id, "gpt-4o", 60, 0, estimated=True, conversation_id="c1")
    assert await check_conversation_limits(project, conversation) is None  # builds the budgets

    aggregations = []
    real_used_tokens = limits.used_tokens

    async def counting_used_tokens(query):
        aggregations.append(query)
        return await real_used_tokens(query)

    monkeypatch.setattr(limits, "used_tokens", counting_used_tokens)
    await record_usage(project.project_id, "gpt-4o", 50, 0, estimated=True, conversation_id="c1")

    assert await check_conversation_limits(project, conversation) == "max_tokens_per_conversation"
    assert not await project_token_cap_reached(project)
    assert aggregations == []
    assert await TokenUsage.find_many({"project_id": project.project_id}).count() == 2
