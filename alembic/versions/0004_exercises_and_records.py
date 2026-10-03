"""exercises and records

Module 5: `exercise` (what is practised) with its aliases, resources and topic
links; `drill` (one prescribed way of practising it) with its source links and
resources; `record` (one exercise practised) with its reference links. Three
option categories are registered - `source`, `location`, `tool` - so
`ck_system_option_category` is replaced. Then the seed: their values, and the
24 exercises and 57 drills agreed with the owner. They are the seed, not the
truth - the pages edit them.

Frozen values rather than an import, for the CHECKs and the seed alike: a
migration that imports app code breaks the day a later revision changes it.
`tests/test_migrations_build_the_schema.py` compares the result against the
models, so a drift between this file and them fails there.

Revision ID: 0004_exercises_and_records
Revises: 0003_goals_and_roadmap
Create Date: 2026-10-03

"""

import sqlalchemy as sa

from alembic import op

revision = "0004_exercises_and_records"
down_revision = "0003_goals_and_roadmap"
branch_labels = None
depends_on = None

# OPTION_CATEGORIES' keys before and after this revision, and RecordKind's
# values, as they stand today.
OLD_CATEGORIES = ("note_category", "topic", "method")
NEW_CATEGORIES = ("source", "location", "tool")
CATEGORIES = OLD_CATEGORIES + NEW_CATEGORIES
RECORD_KINDS = ("practice", "piece", "test")

# (category, value), each category in its seeded order; the position inside a
# category is its sort_order.
OPTIONS = (
    ("source", "Character Art School"),
    ("source", "Character Art School: Coloring"),
    ("source", "Manga Art School"),
    ("source", "Perspective Art School"),
    ("source", "自訂"),
    ("source", "其他"),
    ("location", "台灣・家"),
    ("location", "美國・家"),
    ("tool", "Clip Studio Paint"),
    ("tool", "Procreate"),
    ("tool", "紙筆"),
)

# (name_cn, name_en, (goal code, stage name_cn) or None, description). A
# drill names its exercise by its place in this tuple, counted from 1.
EXERCISES = (
    ("線條", "Lines", ("L0", "線條與形狀"), "穩定的直線與曲線，用手肘和肩膀畫，不用手腕。"),  # 1
    ("2D 形狀", "2D shapes", ("L0", "線條與形狀"), "平面的基本形狀，由小到大。"),  # 2
    ("用線條概括", "Summarise with lines", ("L0", "線條與形狀"), "用最少的線抓住物體的大結構。"),  # 3
    ("基本形體", "Basic forms", ("L0", "空間中的形體"), "方塊、球體、圓柱、圓錐，不同角度。"),  # 4
    ("透視方塊", "Boxes in perspective", ("L0", "空間中的形體"), "一點、兩點、三點透視中的方塊與堆疊。"),  # 5
    ("人體比例", "Body proportion", ("L1", "比例"), "以頭身為單位的人體比例。"),  # 6
    ("人偶", "Mannequin", ("L1", "比例"), "從動態線到人偶的五個步驟。"),  # 7
    ("動態速寫", "Gesture drawing", None, "限時抓動態。每個等級都練，所以不屬於任何階段。"),  # 8
    ("動態形狀與形體", "Dynamic gestures", ("L1", "動態到人偶"), "把動態轉成形狀，再轉成形體。"),  # 9
    ("鏡頭與視角", "Camera and view", ("L1", "透視中的人體"), "鏡頭角度、視錐與空間分區。"),  # 10
    ("透視中的人體", "Figure in perspective", ("L1", "透視中的人體"), "完整形體的人體放進透視。"),  # 11
    ("肌肉量塊", "Muscle masses", ("L2", "主要肌肉量塊"), "疊在動態上的主要肌群量塊。"),  # 12
    ("頭部", "Head", ("L2", "頭部、五官、表情"), "任何角度的頭部與五官。"),  # 13
    ("表情", "Expression", ("L2", "頭部、五官、表情"), "表情與情緒。"),  # 14
    ("手", "Hands", ("L2", "手與腳"), "手的比例與結構。"),  # 15
    ("頭髮", "Hair", ("L2", "完稿：頭髮、衣服、配件"), "頭髮的大形與設計。"),  # 16
    ("衣服與衣褶", "Clothing and folds", ("L2", "完稿：頭髮、衣服、配件"), "衣褶種類與穿在人體上的衣服。"),  # 17
    ("完稿流程", "Workflow", ("L2", "完稿：頭髮、衣服、配件"), "從草稿到線稿的流程。"),  # 18
    ("環境透視技巧", "Environment perspective", ("L3", "環境透視"), "找中心、複製平面、縮放與透視中的橢圓。"),  # 19
    ("構圖", "Composition", ("L3", "構圖與角色入景"), "結合構圖理論，角色半身作品。"),  # 20
    ("色彩複製", "Colour matching", ("L4", "色彩"), "判斷並複製顏色：先色相，再明度。"),  # 21
    ("角色作品", "Character piece", None, "一張完整的角色，粗糙也沒關係。每個等級都畫。"),  # 22
    ("視覺資料庫", "Visual library", None, "依主題累積看過、畫過的東西。"),  # 23
    ("對照畫", "Comparative drawing", None, "同一張圖隔一段時間再畫一次，比較進步。"),  # 24
)

