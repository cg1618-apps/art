"""Records: one per exercise practised.

A record names a drill, an exercise, or neither - never both
(`ck_record_one_activity`); through a drill the exercise is derived. A `test`
record is the test of exactly one stage or one level, and only a test names
either (`ck_record_test_target`).

**Records RESTRICT what they name.** A record is history: deleting the drill,
exercise, stage or goal it names is refused with a count, never a silent loss.
The options it names - location, method, tool - are SET NULL with the option,
because each is optional and the record is worth keeping without it. Its
reference links cascade with it.
"""

import datetime

from sqlalchemy import CheckConstraint, Date, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.constants import RecordKind
from app.database import Base
from app.models.base import TimestampMixin, in_clause
from app.models.exercise import Drill, Exercise
from app.models.goal import Goal, Stage
from app.models.system_option import SystemOption


def _option_fk() -> ForeignKey:
    return ForeignKey("system_option.id", ondelete="SET NULL")


class Record(Base, TimestampMixin):
    __tablename__ = "record"

    id: Mapped[int] = mapped_column(primary_key=True)
    date: Mapped[datetime.date] = mapped_column(Date, nullable=False, index=True)
    # A `location` option; checked by the service.
    location_id: Mapped[int | None] = mapped_column(
        Integer, _option_fk(), nullable=True, index=True
    )
    duration_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    drill_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("drill.id", ondelete="RESTRICT"), nullable=True, index=True
    )
    exercise_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("exercise.id", ondelete="RESTRICT"), nullable=True, index=True
    )
    kind: Mapped[str] = mapped_column(
        String,
        nullable=False,
        default=RecordKind.PRACTICE.value,
        server_default=RecordKind.PRACTICE.value,
    )
    # The stage, or the level, whose test this is. Only when kind is test.
    stage_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("stage.id", ondelete="RESTRICT"), nullable=True, index=True
    )
    goal_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("goal.id", ondelete="RESTRICT"), nullable=True, index=True
    )
    # A `method` option; checked by the service.
    method_id: Mapped[int | None] = mapped_column(
        Integer, _option_fk(), nullable=True, index=True
    )
    # A `tool` option; checked by the service.
    tool_id: Mapped[int | None] = mapped_column(Integer, _option_fk(), nullable=True, index=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    drill = relationship(Drill)
    exercise = relationship(Exercise)
    stage = relationship(Stage)
    goal = relationship(Goal)
    location = relationship(SystemOption, foreign_keys=[location_id])
    method = relationship(SystemOption, foreign_keys=[method_id])
    tool = relationship(SystemOption, foreign_keys=[tool_id])
    references = relationship(
        "RecordReference",
        back_populates="record",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="RecordReference.position",
    )

    @property
    def activity_exercise(self) -> Exercise | None:
        """The exercise practised: named directly, or through the drill."""
        if self.drill is not None:
            return self.drill.exercise
        return self.exercise

    __table_args__ = (
        CheckConstraint(in_clause("kind", RecordKind), name="ck_record_kind"),
        CheckConstraint("num_nonnulls(drill_id, exercise_id) <= 1", name="ck_record_one_activity"),
        # Exactly one of the two on a test, neither otherwise. Written as an
        # equality on the count rather than `(kind = 'test') = (count = 1)`,
        # which would let a non-test record carry both.
        CheckConstraint(
            f"num_nonnulls(stage_id, goal_id) = CASE WHEN kind = '{RecordKind.TEST}' "
            "THEN 1 ELSE 0 END",
            name="ck_record_test_target",
        ),
        CheckConstraint(
            "duration_minutes IS NULL OR duration_minutes >= 0",
            name="ck_record_duration_non_negative",
        ),
    )


class RecordReference(Base):
    """A reference used for the record. `note_resource`'s shape."""

    __tablename__ = "record_reference"

    id: Mapped[int] = mapped_column(primary_key=True)
    record_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("record.id", ondelete="CASCADE"), nullable=False, index=True
    )
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    name: Mapped[str | None] = mapped_column(String, nullable=True)
    url: Mapped[str] = mapped_column(String, nullable=False)

    record = relationship("Record", back_populates="references")

    __table_args__ = (
        CheckConstraint("btrim(url) <> ''", name="ck_record_reference_has_a_url"),
    )
