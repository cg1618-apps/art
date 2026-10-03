"""The closed vocabularies this application is exhaustive over.

Tier 1 of the three option tiers: a list lives here when code branches on its
exact value, and changing it is a code change. The open vocabularies the owner
edits - a note category, a topic, a method - are tier 2, `system_option` rows
managed on the Options page; the categories those rows are filed under are
tier 1 and so are registered here.

`StrEnum` so a member compares equal to its stored text and a pydantic schema
can use the same class to produce a 422 before the constraint is reached - the
shape `travel` uses.
"""

from dataclasses import dataclass
from enum import StrEnum


class Visibility(StrEnum):
    """Reserved. Nothing reads this yet.

    It ships from the first migration because retrofitting the *checks* at
    every read path is the expensive part, not the column. When sharing is
    built, the flip from Cloudflare Access to public moves the gate from the
    edge into this codebase, and these checks have to work - and be tested for
    refusal - before that lands.
    """

    PRIVATE = "private"
    UNLISTED = "unlisted"
    PUBLIC = "public"


class GoalStatus(StrEnum):
    """Where a level stands. Set by hand: nothing derives it from the stages,
    so a level can be passed on its test before every stage is ticked."""

    PLANNED = "planned"
    ACTIVE = "active"
    ACHIEVED = "achieved"


class StageStatus(StrEnum):
    """Where a stage stands. `passed` is the only status that may carry a
    date (`ck_stage_passed_on_iff_passed`)."""

    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    PASSED = "passed"


class RecordKind(StrEnum):
    """What a record is (練習 / 作品 / 測驗). `test` is the only kind that
    names a stage or a level (`ck_record_test_target`)."""

    PRACTICE = "practice"
    PIECE = "piece"
    TEST = "test"


@dataclass(frozen=True)
class OptionCategory:
    """One category of `system_option` rows.

    Registered in code rather than accepted as free text, as `media` does:
    every category is read by some field, so one nobody reads is a typo, and
    each needs a label and a description of its own for the Options page.
    """

    key: str  # stored in system_option.category
    label: str  # what the Options page heads the section with
    description: str  # shown above the category's values on the Options page


NOTE_CATEGORY = "note_category"
TOPIC = "topic"
METHOD = "method"
SOURCE = "source"
LOCATION = "location"
TOOL = "tool"

#: In the order the Options page shows them. A key here is the only thing
#: `ck_system_option_category` accepts, so removing one is a migration.
OPTION_CATEGORIES: dict[str, OptionCategory] = {
    c.key: c
    for c in (
        OptionCategory(
            key=NOTE_CATEGORY,
            label="筆記分類",
            description="一則筆記是哪一種知識：名詞、知識、小技巧或建議。每則筆記最多一個，可以不填。",
        ),
        OptionCategory(
            key=TOPIC,
            label="主題",
            description="筆記或練習項目談的是畫畫的哪個面向，例如透視、人體、光影。可以有多個主題。",
        ),
        OptionCategory(
            key=METHOD,
            label="方法",
            description="一次練習是怎麼畫的：臨摹、描寫、速寫、創作等。由練習紀錄使用。",
        ),
        OptionCategory(
            key=SOURCE,
            label="來源",
            description="一個練法出自哪裡：哪一門課，或是自己訂的。每個練法最多一個，可以不填。",
        ),
        OptionCategory(
            key=LOCATION,
            label="地點",
            description="一次練習是在哪裡畫的。由練習紀錄使用，可以不填。",
        ),
        OptionCategory(
            key=TOOL,
            label="工具",
            description="一次練習用什麼畫的：哪個軟體，或是紙筆。由練習紀錄使用，可以不填。",
        ),
    )
}
