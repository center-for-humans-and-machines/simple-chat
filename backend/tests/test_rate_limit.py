import asyncio
from datetime import datetime, timedelta

from src.models.models import RateLimitWindow
from src.utils.limits import check_rate_limit


async def test_no_rate_limit_admits_everything(make_project):
    project = await make_project()
    assert await check_rate_limit(project, "p1", "1.2.3.4") is None


async def test_requests_past_the_limit_wait_for_the_window(make_project):
    project = await make_project(rate_limit_messages=2, rate_limit_window_seconds=60)

    assert await check_rate_limit(project, "p1", None) is None
    assert await check_rate_limit(project, "p1", None) is None
    wait = await check_rate_limit(project, "p1", None)

    assert wait is not None and 1 <= wait <= 61
    # other participants have their own window
    assert await check_rate_limit(project, "p2", None) is None


async def test_events_that_left_the_window_free_their_slot(make_project):
    project = await make_project(rate_limit_messages=1, rate_limit_window_seconds=60)
    old = datetime.utcnow() - timedelta(seconds=61)
    await RateLimitWindow(
        project_id=project.project_id, key="participant:p1", events=[old]
    ).insert()

    assert await check_rate_limit(project, "p1", None) is None
    window = await RateLimitWindow.find_one({"key": "participant:p1"})
    assert len(window.events) == 1 and window.events[0] > old


async def test_concurrent_requests_admit_exactly_the_limit(make_project):
    limit = 5
    project = await make_project(rate_limit_messages=limit, rate_limit_window_seconds=60)

    # the window does not exist yet, so the requests also race to create it
    results = await asyncio.gather(*(check_rate_limit(project, "p1", None) for _ in range(40)))

    assert sum(result is None for result in results) == limit
    windows = await RateLimitWindow.find({"key": "participant:p1"}).to_list()
    assert len(windows) == 1 and len(windows[0].events) == limit