# (exercise number, name, source value, unit, target, suggested_minutes,
# frequency, instructions), in the order listed; the place inside its
# exercise is the drill"s position.
DRILLS = (
    (1, "基本線條", "自訂", "頁", 1, 10, "每天（暖身）", "直線（水平、垂直、斜線，兩個方向）、1/4 圓弧、半圓弧、波浪線、鋸齒線。長短、輕重各練。"),
    (1, "綜合線條", "自訂", "組", 50, 10, "每天", "隨意畫各種交錯的直線與曲線，隨意選區擷取後臨摹，要畫精準。"),
    (2, "基本形狀", "自訂", "頁", 1, 10, "每天", "正方形、圓形、方形、橢圓形、菱形，由小到大。"),
    (3, "用線條概括", "自訂", "張", 20, 10, "每天", "隨機找圖，旁邊擴展等大的空白畫布。先畫最大分割的紅線（不超過 3 條），再畫次要分割的藍線。"),
    (4, "Static & Dynamic Forms", "Character Art School", "頁", 1, 60, "daily", None),
    (
        4,
        "幾何概括+翻轉",
        "自訂",
        "張",
        10,
        30,
        "每天",
        "隨機找有獨立物體的圖，用基本幾何（可以變形，例如橢圓）概括物體的結構，物體本身和位置都要準確。再把物體裝進盒子，根據概括畫出翻轉後的版本，每個概括 2 個。",
    ),
    (5, "1 Point Perspective", "Perspective Art School", "頁", 1, 120, "Daily / Weekly", None),
    (5, "2 Point Perspective", "Perspective Art School", "頁", 1, 120, "Daily / Weekly", None),
    (5, "3 Point Perspective", "Perspective Art School", "頁", 1, 120, "Daily / Weekly", None),
    (5, "Stacking Perspective", "Perspective Art School", "頁", 1, 120, "Daily / Weekly", None),
    (6, "Proportions", "Character Art School", "頁", 1, 60, "daily until memorized", None),
    (6, "Character Forms", "Character Art School", "頁", 1, 30, "daily", None),
    (6, "Body Proportion", "Manga Art School", "頁", 1, 60, "weekly until learned", None),
    (6, "Head & Body Sketches", "Manga Art School", "頁", 1, 120, "once off", None),
    (7, "骨架五步", "自訂", "張", 1, 10, "每天", "1. 從 Line of Action 取參考。2. 畫動態線。3. 火柴人。4. 幾何人。5. 人偶。"),
    (8, "Line of Action 30 秒", "自訂", "張", 20, 10, "每天", "30 秒一張，只抓動態線和大形。"),
    (8, "Line of Action 1 分鐘", "自訂", "張", 8, 10, "每天", "1 分鐘一張，動態線加上簡單的形體。"),
    (8, "Life Gestures", "Character Art School", "頁", 1, 5, "daily / forever if possible", None),
    (9, "Dynamic Shape Gestures", "Character Art School", "頁", 1, 20, "daily for 3 weeks", None),
    (9, "Dynamic Form Gestures", "Character Art School", "頁", 1, 40, "daily for 3 weeks", None),
    (10, "Camera Angle", "Perspective Art School", "頁", 1, 120, "Daily / Weekly", None),
    (10, "Cone of Vision", "Perspective Art School", "頁", 1, 120, "Weekly", None),
    (10, "Spatial Zones", "Perspective Art School", "頁", 1, 60, "once off", None),
    (11, "Full Form Bodies", "Character Art School", "頁", 1, 60, "daily / every 2nd day", None),
    (12, "Anatomical Gestures", "Character Art School", "頁", 1, 40, "daily for 3 weeks", None),
    (13, "Facial Features", "Character Art School", "頁", 1, 30, "daily", None),
    (13, "Heads & Features", "Character Art School", "頁", 1, 120, "daily / every 2nd day", None),
    (13, "Head Proportion", "Manga Art School", "頁", 1, 60, "weekly until learned", None),
    (13, "Eye Designs", "Manga Art School", "頁", 1, 120, "weekly", None),
    (13, "Head Drawings", "Manga Art School", "頁", 1, 60, "daily", None),
    (13, "Age Variation", "Manga Art School", "頁", 1, 60, "weekly / once off", None),
    (14, "Facial Expression Sheets", "Character Art School", "頁", 1, 90, "twice weekly", None),
    (14, "Observational Studies", "Character Art School", "頁", 1, 120, "once / month", None),
    (14, "Front View Face", "Manga Art School", "頁", 1, 60, "Daily / Weekly", None),
    (14, "Rotated View Face", "Manga Art School", "頁", 1, 120, "Daily / Weekly", None),
    (15, "Hands Proportion", "Manga Art School", "頁", 1, 60, "weekly until learned", None),
    (16, "Hair Design Sheets", "Character Art School", "頁", 1, 120, "twice weekly", None),
    (16, "Hair Design", "Manga Art School", "頁", 1, 60, "Daily / Weekly", None),
    (17, "Clothing Fold Types", "Character Art School", "頁", 1, 120, "one time", None),
    (17, "Character w/ Clothing", "Manga Art School", "張", 1, 120, "once off", None),
    (
        18,
        "4 Stage Workflow Drawings",
        "Character Art School",
        "張",
        1,
        120,
        "daily / every 2nd day",
        None,
    ),
    (
        18,
        "2 Stage Workflow Drawings",
        "Character Art School",
        "張",
        1,
        120,
        "daily / every 2nd day",
        None,
    ),
    (18, "Manga Clean-Up", "Manga Art School", "張", 1, 180, "once off", None),
    (18, "Final Drawing", "Manga Art School", "張", 1, 240, "once off", None),
    (18, "Character Drawing", "Character Art School", "張", 1, 180, None, None),
    (
        19,
        "Finding Center and Duplicating Planes",
        "Perspective Art School",
        "頁",
        1,
        120,
        "Daily / Weekly",
        None,
    ),
    (19, "Scaling In Perspective", "Perspective Art School", "頁", 1, 120, "Daily / Weekly", None),
    (
        19,
        "Drawing Ellipses in Perspective",
        "Perspective Art School",
        "頁",
        1,
        120,
        "Daily / Weekly",
        None,
    ),
    (
        19,
        "Complete Environment Piece",
        "Perspective Art School",
        "張",
        1,
        None,
        "Weekly / Self-Directed",
        None,
    ),
    (20, "Combining Theories", "Character Art School", "張", 1, 240, "one time", None),
    (20, "Character Busts", "Character Art School", "張", 1, 240, "one time", None),
    (21, "色彩複製", "自訂", "個", 20, 10, "每天", "隨機找圖，閉眼用吸管隨機取幾個顏色，刷到空白畫布上，再試著複製：先色相，再明度，要準確。"),
    (22, "週末粗稿", "自訂", "張", 1, 30, "每週", "畫任何想畫的角色，用目前等級的能力，不求精修。"),
    (22, "Personal Character Piece", "Character Art School", "張", 1, 180, "weekly", None),
    (22, "Character Fanart Piece", "Character Art School", "張", 1, 180, "weekly", None),
    (23, "Visual Library Development", "Character Art School", "主題", 1, 60, "weekly", None),
    (24, "Comparative Drawing", "Character Art School", "張", 1, 180, "once off", None),
)

