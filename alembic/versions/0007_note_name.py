"""note name

A note has one name. `note.name` replaces `name_cn`, `name_en`, `name_alt`
and the `note_alias` table, and `ck_note_name_not_blank` replaces
`ck_note_has_a_name`.

**Nothing typed is lost.** Each note's name is its first filled slot - cn,
then en, then alt, the order `display_name` used - so what the library showed
is what it shows now. Every other slot and every alias that differs from that
name is appended to the note's `remark` as one line, `其他名稱：a、b、c`, under
any remark already there.

The downgrade puts the three columns, the alias table and the old check back,
and copies `name` into `name_cn`. It does not take the 其他名稱 line back out of
the remark: the names are still readable there, and parsing them back into
slots would guess which slot each came from.

`tests/test_migrations_build_the_schema.py` compares the result against the
models, and runs the data path both ways.

Revision ID: 0007_note_name
Revises: 0006_timer_draft
Create Date: 2026-10-03

"""

import sqlalchemy as sa

from alembic import op

revision = "0007_note_name"
down_revision = "0006_timer_draft"
branch_labels = None
depends_on = None

OTHER_NAMES = "其他名稱："
# The enumeration comma: what the note form splits aliases on, and what a
# Chinese list of names is written with.
SEPARATOR = "、"
# Only a row written by hand could have every slot blank - `ck_note_has_a_name`
# counts NULLs, not blanks - but the new check refuses an empty name, so such a
# row needs one.
UNNAMED = "未命名"


def _clean(value: str | None) -> str | None:
    if value is None:
        return None
    value = value.strip()
    return value or None


def name_and_remark(slots, aliases, remark):
    """The name a note keeps, and its remark with every other name appended.

    `slots` are name_cn, name_en, name_alt in that order; `aliases` the
    note's aliases in the order they were written. Repeats, and anything equal
    to the chosen name, are dropped. Pure, so the test can call it.
    """
    names = [v for v in (_clean(s) for s in slots) if v]
    name = names[0] if names else UNNAMED
    others: list[str] = []
    for value in names[1:] + [v for v in (_clean(a) for a in aliases) if v]:
        if value != name and value not in others:
            others.append(value)
    if not others:
        return name, remark
    line = OTHER_NAMES + SEPARATOR.join(others)
    existing = (remark or "").rstrip()
    return name, f"{existing}\n{line}" if existing else line


def upgrade() -> None:
    op.add_column("note", sa.Column("name", sa.String(), nullable=True))

    conn = op.get_bind()
    notes = conn.execute(
        sa.text("SELECT id, name_cn, name_en, name_alt, remark FROM note ORDER BY id")
    ).all()
    aliases: dict[int, list[str]] = {}
    for note_id, value in conn.execute(
        sa.text("SELECT note_id, value FROM note_alias ORDER BY note_id, id")
    ):
        aliases.setdefault(note_id, []).append(value)
    for note_id, name_cn, name_en, name_alt, remark in notes:
        name, new_remark = name_and_remark(
            (name_cn, name_en, name_alt), aliases.get(note_id, []), remark
        )
        conn.execute(
            sa.text("UPDATE note SET name = :name, remark = :remark WHERE id = :id"),
            {"name": name, "remark": new_remark, "id": note_id},
        )

    op.alter_column("note", "name", nullable=False)
    op.create_check_constraint("ck_note_name_not_blank", "note", "btrim(name) <> ''")
    op.drop_constraint("ck_note_has_a_name", "note", type_="check")
    op.drop_table("note_alias")
    op.drop_column("note", "name_cn")
    op.drop_column("note", "name_en")
    op.drop_column("note", "name_alt")


def downgrade() -> None:
    """0002's columns, table and check, with `name` copied into `name_cn`.
    The aliases are not restored: the 其他名稱 line in the remark holds them."""
    op.add_column("note", sa.Column("name_cn", sa.String(), nullable=True))
    op.add_column("note", sa.Column("name_en", sa.String(), nullable=True))
    op.add_column("note", sa.Column("name_alt", sa.String(), nullable=True))
    op.execute("UPDATE note SET name_cn = name")
    op.drop_constraint("ck_note_name_not_blank", "note", type_="check")
    op.create_check_constraint(
        "ck_note_has_a_name", "note", "num_nonnulls(name_cn, name_en, name_alt) >= 1"
    )
    op.drop_column("note", "name")

    op.create_table(
        "note_alias",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("note_id", sa.Integer(), nullable=False),
        sa.Column("value", sa.String(), nullable=False),
        sa.ForeignKeyConstraint(
            ["note_id"], ["note.id"], name="note_alias_note_id_fkey", ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id", name="note_alias_pkey"),
        sa.UniqueConstraint("note_id", "value", name="uq_note_alias"),
    )
    op.create_index("ix_note_alias_note_id", "note_alias", ["note_id"])
    op.create_index("ix_note_alias_lookup", "note_alias", [sa.text("lower(value)")])
