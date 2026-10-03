"""References: links worth keeping, with notes, filed into groups.

Only links today. Other kinds of reference - an uploaded image above all -
will be designed when they are built; nothing here anticipates them (see
decisions.md, "References are links, filed by groups").

No `visibility`: a reference is someone else's page, never published from
here.
"""

from sqlalchemy import CheckConstraint, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import TimestampMixin
from app.models.system_option import SystemOption


class Reference(Base, TimestampMixin):
    """One link. The name is required and not unique, as a note's."""

    __tablename__ = "reference"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    # http or https only, normalised in the schema layer, as a resource's.
    url: Mapped[str] = mapped_column(String, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    groups = relationship(
        SystemOption,
        secondary="reference_group",
        order_by=(SystemOption.sort_order, SystemOption.id),
        passive_deletes=True,
    )

    __table_args__ = (
        CheckConstraint("btrim(name) <> ''", name="ck_reference_name_not_blank"),
        CheckConstraint("btrim(url) <> ''", name="ck_reference_has_a_url"),
    )


class ReferenceGroup(Base):
    """A reference's group tags: `note_topic`'s shape, named `<owner>_<tag>`
    as it is. Both sides CASCADE. Options of category `reference_group`
    only, checked by the service."""

    __tablename__ = "reference_group"

    reference_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("reference.id", ondelete="CASCADE"), primary_key=True
    )
    option_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("system_option.id", ondelete="CASCADE"), primary_key=True
    )

    __table_args__ = (
        # The composite key leads with reference_id, so it cannot serve "which
        # references are in this group" - nor the cascade from the option.
        Index("ix_reference_group_option", "option_id"),
    )
