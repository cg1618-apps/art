"""Every schema, re-exported so call sites write `schemas.NoteResponse`."""

from app.schemas.goal import (
    GoalCreate,
    GoalRef,
    GoalResponse,
    GoalUpdate,
    StageCreate,
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
from app.schemas.resource import ResourceIn, ResourceResponse

__all__ = [
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
    "ResourceIn",
    "ResourceResponse",
    "StageCreate",
    "StageResponse",
    "StageSummary",
    "StageUpdate",
]
