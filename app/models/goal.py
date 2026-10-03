"""Goals and the roadmap: a goal is a level, named for what you can draw, and
its stages are the steps that get you there. Every level and every stage closes
with a test - a piece you redraw over time.

A stage's NUMBER is derived, never stored: every stage ordered by (goal
position, stage position, id), numbered from 0. Moving a stage renumbers
everything after it for free.

What a stage OWNS - its resources - cascades with it. A goal's stages do not:
`stage.goal_id` is RESTRICT, because a goal's stages are the roadmap and losing
them by deleting a level header would be the wrong surprise.
"""

from datetime import date

from sqlalchemy import CheckConstraint, Date, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.constants import GoalStatus, StageStatus
from app.database import Base
from app.models.base import NameFallbackMixin, TimestampMixin, in_clause


class Goal(Base, TimestampMixin, NameFallbackMixin):
    """A level: L0 ... L5. `code` is unique and trimmed; the names are not."""

    __tablename__ = "goal"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String, nullable=False)
    name_cn: Mapped[str | None] = mapped_column(String, nullable=True)
    name_en: Mapped[str | None] = mapped_column(String, nullable=True)
    name_alt: Mapped[str | None] = mapped_column(String, nullable=True)
    # Order on the roadmap. Not unique: ties fall back to id.
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    # "Done when you can ..."
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    # The test piece.
    test: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        String,
        nullable=False,
        default=GoalStatus.PLANNED.value,
        server_default=GoalStatus.PLANNED.value,
    )
    # Only when achieved; achieved may leave it NULL.
    achieved_on: Mapped[date | None] = mapped_column(Date, nullable=True)
    remark: Mapped[str | None] = mapped_column(Text, nullable=True)

    # passive_deletes="all": never NULL a stage's goal_id on a delete. The
    # service refuses a goal with stages first; the RESTRICT is the backstop.
    stages = relationship(
        "Stage",
        back_populates="goal",
        order_by="[Stage.position, Stage.id]",
        passive_deletes="all",
    )

    __table_args__ = (
        CheckConstraint("num_nonnulls(name_cn, name_en, name_alt) >= 1", name="ck_goal_has_a_name"),
        CheckConstraint(in_clause("status", GoalStatus), name="ck_goal_status"),
        CheckConstraint(
            f"achieved_on IS NULL OR status = '{GoalStatus.ACHIEVED}'",
            name="ck_goal_achieved_on_iff_achieved",
        ),
        UniqueConstraint("code", name="uq_goal_code"),
    )


class Stage(Base, TimestampMixin, NameFallbackMixin):
    """One step of a level: a focus (`description`) and a test."""

    __tablename__ = "stage"

    id: Mapped[int] = mapped_column(primary_key=True)
    goal_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("goal.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    # Order inside its goal. Not unique: ties fall back to id.
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    name_cn: Mapped[str | None] = mapped_column(String, nullable=True)
    name_en: Mapped[str | None] = mapped_column(String, nullable=True)
    name_alt: Mapped[str | None] = mapped_column(String, nullable=True)
    # The focus: what is practised.
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    test: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        String,
        nullable=False,
        default=StageStatus.NOT_STARTED.value,
        server_default=StageStatus.NOT_STARTED.value,
    )
    passed_on: Mapped[date | None] = mapped_column(Date, nullable=True)
    remark: Mapped[str | None] = mapped_column(Text, nullable=True)

    goal = relationship("Goal", back_populates="stages")
    resources = relationship(
        "StageResource",
        back_populates="stage",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="StageResource.position",
    )

    __table_args__ = (
        CheckConstraint(
            "num_nonnulls(name_cn, name_en, name_alt) >= 1", name="ck_stage_has_a_name"
        ),
        CheckConstraint(in_clause("status", StageStatus), name="ck_stage_status"),
        CheckConstraint(
            f"passed_on IS NULL OR status = '{StageStatus.PASSED}'",
            name="ck_stage_passed_on_iff_passed",
        ),
    )


class StageResource(Base):
    """A lecture to rewatch at the start of a stage. `note_resource`'s shape
    exactly: replaced whole on a save, so `position` is the order sent and
    carries no unique constraint."""

    __tablename__ = "stage_resource"

    id: Mapped[int] = mapped_column(primary_key=True)
    stage_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("stage.id", ondelete="CASCADE"), nullable=False, index=True
    )
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    name: Mapped[str | None] = mapped_column(String, nullable=True)
    # http or https only, normalised in the schema layer.
    url: Mapped[str] = mapped_column(String, nullable=False)

    stage = relationship("Stage", back_populates="resources")

    __table_args__ = (
        CheckConstraint("btrim(url) <> ''", name="ck_stage_resource_has_a_url"),
    )
