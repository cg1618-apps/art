"""notes and options

The first module's schema: `system_option`, the open vocabularies the Options
page edits, and `note` with its aliases, resources and topic links. Then the
seed: the values of the three categories this module registers.

Frozen values rather than an import, for both the CHECK and the seed: a
migration that imports app code breaks the day a later revision changes it.
`tests/test_migrations_build_the_schema.py` compares the result against the
models, so a drift between this file and them fails there.

Revision ID: 0002_notes_and_options
Revises: 0001_baseline
Create Date: 2026-10-03

"""

import sqlalchemy as sa

from alembic import op

revision = "0002_notes_and_options"
down_revision = "0001_baseline"
branch_labels = None
depends_on = None

# OPTION_CATEGORIES' keys, and Visibility's values, as they stand today.
CATEGORIES = ("note_category", "topic", "method")
VISIBILITIES = ("private", "unlisted", "public")

# (category, value, description), each category in its seeded order; the
# position inside a category is its sort_order.
SEED = (
    ("note_category", "名詞", None),
    ("note_category", "知識", None),
    ("note_category", "小技巧", None),
    ("note_category", "建議", None),
    ("topic", "線條", None),
    ("topic", "形狀", None),
    ("topic", "透視", None),
    ("topic", "比例", None),
    ("topic", "人體", None),
    ("topic", "動態", None),
    ("topic", "構圖", None),
    ("topic", "光影", None),
    ("topic", "色彩", None),
    ("topic", "特效", None),
    ("method", "臨摹", "直接在參考圖上方描繪，盡量完整還原。（很少使用）"),
    (
        "method",
        "重現",
        "不疊在參考圖上，看著參考圖盡量完整還原整張圖，例如動畫截圖。屬於描寫的一種。",
    ),
    ("method", "描寫", "看著參考圖畫，不疊在參考圖上。不要求完整還原。"),
    ("method", "速寫", "限時快速畫，抓動態和大形，不追求細節。"),
    ("method", "同人創作", "以既有角色或作品為題材的創作：構圖和姿勢是自己的，對象是別人的。"),
    ("method", "原創創作", "原創題材，例如自己的原創角色。可以使用參考資料。"),
    ("method", "隨便畫", "沒有特定目標，想畫什麼就畫什麼。"),
)


def _in(column: str, values: tuple[str, ...]) -> str:
    return f"{column} IN ({', '.join(repr(v) for v in values)})"


def _timestamps() -> list[sa.Column]:
    return [
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    ]


def seed(conn) -> None:
    """Idempotent: a value already in its category (by the unique index's
    rule, trimmed and case-folded) is left as it is."""
    positions: dict[str, int] = {}
    for category, value, description in SEED:
        sort_order = positions.get(category, 0)
        positions[category] = sort_order + 1
        conn.execute(
            sa.text(
                """
                INSERT INTO system_option (category, value, description, sort_order)
                SELECT :category, :value, :description, :sort_order
                 WHERE NOT EXISTS (
                       SELECT 1 FROM system_option
                        WHERE category = :category
                          AND lower(btrim(value)) = lower(btrim(:value)))
                """
            ),
            {
                "category": category,
                "value": value,
                "description": description,
                "sort_order": sort_order,
            },
        )


def upgrade() -> None:
    op.create_table(
        "system_option",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("category", sa.String(), nullable=False),
        sa.Column("value", sa.String(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("remark", sa.Text(), nullable=True),
        sa.Column("sort_order", sa.Integer(), server_default="0", nullable=False),
        *_timestamps(),
        sa.CheckConstraint(_in("category", CATEGORIES), name="ck_system_option_category"),
        sa.PrimaryKeyConstraint("id", name="system_option_pkey"),
    )
    op.create_index(
        "uq_system_option_value",
        "system_option",
        ["category", sa.text("lower(btrim(value))")],
        unique=True,
    )

    op.create_table(
        "note",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name_cn", sa.String(), nullable=True),
        sa.Column("name_en", sa.String(), nullable=True),
        sa.Column("name_alt", sa.String(), nullable=True),
        sa.Column("category_id", sa.Integer(), nullable=True),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("body", sa.Text(), nullable=True),
        sa.Column("remark", sa.Text(), nullable=True),
        sa.Column("visibility", sa.String(), server_default="private", nullable=False),
        *_timestamps(),
        sa.CheckConstraint(
            "num_nonnulls(name_cn, name_en, name_alt) >= 1", name="ck_note_has_a_name"
        ),
        sa.CheckConstraint(_in("visibility", VISIBILITIES), name="ck_note_visibility"),
        sa.ForeignKeyConstraint(
            ["category_id"],
            ["system_option.id"],
            name="note_category_id_fkey",
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name="note_pkey"),
    )
    op.create_index("ix_note_category_id", "note", ["category_id"])

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

    op.create_table(
        "note_resource",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("note_id", sa.Integer(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(), nullable=True),
        sa.Column("url", sa.String(), nullable=False),
        sa.CheckConstraint("btrim(url) <> ''", name="ck_note_resource_has_a_url"),
        sa.ForeignKeyConstraint(
            ["note_id"], ["note.id"], name="note_resource_note_id_fkey", ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id", name="note_resource_pkey"),
    )
    op.create_index("ix_note_resource_note_id", "note_resource", ["note_id"])

    op.create_table(
        "note_topic",
        sa.Column("note_id", sa.Integer(), nullable=False),
        sa.Column("option_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["note_id"], ["note.id"], name="note_topic_note_id_fkey", ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["option_id"],
            ["system_option.id"],
            name="note_topic_option_id_fkey",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("note_id", "option_id", name="note_topic_pkey"),
    )
    op.create_index("ix_note_topic_option", "note_topic", ["option_id"])

    seed(op.get_bind())


def downgrade() -> None:
    """Everything this revision created, children first. The seeded values go
    with their table."""
    op.drop_table("note_topic")
    op.drop_table("note_resource")
    op.drop_table("note_alias")
    op.drop_table("note")
    op.drop_table("system_option")
