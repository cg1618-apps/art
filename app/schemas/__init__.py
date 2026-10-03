"""Every schema, re-exported so call sites write `schemas.NoteResponse`."""

from app.schemas.exercise import (
    DrillCreate,
    DrillRef,
    DrillResponse,
    DrillUpdate,
    ExerciseCreate,
    ExerciseRef,
    ExerciseResponse,
    ExerciseSummary,
    ExerciseUpdate,
)
from app.schemas.goal import (
    GoalCreate,
    GoalRef,
    GoalResponse,
    GoalUpdate,
    StageCreate,
    StageRef,
    StageResponse,
    StageSummary,
    StageUpdate,
)
from app.schemas.note import (
    NoteCreate,
    NoteResponse,
    NoteSummary,
    NoteUpdate,
)
from app.schemas.option import (
    OptionCategoryResponse,
    OptionCreate,
    OptionRef,
    OptionResponse,
    OptionUpdate,
)
from app.schemas.record import (
    Activity,
    DaySummary,
    RecordCreate,
    RecordResponse,
    RecordUpdate,
)
from app.schemas.resource import ResourceIn, ResourceResponse

__all__ = [
    "Activity",
    "DaySummary",
    "DrillCreate",
    "DrillRef",
    "DrillResponse",
    "DrillUpdate",
    "ExerciseCreate",
    "ExerciseRef",
    "ExerciseResponse",
    "ExerciseSummary",
    "ExerciseUpdate",
    "GoalCreate",
    "GoalRef",
    "GoalResponse",
    "GoalUpdate",
    "NoteCreate",
    "NoteResponse",
    "NoteSummary",
    "NoteUpdate",
    "OptionCategoryResponse",
    "OptionCreate",
    "OptionRef",
    "OptionResponse",
    "OptionUpdate",
    "RecordCreate",
    "RecordResponse",
    "RecordUpdate",
    "ResourceIn",
    "ResourceResponse",
    "StageCreate",
    "StageRef",
    "StageResponse",
    "StageSummary",
    "StageUpdate",
]
