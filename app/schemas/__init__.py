"""Every schema, re-exported so call sites write `schemas.NoteResponse`."""

from app.schemas.note import (
    NoteCreate,
    NoteResponse,
    NoteSummary,
    NoteUpdate,
    ResourceIn,
    ResourceResponse,
)
from app.schemas.option import (
    OptionCategoryResponse,
    OptionCreate,
    OptionRef,
    OptionResponse,
    OptionUpdate,
)

__all__ = [
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
]
