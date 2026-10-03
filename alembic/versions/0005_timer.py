"""timer

Module 6: `active_timer`, the one running timer. At most one row, held by a
unique index on a constant (`uq_active_timer_single`). Nothing is seeded.

Frozen values rather than an import, as in 0004: a migration that imports app
code breaks the day a later revision changes it.
`tests/test_migrations_build_the_schema.py` compares the result against the
models.

Revision ID: 0005_timer
Revises: 0004_exercises_and_records
Create Date: 2026-10-03

"""

import sqlalchemy as sa

from alembic import op

revision = "0005_timer"
down_revision = "0004_exercises_and_records"
branch_labels = None
depends_on = None

# TimerMode's values, as they stand today.
TIMER_MODES = ("stopwatch", "countdown")


def _in(column: str, values: tuple[str, ...]) -> str:
    return f"{column} IN ({', '.join(repr(v) for v in values)})"


def upgrade() -> None:
    op.create_table(
        "active_timer",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("mode", sa.String(), nullable=False),
        sa.Column("target_seconds", sa.Integer(), nullable=True),
        sa.Column(
            "started_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("running_since", sa.DateTime(timezone=True), nullable=True),
        sa.Column("elapsed_seconds", sa.Integer(), server_default="0", nullable=False),
        sa.Column("stopped_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("drill_id", sa.Integer(), nullable=True),
        sa.Column("exercise_id", sa.Integer(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.CheckConstraint(_in("mode", TIMER_MODES), name="ck_active_timer_mode"),
        sa.CheckConstraint(
            "CASE WHEN mode = 'countdown' THEN target_seconds IS NOT NULL "
            "ELSE target_seconds IS NULL END",
            name="ck_active_timer_target",
        ),
        sa.CheckConstraint(
            "target_seconds IS NULL OR target_seconds >= 1",
            name="ck_active_timer_target_positive",
        ),
        sa.CheckConstraint("elapsed_seconds >= 0", name="ck_active_timer_elapsed_non_negative"),
        sa.CheckConstraint(
            "num_nonnulls(drill_id, exercise_id) <= 1", name="ck_active_timer_one_activity"
        ),
        sa.CheckConstraint(
            "num_nonnulls(running_since, stopped_at) <= 1", name="ck_active_timer_state"
        ),
        sa.ForeignKeyConstraint(
            ["drill_id"], ["drill.id"], name="active_timer_drill_id_fkey", ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(
            ["exercise_id"],
            ["exercise.id"],
            name="active_timer_exercise_id_fkey",
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name="active_timer_pkey"),
    )
    op.create_index("ix_active_timer_drill_id", "active_timer", ["drill_id"])
    op.create_index("ix_active_timer_exercise_id", "active_timer", ["exercise_id"])
    op.create_index("uq_active_timer_single", "active_timer", [sa.text("(true)")], unique=True)


def downgrade() -> None:
    """The table, and with it its indexes. A timer is not history: a running
    one is lost with the revision, by design."""
    op.drop_table("active_timer")
