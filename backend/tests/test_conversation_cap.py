from src.models.message import Conversations
from src.utils.limits import check_start_limits

PARTICIPANT = "p1"
EXPERIMENT = "e1"


async def written(project, conversation_id, round_number, user_turns=1):
    await Conversations(
        conversation_id=conversation_id,
        project_id=project.project_id,
        participant_id=PARTICIPANT,
        experiment_id=EXPERIMENT,
        model="gpt-4o",
        created_at="now",
        multi_rounds=round_number,
        user_turns=user_turns,
    ).insert()


async def start(project, round_number):
    return await check_start_limits(
        project, PARTICIPANT, experiment_id=EXPERIMENT, current_round=round_number
    )


async def test_first_conversation_of_a_round_continues_round_one(make_project):
    project = await make_project(max_conversations_per_participant=1)
    await written(project, "r1", 1)

    assert await start(project, 2) is None


async def test_more_conversations_of_the_same_round_are_counted(make_project):
    project = await make_project(max_conversations_per_participant=2)
    await written(project, "r1", 1)
    await written(project, "r2-a", 2)

    # the second round-2 conversation is the participant's second conversation
    assert await start(project, 2) is None
    await written(project, "r2-b", 2)

    # a third would be one past the cap
    assert await start(project, 2) == "max_conversations_per_participant"
    assert await start(project, 3) is None  # round 3 still continues round 2


async def test_round_n_without_the_previous_round_is_counted(make_project):
    project = await make_project(max_conversations_per_participant=1)
    await written(project, "r1", 1)

    assert await start(project, 3) == "max_conversations_per_participant"


async def test_reloaded_round_conversations_without_messages_do_not_count(make_project):
    project = await make_project(max_conversations_per_participant=1)
    await written(project, "r1", 1)
    await written(project, "r2-reload", 2, user_turns=0)

    assert await start(project, 2) is None
