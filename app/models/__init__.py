"""Every model, re-exported so `from app import models` reaches all of them.

Alembic's autogenerate reads `Base.metadata`, which is only populated for
modules that have actually been imported - so a model missing from this file
is a table missing from the next migration, with nothing to say so.
"""

from app.models.exercise import (
    Drill,
    DrillResource,
    DrillSourceLink,
    Exercise,
    ExerciseAlias,
    ExerciseResource,
    ExerciseTopic,
)
from app.models.goal import Goal, Stage, StageResource
from app.models.note import Note, NoteAlias, NoteResource, NoteTopic
from app.models.record import Record, RecordReference
from app.models.system_option import SystemOption

__all__ = [
    "Drill",
    "DrillResource",
    "DrillSourceLink",
    "Exercise",
    "ExerciseAlias",
    "ExerciseResource",
    "ExerciseTopic",
    "Goal",
    "Note",
    "NoteAlias",
    "NoteResource",
    "NoteTopic",
    "Record",
    "RecordReference",
    "Stage",
    "StageResource",
    "SystemOption",
]
