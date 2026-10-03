"""The open vocabularies the owner edits on the Options page.

Tier 2: a list lives here when no code branches on its exact value. Entities
link to an option by id, never by copying its text, so a rename is one row and
shows everywhere at once.

What names an option - `note.category_id`, `note_topic.option_id` - gives way
when it is deleted: single-valued references are set NULL, tag links cascade.
The API states how many before it deletes (`DELETE ...?in_use=n`).
"""

from sqlalchemy import CheckConstraint, Index, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.constants import OPTION_CATEGORIES
from app.database import Base
from app.models.base import TimestampMixin, in_clause


class SystemOption(Base, TimestampMixin):
    """One value in one registered category.

    `description` is what the value means, written for the moment it is
    picked - the Options page and the picker's tooltip show it. `remark` is a
    note to yourself, shown on the Options page only.
    """

    __tablename__ = "system_option"

    id: Mapped[int] = mapped_column(primary_key=True)
    category: Mapped[str] = mapped_column(String, nullable=False)
    value: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    remark: Mapped[str | None] = mapped_column(Text, nullable=True)
    sort_order: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )

    __table_args__ = (
        CheckConstraint(in_clause("category", OPTION_CATEGORIES), name="ck_system_option_category"),
        # `速寫` and ` 速寫 ` are one value, and so are `Hand` and `hand`. The
        # schema trims on the way in; btrim here holds the rule for a row
        # written any other way. Leads with category, so it also serves the
        # list's `?category=` filter.
        Index(
            "uq_system_option_value",
            "category",
            func.lower(func.btrim(value)),
            unique=True,
        ),
    )
