"""The running timer: live session state, not a catalogue row.

At most one row (`uq_active_timer_single`, a unique index on a constant). The
server holds it so a refresh, a closed tab or a sleeping laptop loses nothing;
the browser does the ticking.

**Every time comes from the database clock**, never the client's: two devices
must agree on one timer. The state is derived - `running` while
`running_since` is set, `stopped` once `stopped_at` is, `paused` with neither -
and `ck_active_timer_state` keeps both from being set at once.

The activity is SET NULL with its drill or exercise, not RESTRICT: a running
timer is not history, and deleting the drill should not be blocked by it.
"""

import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.constants import TimerMode, TimerState
from app.database import Base
from app.models.base import TimestampMixin, in_clause
from app.models.exercise import Drill, Exercise


class ActiveTimer(Base, TimestampMixin):
    __tablename__ = "active_timer"

    id: Mapped[int] = mapped_column(primary_key=True)
    mode: Mapped[str] = mapped_column(String, nullable=False)
    # A countdown's target; NULL for a stopwatch.
    target_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    # When it was first started; pausing does not move it.
    started_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    # NULL while paused or stopped.
    running_since: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    # Counted before `running_since`: the live figure is this plus
    # (now - running_since) while running.
    elapsed_seconds: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    # Set by stop. A stopped timer waits for its record.
    stopped_at: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    drill_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("drill.id", ondelete="SET NULL"), nullable=True, index=True
    )
    exercise_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("exercise.id", ondelete="SET NULL"), nullable=True, index=True
    )

    drill = relationship(Drill)
    exercise = relationship(Exercise)

    @property
    def activity_exercise(self) -> Exercise | None:
        """The exercise timed: named directly, or through the drill."""
        if self.drill is not None:
            return self.drill.exercise
        return self.exercise

    @property
    def state(self) -> TimerState:
        if self.stopped_at is not None:
            return TimerState.STOPPED
        if self.running_since is not None:
            return TimerState.RUNNING
        return TimerState.PAUSED

    __table_args__ = (
        # A unique index on a constant: a second row collides with the first.
        Index("uq_active_timer_single", text("(true)"), unique=True),
        CheckConstraint(in_clause("mode", TimerMode), name="ck_active_timer_mode"),
        CheckConstraint(
            f"CASE WHEN mode = '{TimerMode.COUNTDOWN}' THEN target_seconds IS NOT NULL "
            "ELSE target_seconds IS NULL END",
            name="ck_active_timer_target",
        ),
        CheckConstraint(
            "target_seconds IS NULL OR target_seconds >= 1",
            name="ck_active_timer_target_positive",
        ),
        CheckConstraint(
            "elapsed_seconds >= 0", name="ck_active_timer_elapsed_non_negative"
        ),
        CheckConstraint(
            "num_nonnulls(drill_id, exercise_id) <= 1", name="ck_active_timer_one_activity"
        ),
        CheckConstraint(
            "num_nonnulls(running_since, stopped_at) <= 1", name="ck_active_timer_state"
        ),
    )
