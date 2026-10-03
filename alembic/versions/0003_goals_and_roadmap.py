"""goals and roadmap

Modules 2 and 3 built together: `goal` (a level), `stage` (a step of one) and
`stage_resource` (the lectures kept with a stage). Then the seed: the six
levels and sixteen stages agreed with the owner. They are the seed, not the
truth - the Roadmap page edits them.

Frozen values rather than an import, for the CHECKs and the seed alike: a
migration that imports app code breaks the day a later revision changes it.
`tests/test_migrations_build_the_schema.py` compares the result against the
models, so a drift between this file and them fails there.

Revision ID: 0003_goals_and_roadmap
Revises: 0002_notes_and_options
Create Date: 2026-10-03

"""

import sqlalchemy as sa

from alembic import op

revision = "0003_goals_and_roadmap"
down_revision = "0002_notes_and_options"
branch_labels = None
depends_on = None

# GoalStatus' and StageStatus' values, as they stand today.
GOAL_STATUSES = ("planned", "active", "achieved")
STAGE_STATUSES = ("not_started", "in_progress", "passed")

# (code, name_cn, name_en, description, test, status), in roadmap order; the
# place in this tuple is the goal's position.
GOALS = (
    (
        "L0",
        "基礎",
        "Foundations",
        "能穩定地畫出線條與基本形狀，並把方塊、圓柱、球體放進透視空間。",
        "一頁穩定的線條與橢圓，加上 20 個隨機角度、看起來都立體的方塊。",
        "active",
    ),
    (
        "L1",
        "人體",
        "Figure",
        "能憑想像畫出有動態的全身人體，在平視、俯視、仰視下比例都正確。頭部用簡單形體即可。",
        "同一個姿勢以平視、俯視、仰視各畫一次的人偶。",
        "planned",
    ),
    (
        "L2",
        "角色",
        "Character",
        "把人體變成具體的動漫角色：臉、表情、手、頭髮、衣服、小配件。",
        "從 Drawing List 選一個角色，以動作姿勢、三個角度各畫一次。",
        "planned",
    ),
    (
        "L3",
        "場景",
        "Scene",
        "把角色放進透視正確的背景，仍不上色：同一條地平線、合理的比例、腳踩在地上。",
        "角色在房間或街道中的線稿，兩點透視。",
        "planned",
    ),
    (
        "L4",
        "上色",
        "Colour",
        "先用灰階明度、再用顏色為角色上色，光源明確。",
        "簡單背景的上色角色。",
        "planned",
    ),
    (
        "L5",
        "插畫",
        "Illustration",
        "完成有背景的彩色插畫，包含動物、奇幻生物與特效。",
        "從縮圖到完稿的一張完整作品。",
        "planned",
    ),
)

