"""References: the library, one reference, and its writes."""

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session

from app import schemas
from app.database import get_db
from app.models import Reference
from app.routers.common import option_ref
from app.services import references

router = APIRouter(prefix="/api/references", tags=["References"])


def _summary(row: Reference) -> schemas.ReferenceSummary:
    return schemas.ReferenceSummary(
        id=row.id,
        name=row.name,
        url=row.url,
        groups=[option_ref(g) for g in row.groups],
        notes_excerpt=references.excerpt(row.notes),
        updated_at=row.updated_at,
    )


def _response(row: Reference) -> schemas.ReferenceResponse:
    return schemas.ReferenceResponse(
        id=row.id,
        name=row.name,
        url=row.url,
        groups=[option_ref(g) for g in row.groups],
        notes=row.notes,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


@router.get("", response_model=list[schemas.ReferenceSummary])
def list_references(
    q: str | None = Query(default=None, description="Matches the name, the link or the notes"),
    group_id: list[int] | None = Query(None),
    no_group: bool = Query(False, description="Only the references in no group"),
    db: Session = Depends(get_db),
):
    """The library: a bare array sorted by name. A repeated `group_id` means
    "any of" its values."""
    return [_summary(row) for row in references.search(db, q, group_id, no_group)]


@router.get("/{reference_id}", response_model=schemas.ReferenceResponse)
def get_reference(reference_id: int, db: Session = Depends(get_db)):
    return _response(references.get(db, reference_id))


@router.post("", response_model=schemas.ReferenceResponse, status_code=201)
def create_reference(payload: schemas.ReferenceCreate, db: Session = Depends(get_db)):
    return _response(references.create(db, payload))


@router.patch("/{reference_id}", response_model=schemas.ReferenceResponse)
def update_reference(
    reference_id: int, payload: schemas.ReferenceUpdate, db: Session = Depends(get_db)
):
    return _response(references.update(db, reference_id, payload))


@router.delete("/{reference_id}", status_code=204)
def delete_reference(reference_id: int, db: Session = Depends(get_db)):
    references.delete(db, reference_id)
    return Response(status_code=204)