# Exercises (counted from 1) that carry the Line of Action resource.
LINE_OF_ACTION = ("Line of Action", "https://line-of-action.com/")
LINE_OF_ACTION_EXERCISES = (7, 8)


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


def _link_table(table: str, owner: str) -> None:
    """A `note_resource`-shaped table owned by `owner`."""
    op.create_table(
        table,
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column(f"{owner}_id", sa.Integer(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(), nullable=True),
        sa.Column("url", sa.String(), nullable=False),
        sa.CheckConstraint("btrim(url) <> ''", name=f"ck_{table}_has_a_url"),
        sa.ForeignKeyConstraint(
            [f"{owner}_id"], [f"{owner}.id"], name=f"{table}_{owner}_id_fkey", ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id", name=f"{table}_pkey"),
    )
    op.create_index(f"ix_{table}_{owner}_id", table, [f"{owner}_id"])


def _option_fk(table: str, column: str) -> sa.ForeignKeyConstraint:
    return sa.ForeignKeyConstraint(
        [column], ["system_option.id"], name=f"{table}_{column}_fkey", ondelete="SET NULL"
    )


# The exercise a seeded drill or resource belongs to: by both seeded names,
# the first if the owner has since made a twin.
EXERCISE_BY_NAMES = """
    (SELECT id FROM exercise
      WHERE name_cn = :exercise_cn AND name_en = :exercise_en
      ORDER BY id LIMIT 1)
"""


def seed(conn) -> None:
    """Idempotent: an option already in its category, an exercise whose two
    names exist, a drill whose exercise already holds a drill of that name,
    and a resource already on its exercise are left as they are. A stage
    the owner renamed is not found, and the exercise is seeded with none."""
    positions: dict[str, int] = {}
    for category, value in OPTIONS:
        sort_order = positions.get(category, 0)
        positions[category] = sort_order + 1
        conn.execute(
            sa.text(
                """
                INSERT INTO system_option (category, value, sort_order)
                SELECT :category, :value, :sort_order
                 WHERE NOT EXISTS (
                       SELECT 1 FROM system_option
                        WHERE category = :category
                          AND lower(btrim(value)) = lower(btrim(:value)))
                """
            ),
            {"category": category, "value": value, "sort_order": sort_order},
        )

    for name_cn, name_en, stage, description in EXERCISES:
        goal_code, stage_cn = stage if stage is not None else (None, None)
        conn.execute(
            sa.text(
                """
                INSERT INTO exercise (name_cn, name_en, stage_id, description)
                SELECT :name_cn, :name_en,
                       (SELECT stage.id FROM stage JOIN goal ON goal.id = stage.goal_id
                         WHERE goal.code = :goal_code AND stage.name_cn = :stage_cn
                         ORDER BY stage.id LIMIT 1),
                       :description
                 WHERE NOT EXISTS (
                       SELECT 1 FROM exercise WHERE name_cn = :name_cn AND name_en = :name_en)
                """
            ),
            {
                "name_cn": name_cn,
                "name_en": name_en,
                "goal_code": goal_code,
                "stage_cn": stage_cn,
                "description": description,
            },
        )

    drill_positions: dict[int, int] = {}
    for number, name, source, unit, target, minutes, frequency, instructions in DRILLS:
        position = drill_positions.get(number, 0)
        drill_positions[number] = position + 1
        exercise_cn, exercise_en, _, _ = EXERCISES[number - 1]
        conn.execute(
            sa.text(
                f"""
                INSERT INTO drill (exercise_id, name, source_id, instructions, unit, target,
                                   suggested_minutes, frequency, position)
                SELECT exercise.id, :name,
                       (SELECT id FROM system_option
                         WHERE category = 'source' AND value = :source
                         ORDER BY id LIMIT 1),
                       :instructions, :unit, :target, :minutes, :frequency, :position
                  FROM exercise
                 WHERE exercise.id = {EXERCISE_BY_NAMES}
                   AND NOT EXISTS (
                       SELECT 1 FROM drill
                        WHERE drill.exercise_id = exercise.id AND drill.name = :name)
                """
            ),
            {
                "exercise_cn": exercise_cn,
                "exercise_en": exercise_en,
                "name": name,
                "source": source,
                "instructions": instructions,
                "unit": unit,
                "target": target,
                "minutes": minutes,
                "frequency": frequency,
                "position": position,
            },
        )

    resource_name, resource_url = LINE_OF_ACTION
    for number in LINE_OF_ACTION_EXERCISES:
        exercise_cn, exercise_en, _, _ = EXERCISES[number - 1]
        conn.execute(
            sa.text(
                f"""
                INSERT INTO exercise_resource (exercise_id, position, name, url)
                SELECT exercise.id,
                       (SELECT count(*) FROM exercise_resource r WHERE r.exercise_id = exercise.id),
                       :name, :url
                  FROM exercise
                 WHERE exercise.id = {EXERCISE_BY_NAMES}
                   AND NOT EXISTS (
                       SELECT 1 FROM exercise_resource r
                        WHERE r.exercise_id = exercise.id AND r.url = :url)
                """
            ),
            {
                "exercise_cn": exercise_cn,
                "exercise_en": exercise_en,
                "name": resource_name,
                "url": resource_url,
            },
        )


def upgrade() -> None:
    op.drop_constraint("ck_system_option_category", "system_option", type_="check")
    op.create_check_constraint(
        "ck_system_option_category", "system_option", _in("category", CATEGORIES)
    )

    op.create_table(
        "exercise",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name_cn", sa.String(), nullable=True),
        sa.Column("name_en", sa.String(), nullable=True),
        sa.Column("name_alt", sa.String(), nullable=True),
        sa.Column("stage_id", sa.Integer(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("remark", sa.Text(), nullable=True),
        *_timestamps(),
        sa.CheckConstraint(
            "num_nonnulls(name_cn, name_en, name_alt) >= 1", name="ck_exercise_has_a_name"
        ),
        sa.ForeignKeyConstraint(
            ["stage_id"], ["stage.id"], name="exercise_stage_id_fkey", ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("id", name="exercise_pkey"),
    )
    op.create_index("ix_exercise_stage_id", "exercise", ["stage_id"])

    op.create_table(
        "exercise_alias",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("exercise_id", sa.Integer(), nullable=False),
        sa.Column("value", sa.String(), nullable=False),
        sa.ForeignKeyConstraint(
            ["exercise_id"],
            ["exercise.id"],
            name="exercise_alias_exercise_id_fkey",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="exercise_alias_pkey"),
        sa.UniqueConstraint("exercise_id", "value", name="uq_exercise_alias"),
    )
    op.create_index("ix_exercise_alias_exercise_id", "exercise_alias", ["exercise_id"])
    op.create_index("ix_exercise_alias_lookup", "exercise_alias", [sa.text("lower(value)")])

    _link_table("exercise_resource", "exercise")

    op.create_table(
        "exercise_topic",
        sa.Column("exercise_id", sa.Integer(), nullable=False),
        sa.Column("option_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["exercise_id"],
            ["exercise.id"],
            name="exercise_topic_exercise_id_fkey",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["option_id"],
            ["system_option.id"],
            name="exercise_topic_option_id_fkey",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("exercise_id", "option_id", name="exercise_topic_pkey"),
    )
    op.create_index("ix_exercise_topic_option", "exercise_topic", ["option_id"])

    op.create_table(
        "drill",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("exercise_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(), nullable=True),
        sa.Column("source_id", sa.Integer(), nullable=True),
        sa.Column("instructions", sa.Text(), nullable=True),
        sa.Column("unit", sa.String(), nullable=True),
        sa.Column("target", sa.Integer(), nullable=True),
        sa.Column("suggested_minutes", sa.Integer(), nullable=True),
        sa.Column("frequency", sa.String(), nullable=True),
        sa.Column("remark", sa.Text(), nullable=True),
        sa.Column("position", sa.Integer(), nullable=False),
        *_timestamps(),
        sa.CheckConstraint("target IS NULL OR target >= 1", name="ck_drill_target_positive"),
        sa.CheckConstraint(
            "suggested_minutes IS NULL OR suggested_minutes >= 1",
            name="ck_drill_suggested_minutes_positive",
        ),
        sa.ForeignKeyConstraint(
            ["exercise_id"], ["exercise.id"], name="drill_exercise_id_fkey", ondelete="RESTRICT"
        ),
        _option_fk("drill", "source_id"),
        sa.PrimaryKeyConstraint("id", name="drill_pkey"),
    )
    op.create_index("ix_drill_exercise_id", "drill", ["exercise_id"])
    op.create_index("ix_drill_source_id", "drill", ["source_id"])

    _link_table("drill_source_link", "drill")
    _link_table("drill_resource", "drill")

    op.create_table(
        "record",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("location_id", sa.Integer(), nullable=True),
        sa.Column("duration_minutes", sa.Integer(), nullable=True),
        sa.Column("drill_id", sa.Integer(), nullable=True),
        sa.Column("exercise_id", sa.Integer(), nullable=True),
        sa.Column("kind", sa.String(), server_default="practice", nullable=False),
        sa.Column("stage_id", sa.Integer(), nullable=True),
        sa.Column("goal_id", sa.Integer(), nullable=True),
        sa.Column("method_id", sa.Integer(), nullable=True),
        sa.Column("tool_id", sa.Integer(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        *_timestamps(),
        sa.CheckConstraint(_in("kind", RECORD_KINDS), name="ck_record_kind"),
        sa.CheckConstraint(
            "num_nonnulls(drill_id, exercise_id) <= 1", name="ck_record_one_activity"
        ),
        sa.CheckConstraint(
            "num_nonnulls(stage_id, goal_id) = CASE WHEN kind = 'test' THEN 1 ELSE 0 END",
            name="ck_record_test_target",
        ),
        sa.CheckConstraint(
            "duration_minutes IS NULL OR duration_minutes >= 0",
            name="ck_record_duration_non_negative",
        ),
        _option_fk("record", "location_id"),
        sa.ForeignKeyConstraint(
            ["drill_id"], ["drill.id"], name="record_drill_id_fkey", ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["exercise_id"], ["exercise.id"], name="record_exercise_id_fkey", ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["stage_id"], ["stage.id"], name="record_stage_id_fkey", ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["goal_id"], ["goal.id"], name="record_goal_id_fkey", ondelete="RESTRICT"
        ),
        _option_fk("record", "method_id"),
        _option_fk("record", "tool_id"),
        sa.PrimaryKeyConstraint("id", name="record_pkey"),
    )
    for column in (
        "date",
        "location_id",
        "drill_id",
        "exercise_id",
        "stage_id",
        "goal_id",
        "method_id",
        "tool_id",
    ):
        op.create_index(f"ix_record_{column}", "record", [column])

    _link_table("record_reference", "record")

    seed(op.get_bind())


def downgrade() -> None:
    """Everything this revision created, children first, then the new
    categories' values - nothing names them once the tables are gone - and
    the old category check back."""
    op.drop_table("record_reference")
    op.drop_table("record")
    op.drop_table("drill_resource")
    op.drop_table("drill_source_link")
    op.drop_table("drill")
    op.drop_table("exercise_topic")
    op.drop_table("exercise_resource")
    op.drop_table("exercise_alias")
    op.drop_table("exercise")

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
