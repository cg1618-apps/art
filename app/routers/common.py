"""How every router shows the rows another row names: an option, a list of
links, a stage, an activity. One copy, so a field added to a ref is added
everywhere."""

from app import schemas


def option_ref(option) -> schemas.OptionRef | None:
    if option is None:
        return None
    return schemas.OptionRef(id=option.id, value=option.value, description=option.description)


def resource_list(rows) -> list[schemas.ResourceResponse]:
    """Any `<table>_resource`-shaped rows, in their stored order."""
    return [schemas.ResourceResponse(id=r.id, name=r.name, url=r.url) for r in rows]


def stage_ref(stage, numbers: dict[int, int]) -> schemas.StageRef | None:
    """`numbers` is `stages.numbers`."""
    if stage is None:
        return None
    return schemas.StageRef(id=stage.id, number=numbers[stage.id], display_name=stage.display_name)


def goal_ref(goal) -> schemas.GoalRef | None:
    if goal is None:
        return None
    return schemas.GoalRef(id=goal.id, code=goal.code, display_name=goal.display_name)


def activity(row) -> schemas.Activity | None:
    """What a record or the timer names, through its `activity_exercise` and
    `drill`. Null when it names neither."""
    exercise = row.activity_exercise
    if exercise is None:
        return None
    drill = row.drill
    return schemas.Activity(
        exercise=schemas.ExerciseRef(id=exercise.id, display_name=exercise.display_name),
        drill=None if drill is None else schemas.DrillRef(id=drill.id, display_name=drill.display_name),
    )
