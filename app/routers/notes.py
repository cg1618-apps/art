"""Notes: the library, one note, and its writes."""

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session

from app import schemas
from app.database import get_db
from app.models import Note
from app.routers.common import option_ref, resource_list
from app.services import notes

router = APIRouter(prefix="/api/notes", tags=["Notes"])


def _summary_fields(row: Note) -> dict:
    return {
        "id": row.id,
        "display_name": row.display_name,
        "name_cn": row.name_cn,
        "name_en": row.name_en,
        "name_alt": row.name_alt,
        "category": option_ref(row.category),
        "topics": [option_ref(t) for t in row.topics],
        "summary": row.summary,
        "visibility": row.visibility,
        "updated_at": row.updated_at,
    }


def _summary(row: Note) -> schemas.NoteSummary:
    return schemas.NoteSummary(**_summary_fields(row))


def _response(row: Note) -> schemas.NoteResponse:
    return schemas.NoteResponse(
        **_summary_fields(row),
        aliases=sorted(alias.value for alias in row.aliases),
        body=row.body,
        remark=row.remark,
        resources=resource_list(row.resources),
        created_at=row.created_at,
    )


@router.get("", response_model=list[schemas.NoteSummary])
def list_notes(
    q: str | None = Query(default=None, description="Matches a name, an alias or the summary"),
    category_id: list[int] | None = Query(None),
    topic_id: list[int] | None = Query(None),
    db: Session = Depends(get_db),
):
    """The library: a bare array sorted by display name. A repeated parameter
    means "any of" its values."""
    return [_summary(row) for row in notes.search(db, q, category_id, topic_id)]


@router.get("/{note_id}", response_model=schemas.NoteResponse)
def get_note(note_id: int, db: Session = Depends(get_db)):
    return _response(notes.get(db, note_id))


@router.post("", response_model=schemas.NoteResponse, status_code=201)
def create_note(payload: schemas.NoteCreate, db: Session = Depends(get_db)):
    return _response(notes.create(db, payload))


@router.patch("/{note_id}", response_model=schemas.NoteResponse)
def update_note(note_id: int, payload: schemas.NoteUpdate, db: Session = Depends(get_db)):
    return _response(notes.update(db, note_id, payload))


@router.delete("/{note_id}", status_code=204)
def delete_note(note_id: int, db: Session = Depends(get_db)):
    notes.delete(db, note_id)
    return Response(status_code=204)
