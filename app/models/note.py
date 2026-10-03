"""Notes: knowledge not tied to any one record, tool or reference - terms,
tips, advice, notes in general.

What a note OWNS - resources, topic links - cascades with it. What it NAMES -
its category - is SET NULL when the option goes, because a category is
optional and a note is worth keeping without one.
"""

from sqlalchemy import CheckConstraint, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.constants import Visibility
from app.database import Base
from app.models.base import TimestampMixin, in_clause
from app.models.system_option import SystemOption


class Note(Base, TimestampMixin):
    """One name, required and not unique: two notes may share one. Not the
    three name slots the other named rows carry - see decisions.md, "A note
    has one name"."""

    __tablename__ = "note"

    id: Mapped[int] = mapped_column(primary_key=True)
    # Trimmed by the schema; the check holds it for a row written any other way.
    name: Mapped[str] = mapped_column(String, nullable=False)
    # Must be a `note_category` option; a FK cannot see the category, so the
    # service checks it.
    category_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("system_option.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    body: Mapped[str | None] = mapped_column(Text, nullable=True)
    remark: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Reserved; nothing reads it yet. See `Visibility`.
    visibility: Mapped[str] = mapped_column(
        String,
        nullable=False,
        default=Visibility.PRIVATE.value,
        server_default=Visibility.PRIVATE.value,
    )

    category = relationship(SystemOption, foreign_keys=[category_id])
    resources = relationship(
        "NoteResource",
        back_populates="note",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="NoteResource.position",
    )
    topics = relationship(
        SystemOption,
        secondary="note_topic",
        order_by=(SystemOption.sort_order, SystemOption.id),
        passive_deletes=True,
    )

    __table_args__ = (
        CheckConstraint("btrim(name) <> ''", name="ck_note_name_not_blank"),
        CheckConstraint(in_clause("visibility", Visibility), name="ck_note_visibility"),
    )


class NoteResource(Base):
    """A link worth keeping beside the note. Replaced whole on a save, so
    `position` is the order sent and carries no unique constraint - one would
    collide with the rows being replaced inside the same flush (`food`'s
    `tbd_link`, with `label` renamed `name`: "label" is a tag word here)."""

    __tablename__ = "note_resource"

    id: Mapped[int] = mapped_column(primary_key=True)
    note_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("note.id", ondelete="CASCADE"), nullable=False, index=True
    )
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    name: Mapped[str | None] = mapped_column(String, nullable=True)
    # http or https only, normalised in the schema layer.
    url: Mapped[str] = mapped_column(String, nullable=False)

    note = relationship("Note", back_populates="resources")

    __table_args__ = (
        CheckConstraint("btrim(url) <> ''", name="ck_note_resource_has_a_url"),
    )


class NoteTopic(Base):
    """A note's topic tags. Both sides CASCADE - a link has no life of its own.
    Options of category `topic` only, checked by the service."""

    __tablename__ = "note_topic"

    note_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("note.id", ondelete="CASCADE"), primary_key=True
    )
    option_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("system_option.id", ondelete="CASCADE"), primary_key=True
    )

    __table_args__ = (
        # The composite key leads with note_id, so it cannot serve "which
        # notes carry this topic" - nor the cascade from the option.
        Index("ix_note_topic_option", "option_id"),
    )
