"""A real migration, added to prove the rollback path reverses one.

REHEARSAL ONLY. This revision and the deliberate health failure that
accompanies it are removed in the follow-up change. It exists because
`downgrade` had never run end to end on any app in this platform: the refusal
path was tested against a scratch chain, and the reversal itself was not.

It creates a table rather than altering an existing one, so reversing it
cannot lose anything that was already there - the whole point of rehearsing on
the app with an empty database.
"""

import sqlalchemy as sa
from alembic import op

revision = "0002_rollback_rehearsal"
down_revision = "0001_baseline"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "rollback_rehearsal",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("note", sa.Text(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("rollback_rehearsal")
