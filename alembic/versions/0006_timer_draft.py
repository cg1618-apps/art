"""timer draft

`active_timer.draft`: the record a timer will become, filled in while it runs.
Nullable JSONB, no default; an existing timer keeps running with no draft.

`tests/test_migrations_build_the_schema.py` compares the result against the
models.

Revision ID: 0006_timer_draft
Revises: 0005_timer
Create Date: 2026-10-03

"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "0006_timer_draft"
down_revision = "0005_timer"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "active_timer",
        sa.Column("draft", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )


def downgrade() -> None:
    """The column. A timer's draft is not history: it is lost with the
    revision, as the timer itself is with 0005's."""
    op.drop_column("active_timer", "draft")
