"""Exercises and drills: `food`'s dish and recipe. An exercise is what is
practised; a drill is one prescribed way of doing it.

What an exercise OWNS - aliases, resources, topic links - cascades with it, as
a note's do. Its drills do not: `drill.exercise_id` is RESTRICT, and the
service refuses an exercise that still has drills. Its stage is SET NULL when
the stage goes: warm-ups and gesture have no stage anyway, so an exercise is
worth keeping without one.

A drill's source is SET NULL with its option; its links cascade with it.
Records RESTRICT both (see `app.models.record`).
"""

from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import NameFallbackMixin, TimestampMixin
from app.models.goal import Stage
from app.models.system_option import SystemOption


class Exercise(Base, TimestampMixin, NameFallbackMixin):
    """Names are not unique, as a note's are not."""

    __tablename__ = "exercise"

    id: Mapped[int] = mapped_column(primary_key=True)
    name_cn: Mapped[str | None] = mapped_column(String, nullable=True)
    name_en: Mapped[str | None] = mapped_column(String, nullable=True)
    name_alt: Mapped[str | None] = mapped_column(String, nullable=True)
    # None for what is practised at every level - warm-ups, gesture.
    stage_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("stage.id", ondelete="SET NULL"), nullable=True, index=True
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    remark: Mapped[str | None] = mapped_column(Text, nullable=True)

    stage = relationship(Stage)
    aliases = relationship(
        "ExerciseAlias",
        back_populates="exercise",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    resources = relationship(
        "ExerciseResource",
        back_populates="exercise",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="ExerciseResource.position",
    )
    topics = relationship(
        SystemOption,
        secondary="exercise_topic",
        order_by=(SystemOption.sort_order, SystemOption.id),
        passive_deletes=True,
    )
    # passive_deletes="all": never NULL a drill's exercise_id on a delete. The
    # service refuses an exercise with drills first; the RESTRICT is the
    # backstop.
    drills = relationship(
        "Drill",
        back_populates="exercise",
        order_by="[Drill.position, Drill.id]",
        passive_deletes="all",
    )

    __table_args__ = (
        CheckConstraint(
            "num_nonnulls(name_cn, name_en, name_alt) >= 1", name="ck_exercise_has_a_name"
        ),
    )


class ExerciseAlias(Base):
    """Anything you might type to find an exercise. Searched, never
    displayed; `food`'s alias table."""

    __tablename__ = "exercise_alias"

    id: Mapped[int] = mapped_column(primary_key=True)
    exercise_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("exercise.id", ondelete="CASCADE"), nullable=False, index=True
    )
    value: Mapped[str] = mapped_column(String, nullable=False)

    exercise = relationship("Exercise", back_populates="aliases")

    __table_args__ = (
        UniqueConstraint("exercise_id", "value", name="uq_exercise_alias"),
        Index("ix_exercise_alias_lookup", func.lower(value)),
    )


class ExerciseResource(Base):
    """A link kept beside the exercise. `note_resource`'s shape exactly."""

    __tablename__ = "exercise_resource"

    id: Mapped[int] = mapped_column(primary_key=True)
    exercise_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("exercise.id", ondelete="CASCADE"), nullable=False, index=True
    )
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    name: Mapped[str | None] = mapped_column(String, nullable=True)
    url: Mapped[str] = mapped_column(String, nullable=False)

    exercise = relationship("Exercise", back_populates="resources")

    __table_args__ = (
        CheckConstraint("btrim(url) <> ''", name="ck_exercise_resource_has_a_url"),
    )


class ExerciseTopic(Base):
    """An exercise's topic tags: `note_topic`'s shape, `topic` options only."""

    __tablename__ = "exercise_topic"

    exercise_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("exercise.id", ondelete="CASCADE"), primary_key=True
    )
    option_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("system_option.id", ondelete="CASCADE"), primary_key=True
    )

    __table_args__ = (Index("ix_exercise_topic_option", "option_id"),)


class Drill(Base, TimestampMixin):
    """One prescribed way of practising an exercise. Its name is optional and
    falls back to the exercise's."""

    __tablename__ = "drill"

    id: Mapped[int] = mapped_column(primary_key=True)
    exercise_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("exercise.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    name: Mapped[str | None] = mapped_column(String, nullable=True)
    # Must be a `source` option; a FK cannot see the category, so the service
    # checks it.
    source_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("system_option.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    instructions: Mapped[str | None] = mapped_column(Text, nullable=True)
    # 頁, 張, 組, 個 - free text.
    unit: Mapped[str | None] = mapped_column(String, nullable=True)
    # How many units make one round.
    target: Mapped[int | None] = mapped_column(Integer, nullable=True)
    suggested_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    # "daily for 3 weeks", 每天 - the sheet's own wording.
    frequency: Mapped[str | None] = mapped_column(String, nullable=True)
    remark: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Order inside its exercise. Not unique: ties fall back to id.
    position: Mapped[int] = mapped_column(Integer, nullable=False)

    exercise = relationship("Exercise", back_populates="drills")
    source = relationship(SystemOption, foreign_keys=[source_id])
    source_links = relationship(
        "DrillSourceLink",
        back_populates="drill",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="DrillSourceLink.position",
    )
    resources = relationship(
        "DrillResource",
        back_populates="drill",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="DrillResource.position",
    )

    @property
    def display_name(self) -> str:
        """Its own name, or its exercise's."""
        if self.name and self.name.strip():
            return self.name
        return self.exercise.display_name if self.exercise is not None else ""

    __table_args__ = (
        CheckConstraint("target IS NULL OR target >= 1", name="ck_drill_target_positive"),
        CheckConstraint(
            "suggested_minutes IS NULL OR suggested_minutes >= 1",
            name="ck_drill_suggested_minutes_positive",
        ),
    )


class DrillSourceLink(Base):
    """Where the drill comes from - the lecture, the assignment sheet.
    `note_resource`'s shape."""

    __tablename__ = "drill_source_link"

    id: Mapped[int] = mapped_column(primary_key=True)
    drill_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("drill.id", ondelete="CASCADE"), nullable=False, index=True
    )
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    name: Mapped[str | None] = mapped_column(String, nullable=True)
    url: Mapped[str] = mapped_column(String, nullable=False)

    drill = relationship("Drill", back_populates="source_links")

    __table_args__ = (
        CheckConstraint("btrim(url) <> ''", name="ck_drill_source_link_has_a_url"),
    )


class DrillResource(Base):
    """A link used while doing the drill. `note_resource`'s shape."""

    __tablename__ = "drill_resource"

    id: Mapped[int] = mapped_column(primary_key=True)
    drill_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("drill.id", ondelete="CASCADE"), nullable=False, index=True
    )
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    name: Mapped[str | None] = mapped_column(String, nullable=True)
    url: Mapped[str] = mapped_column(String, nullable=False)

    drill = relationship("Drill", back_populates="resources")

    __table_args__ = (
        CheckConstraint("btrim(url) <> ''", name="ck_drill_resource_has_a_url"),
    )
