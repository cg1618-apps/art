"""System options: the registry of categories, and the values in each.

No read/write split: art is behind Cloudflare Access whole, so there is no
`/api/edit` prefix as in `food`. Publishing will use `/s/...` for reads.
"""

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session

from app import schemas
from app.constants import OPTION_CATEGORIES
from app.database import get_db
from app.models import SystemOption
from app.services import options

router = APIRouter(prefix="/api/options", tags=["Options"])


def _response(row: SystemOption, in_use: int) -> schemas.OptionResponse:
    return schemas.OptionResponse(
        id=row.id,
        category=row.category,
        value=row.value,
        description=row.description,
        remark=row.remark,
        sort_order=row.sort_order,
        in_use=in_use,
    )


@router.get("/categories", response_model=list[schemas.OptionCategoryResponse])
def list_categories():
    """The registry, in the order the Options page shows it."""
    return [
        schemas.OptionCategoryResponse(key=c.key, label=c.label, description=c.description)
        for c in OPTION_CATEGORIES.values()
    ]


@router.get("", response_model=list[schemas.OptionResponse])
def list_options(
    category: str | None = Query(default=None, description="One registered category key"),
    db: Session = Depends(get_db),
):
    """Every option, each with `in_use`: a bare array in category order, then
    the owner's order inside each."""
    rows = options.listed(db, category)
    counts = options.in_use_counts(db, [row.id for row in rows])
    return [_response(row, counts.get(row.id, 0)) for row in rows]


@router.post("", response_model=schemas.OptionResponse, status_code=201)
def create_option(payload: schemas.OptionCreate, db: Session = Depends(get_db)):
    return _response(options.create(db, payload), 0)


@router.patch("/{option_id}", response_model=schemas.OptionResponse)
def update_option(option_id: int, payload: schemas.OptionUpdate, db: Session = Depends(get_db)):
    row = options.update(db, option_id, payload)
    return _response(row, options.in_use(db, row.id))


@router.delete("/{option_id}", status_code=204)
def delete_option(
    option_id: int,
    in_use: int = Query(..., description="The in-use count the page showed"),
    db: Session = Depends(get_db),
):
    """Delete, with the count the user was shown echoed back; 409 with
    `field`, `expected` and `actual` when it has moved."""
    options.delete(db, option_id, in_use)
    return Response(status_code=204)