# (goal code, name_cn, name_en, description, test), in roadmap order; the place
# inside its goal is the stage's position. Every stage seeds not_started.
STAGES = (
    (
        "L0",
        "Clip Studio Paint 設定",
        "Clip Studio Paint setup",
        "筆刷、穩定化、快捷鍵、翻轉畫布快捷鍵、透視尺，以及之後用來檢查比例與鏡頭角度的 3D 素描人偶。",
        "2 分鐘內擺好 3D 人偶的姿勢並設定鏡頭角度。",
    ),
    (
        "L0",
        "線條與形狀",
        "Lines and shapes",
        "只有 2D：直線、曲線、弧線、波浪線、鋸齒線、圓形、橢圓、方形、菱形。用手肘和肩膀畫，不用手腕。",
        "一頁穩定、不抖的線條與橢圓。",
    ),
    (
        "L0",
        "空間中的形體",
        "Form in space",
        "方塊、圓柱、球體在一點、兩點、三點透視中，自由旋轉。",
        "20 個隨機角度、看起來都立體的方塊，以及橢圓正確的圓柱。",
    ),
    (
        "L1",
        "比例",
        "Proportion",
        "以頭身為單位的人體，用基本形體組成人偶。",
        "憑記憶畫出正面、側面、¾ 的人偶，疊在 3D 人偶上誤差在半個頭以內。",
    ),
    (
        "L1",
        "動態到人偶",
        "Gesture to mannequin",
        "動態線，然後是動態形狀與動態形體。",
        "憑想像畫一個動態，轉成人偶後仍保有動感。",
    ),
    (
        "L1",
        "透視中的人體",
        "Figure in perspective",
        "鏡頭角度、視錐、透視縮短。解決「看起來怪怪的」的階段。",
        "同一個姿勢以平視、俯視、仰視各畫一次。",
    ),
    (
        "L2",
        "主要肌肉量塊",
        "Major muscle masses",
        "胸廓、骨盆、肩帶與大肌群，疊在人偶上，只到量塊層級。",
        "在三個動態人偶上畫出主要量塊。",
    ),
    (
        "L2",
        "頭部、五官、表情",
        "Head, face, expression",
        "任何角度的頭部、五官位置、動漫風格化與表情。",
        "同一個角色，三個角度、六種表情。",
    ),
    (
        "L2",
        "手與腳",
        "Hands and feet",
        "用方塊與圓柱組成手和腳，再加上姿勢。",
        "一頁不同姿勢的手與腳。",
    ),
    (
        "L2",
        "完稿：頭髮、衣服、配件",
        "Finishing",
        "頭髮的大形、衣褶、配件、線條粗細、四階段流程。",
        "L2 的測驗作品。",
    ),
    (
        "L3",
        "環境透視",
        "Environment perspective",
        "找中心與複製平面、透視中的縮放與橢圓、空間分區。",
        "兩點透視的房間，家具都對準消失點。",
    ),
    (
        "L3",
        "構圖與角色入景",
        "Composition and character in scene",
        "縮圖、三分法、引導線，把角色放進場景。",
        "三張縮圖，選一張完成線稿。",
    ),
    (
        "L4",
        "明度與光影",
        "Value and light",
        "只用灰階：明度、單一光源、陰影。",
        "單一光源的灰階角色。",
    ),
    (
        "L4",
        "色彩",
        "Colour",
        "色相、明度、彩度，色彩和諧與上色流程。",
        "L4 的測驗作品。",
    ),
    (
        "L5",
        "完整插畫與生物",
        "Full pieces and creatures",
        "大氣透視、完整流程，以及用基本形體組成動物與奇幻生物。",
        "一張有背景的完整作品。",
    ),
    (
        "L5",
        "特效",
        "Effects",
        "火焰、閃電、魔法、發光、煙霧：形狀、由亮到暗的漸層，以及 Clip Studio Paint 的發光與相加類圖層。",
        "一張有火球的角色插畫。",
    ),
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
    """Idempotent: a goal whose code exists, and a stage whose goal already
    holds a stage of that name, are left as they are."""
    for position, (code, name_cn, name_en, description, test, status) in enumerate(GOALS):
        conn.execute(
            sa.text(
                """
                INSERT INTO goal (code, name_cn, name_en, position, description, test, status)
                SELECT :code, :name_cn, :name_en, :position, :description, :test, :status
                 WHERE NOT EXISTS (SELECT 1 FROM goal WHERE code = :code)
                """
            ),
            {
                "code": code,
                "name_cn": name_cn,
                "name_en": name_en,
                "position": position,
                "description": description,
                "test": test,
                "status": status,
            },
        )

    positions: dict[str, int] = {}
    for code, name_cn, name_en, description, test in STAGES:
        position = positions.get(code, 0)
        positions[code] = position + 1
        conn.execute(
            sa.text(
                """
                INSERT INTO stage (goal_id, position, name_cn, name_en, description, test)
                SELECT goal.id, :position, :name_cn, :name_en, :description, :test
                  FROM goal
                 WHERE goal.code = :code
                   AND NOT EXISTS (
                       SELECT 1 FROM stage
                        WHERE stage.goal_id = goal.id
                          AND stage.name_cn = :name_cn)
                """
            ),
            {
                "code": code,
                "position": position,
                "name_cn": name_cn,
                "name_en": name_en,
                "description": description,
                "test": test,
            },
        )


def upgrade() -> None:
    op.create_table(
        "goal",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(), nullable=False),
        sa.Column("name_cn", sa.String(), nullable=True),
        sa.Column("name_en", sa.String(), nullable=True),
        sa.Column("name_alt", sa.String(), nullable=True),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("test", sa.Text(), nullable=True),
        sa.Column("status", sa.String(), server_default="planned", nullable=False),
        sa.Column("achieved_on", sa.Date(), nullable=True),
        sa.Column("remark", sa.Text(), nullable=True),
        *_timestamps(),
        sa.CheckConstraint(
            "num_nonnulls(name_cn, name_en, name_alt) >= 1", name="ck_goal_has_a_name"
        ),
        sa.CheckConstraint(_in("status", GOAL_STATUSES), name="ck_goal_status"),
        sa.CheckConstraint(
            "achieved_on IS NULL OR status = 'achieved'",
            name="ck_goal_achieved_on_iff_achieved",
        ),
        sa.PrimaryKeyConstraint("id", name="goal_pkey"),
        sa.UniqueConstraint("code", name="uq_goal_code"),
    )

    op.create_table(
        "stage",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("goal_id", sa.Integer(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("name_cn", sa.String(), nullable=True),
        sa.Column("name_en", sa.String(), nullable=True),
        sa.Column("name_alt", sa.String(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("test", sa.Text(), nullable=True),
        sa.Column("status", sa.String(), server_default="not_started", nullable=False),
        sa.Column("passed_on", sa.Date(), nullable=True),
        sa.Column("remark", sa.Text(), nullable=True),
        *_timestamps(),
        sa.CheckConstraint(
            "num_nonnulls(name_cn, name_en, name_alt) >= 1", name="ck_stage_has_a_name"
        ),
        sa.CheckConstraint(_in("status", STAGE_STATUSES), name="ck_stage_status"),
        sa.CheckConstraint(
            "passed_on IS NULL OR status = 'passed'", name="ck_stage_passed_on_iff_passed"
        ),
        sa.ForeignKeyConstraint(
            ["goal_id"], ["goal.id"], name="stage_goal_id_fkey", ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("id", name="stage_pkey"),
    )
    op.create_index("ix_stage_goal_id", "stage", ["goal_id"])

    op.create_table(
        "stage_resource",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("stage_id", sa.Integer(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(), nullable=True),
        sa.Column("url", sa.String(), nullable=False),
        sa.CheckConstraint("btrim(url) <> ''", name="ck_stage_resource_has_a_url"),
        sa.ForeignKeyConstraint(
            ["stage_id"], ["stage.id"], name="stage_resource_stage_id_fkey", ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id", name="stage_resource_pkey"),
    )
    op.create_index("ix_stage_resource_stage_id", "stage_resource", ["stage_id"])

    seed(op.get_bind())


def downgrade() -> None:
    """Everything this revision created, children first. The seeded rows go
    with their tables."""
    op.drop_table("stage_resource")
    op.drop_table("stage")
    op.drop_table("goal")
