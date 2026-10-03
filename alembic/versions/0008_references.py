"""references

The Reference module: `reference`, a link with a name and notes, and
`reference_group`, its group tags. The `reference_group` option category is
registered, so `ck_system_option_category` is replaced. Nothing is seeded:
the owner creates the groups.

Frozen values rather than an import, as every revision here.
`tests/test_migrations_build_the_schema.py` compares the result against the
models.

Revision ID: 0008_references
Revises: 0007_note_name
Create Date: 2026-10-03

"""

import sqlalchemy as sa

from alembic import op

revision = "0008_references"
down_revision = "0007_note_name"
branch_labels = None
depends_on = None

# OPTION_CATEGORIES' keys before and after this revision.
OLD_CATEGORIES = ("note_category", "topic", "method", "source", "location", "tool")
NEW_CATEGORIES = ("reference_group",)
CATEGORIES = OLD_CATEGORIES + NEW_CATEGORIES


def _in(column: str, values: tuple[str, ...]) -> str:
    return f"{column} IN ({', '.join(repr(v) for v in values)})"


def upgrade() -> None:
    op.drop_constraint("ck_system_option_category", "system_option", type_="check")
    op.create_check_constraint(
        "ck_system_option_category", "system_option", _in("category", CATEGORIES)
    )

    op.create_table(
        "reference",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("url", sa.String(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.CheckConstraint("btrim(name) <> ''", name="ck_reference_name_not_blank"),
        sa.CheckConstraint("btrim(url) <> ''", name="ck_reference_has_a_url"),
        sa.PrimaryKeyConstraint("id", name="reference_pkey"),
    )

    op.create_table(
        "reference_group",
        sa.Column("reference_id", sa.Integer(), nullable=False),
        sa.Column("option_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["reference_id"],
            ["reference.id"],
            name="reference_group_reference_id_fkey",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["option_id"],
            ["system_option.id"],
            name="reference_group_option_id_fkey",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("reference_id", "option_id", name="reference_group_pkey"),
    )
    op.create_index("ix_reference_group_option", "reference_group", ["option_id"])


def downgrade() -> None:
    """The two tables, then the category's values - nothing names them once
    the tables are gone - and the old category check back."""
    op.drop_table("reference_group")
    op.drop_table("reference")

    op.get_bind().execute(
        sa.text("DELETE FROM system_option WHERE category IN :categories").bindparams(
            sa.bindparam("categories", expanding=True)
        ),
        {"categories": list(NEW_CATEGORIES)},
    )
    op.drop_constraint("ck_system_option_category", "system_option", type_="check")
    op.create_check_constraint(
        "ck_system_option_category", "system_option", _in("category", OLD_CATEGORIES)
    )
