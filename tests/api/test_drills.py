"""Drills over HTTP: CRUD with source, source links and resources, the name
falling back to the exercise's, the positive-number rules, moving between
exercises, the refused delete; and the list's order, filters and counts.

Every refusal has a mirror that succeeds against the same setup. Every filter
test makes a row the filter must leave out, so a filter that did nothing would
fail.
"""

from tests.api.helpers import (
    create_drill,
    create_exercise,
    create_goal,
    create_record,
    create_stage,
)


def test_a_drill_round_trips_through_create_read_update_delete(client, options):
    exercise = create_exercise(client, name_cn="人偶", name_en="Mannequin")
    created = create_drill(
        client,
        exercise["id"],
        name="骨架五步",
        source_id=options["source"].id,
        source_links=[{"name": "作業表", "url": "https://example.com/sheet"}],
        resources=[{"name": "Line of Action", "url": "line-of-action.com"}],
        instructions="1. 動態線。2. 火柴人。",
        unit="張",
        target=1,
        suggested_minutes=10,
        frequency="每天",
        remark="先暖身",
    )
    assert created == {
        "id": created["id"],
        "exercise": {"id": exercise["id"], "display_name": "人偶"},
        "display_name": "骨架五步",
        "name": "骨架五步",
        "source": {
            "id": options["source"].id,
            "value": "Character Art School",
            "description": None,
        },
        "source_links": [
            {
                "id": created["source_links"][0]["id"],
                "name": "作業表",
                "url": "https://example.com/sheet",
            }
        ],
        "resources": [
            {
                "id": created["resources"][0]["id"],
                "name": "Line of Action",
                "url": "https://line-of-action.com",
            }
        ],
        "instructions": "1. 動態線。2. 火柴人。",
        "unit": "張",
        "target": 1,
        "suggested_minutes": 10,
        "frequency": "每天",
        "remark": "先暖身",
        "position": 0,
        "created_at": created["created_at"],
        "updated_at": created["updated_at"],
    }
    assert client.get(f"/api/drills/{created['id']}").json() == created

    updated = client.patch(
        f"/api/drills/{created['id']}",
        json={"name": "", "source_id": None, "source_links": [], "target": None},
    )
    assert updated.status_code == 200, updated.text
    body = updated.json()
    assert (body["name"], body["display_name"]) == (None, "人偶")  # falls back
    assert (body["source"], body["source_links"], body["target"]) == (None, [], None)
    assert len(body["resources"]) == 1  # not sent, untouched

    assert client.delete(f"/api/drills/{created['id']}").status_code == 204
    assert client.get(f"/api/drills/{created['id']}").status_code == 404


def test_a_source_that_is_a_tool_option_is_refused(client, options):
    exercise = create_exercise(client)
    response = client.post(
        "/api/drills", json={"exercise_id": exercise["id"], "source_id": options["tool"].id}
    )
    assert response.status_code == 422, response.text
    assert "tool" in response.json()["detail"]
    drill = create_drill(client, exercise["id"])
    patched = client.patch(f"/api/drills/{drill['id']}", json={"source_id": options["tool"].id})
    assert patched.status_code == 422, patched.text


def test_a_source_that_is_a_source_option_is_accepted(client, options):
    """The mirror, with the same fixture."""
    exercise = create_exercise(client)
    drill = create_drill(client, exercise["id"], source_id=options["source"].id)
    assert drill["source"]["id"] == options["source"].id


def test_target_and_suggested_minutes_are_at_least_one(client):
    exercise = create_exercise(client)
    for field in ("target", "suggested_minutes"):
        for value in (0, -1):
            response = client.post(
                "/api/drills", json={"exercise_id": exercise["id"], field: value}
            )
            assert response.status_code == 422, (field, value, response.text)
        assert create_drill(client, exercise["id"], **{field: 1})[field] == 1


def test_an_exercise_that_does_not_exist_is_422(client):
    response = client.post("/api/drills", json={"exercise_id": 999999})
    assert response.status_code == 422, response.text


def test_exercise_and_position_cannot_be_cleared(client):
    exercise = create_exercise(client)
    drill = create_drill(client, exercise["id"])
    for body in ({"exercise_id": None}, {"position": None}):
        response = client.patch(f"/api/drills/{drill['id']}", json=body)
        assert response.status_code == 422, (body, response.text)


def test_a_new_drill_goes_last_and_a_moved_one_goes_last_in_its_new_exercise(client):
    one = create_exercise(client, name_cn="線條")
    two = create_exercise(client, name_cn="形狀")
    first = create_drill(client, one["id"], name="a")
    second = create_drill(client, one["id"], name="b")
    there = create_drill(client, two["id"], name="c")
    assert (first["position"], second["position"], there["position"]) == (0, 1, 0)

    moved = client.patch(f"/api/drills/{first['id']}", json={"exercise_id": two["id"]})
    assert moved.status_code == 200, moved.text
    assert moved.json()["position"] == 1
    assert moved.json()["exercise"] == {"id": two["id"], "display_name": "形狀"}


def test_a_drill_named_by_a_record_is_not_deleted(client):
    exercise = create_exercise(client)
    drill = create_drill(client, exercise["id"])
    record = create_record(client, drill_id=drill["id"])
    response = client.delete(f"/api/drills/{drill['id']}")
    assert response.status_code == 409, response.text
    assert response.json()["records"] == 1
    assert response.json()["detail"]
    assert client.get(f"/api/drills/{drill['id']}").status_code == 200

    # The mirror: the record gone, the delete goes.
    assert client.delete(f"/api/records/{record['id']}").status_code == 204
    assert client.delete(f"/api/drills/{drill['id']}").status_code == 204


def test_a_missing_drill_is_404(client):
    assert client.get("/api/drills/999999").status_code == 404
    assert client.patch("/api/drills/999999", json={"name": "x"}).status_code == 404
    assert client.delete("/api/drills/999999").status_code == 404


# --- the list -----------------------------------------------------------------


def _names(client, **params):
    response = client.get("/api/drills", params=params)
    assert response.status_code == 200, response.text
    return [d["display_name"] for d in response.json()]


def test_the_list_is_in_roadmap_order_then_by_position(client):
    l0 = create_goal(client, "L0", position=0)
    l1 = create_goal(client, "L1", position=1)
    later = create_stage(client, l1["id"], name_cn="比例")
    earlier = create_stage(client, l0["id"], name_cn="線條與形狀")
    gesture = create_exercise(client, name_cn="動態速寫")
    mannequin = create_exercise(client, name_cn="人偶", stage_id=later["id"])
    shapes = create_exercise(client, name_cn="2D 形狀", stage_id=earlier["id"])
    create_drill(client, gesture["id"], name="三十秒")
    create_drill(client, mannequin["id"], name="骨架五步", position=1)
    create_drill(client, mannequin["id"], name="盒子人", position=0)
    create_drill(client, shapes["id"])  # no name: falls back to the exercise's
    assert _names(client) == ["2D 形狀", "盒子人", "骨架五步", "三十秒"]


def test_the_summary_carries_its_exercise_stage_and_topics(client, options):
    goal = create_goal(client)
    stage = create_stage(client, goal["id"], name_cn="線條與形狀")
    exercise = create_exercise(
        client, name_cn="線條", stage_id=stage["id"], topic_ids=[options["topic"].id]
    )
    drill = create_drill(
        client,
        exercise["id"],
        name="基本線條",
        source_id=options["source"].id,
        instructions="畫滿一頁",
        unit="頁",
        target=2,
        suggested_minutes=15,
        frequency="每天",
    )
    assert client.get("/api/drills").json() == [
        {
            "id": drill["id"],
            "display_name": "基本線條",
            "name": "基本線條",
            "exercise": {"id": exercise["id"], "display_name": "線條"},
            "stage": {"id": stage["id"], "number": 0, "display_name": "線條與形狀"},
            "topics": [{"id": options["topic"].id, "value": "透視", "description": "空間的遠近"}],
            "source": {
                "id": options["source"].id,
                "value": "Character Art School",
                "description": None,
            },
            "unit": "頁",
            "target": 2,
            "suggested_minutes": 15,
            "frequency": "每天",
            "record_count": 0,
            "total_minutes": 0,
            "updated_at": drill["updated_at"],
        }
    ]


def test_search_matches_the_drill_name_its_instructions_and_its_exercise(client):
    lines = create_exercise(client, name_cn="線條", aliases=["warm-up"])
    hands = create_exercise(client, name_cn="手", name_en="Hands")
    create_drill(client, lines["id"], name="基本線條")
    create_drill(client, hands["id"], name="手勢", instructions="畫二十個比例草圖")
    create_drill(client, hands["id"], name="骨架")
    assert _names(client, q="基本") == ["基本線條"]
    assert _names(client, q="比例") == ["手勢"]
    assert _names(client, q="WARM") == ["基本線條"]
    assert _names(client, q="hands") == ["手勢", "骨架"]
    assert _names(client, q="%") == []


def test_the_exercise_filter_means_any_of(client):
    one = create_exercise(client, name_cn="線條")
    two = create_exercise(client, name_cn="形狀")
    three = create_exercise(client, name_cn="手")
    create_drill(client, one["id"], name="a")
    create_drill(client, two["id"], name="b")
    create_drill(client, three["id"], name="c")
    assert _names(client, exercise_id=[one["id"]]) == ["a"]
    assert _names(client, exercise_id=[one["id"], two["id"]]) == ["b", "a"]


def test_the_stage_filters_go_through_the_exercise(client):
    goal = create_goal(client)
    stage = create_stage(client, goal["id"], name_cn="線條與形狀")
    other = create_stage(client, goal["id"], name_cn="比例")
    staged = create_exercise(client, name_cn="線條", stage_id=stage["id"])
    elsewhere = create_exercise(client, name_cn="人偶", stage_id=other["id"])
    unstaged = create_exercise(client, name_cn="動態速寫")
    create_drill(client, staged["id"], name="a")
    create_drill(client, elsewhere["id"], name="b")
    create_drill(client, unstaged["id"], name="c")
    assert _names(client, stage_id=[stage["id"]]) == ["a"]
    assert _names(client, stage_id=[stage["id"], other["id"]]) == ["a", "b"]
    assert _names(client, no_stage="true") == ["c"]


def test_the_topic_filter_goes_through_the_exercise(client, options):
    perspective = create_exercise(client, name_cn="透視方塊", topic_ids=[options["topic"].id])
    body = create_exercise(client, name_cn="人偶", topic_ids=[options["other_topic"].id])
    plain = create_exercise(client, name_cn="線條")
    create_drill(client, perspective["id"], name="a")
    create_drill(client, body["id"], name="b")
    create_drill(client, plain["id"], name="c")
    assert _names(client, topic_id=[options["topic"].id]) == ["a"]
    assert _names(client, topic_id=[options["topic"].id, options["other_topic"].id]) == [
        "b",
        "a",
    ]


def test_the_source_filter_leaves_out_other_sources_and_none(client, make_option):
    school = make_option("source", "Character Art School")
    book = make_option("source", "Figure Drawing")
    exercise = create_exercise(client)
    create_drill(client, exercise["id"], name="a", source_id=school.id)
    create_drill(client, exercise["id"], name="b", source_id=book.id)
    create_drill(client, exercise["id"], name="c")
    assert _names(client, source_id=[school.id]) == ["a"]
    assert _names(client, source_id=[school.id, book.id]) == ["a", "b"]


def test_filters_narrow_each_other(client, options):
    topical = create_exercise(client, name_cn="透視方塊", topic_ids=[options["topic"].id])
    plain = create_exercise(client, name_cn="線條")
    create_drill(client, topical["id"], name="a", source_id=options["source"].id)
    create_drill(client, topical["id"], name="b")
    create_drill(client, plain["id"], name="c", source_id=options["source"].id)
    assert _names(client, topic_id=[options["topic"].id], source_id=[options["source"].id]) == ["a"]


def test_counts_are_the_records_naming_the_drill(client):
    exercise = create_exercise(client)
    drill = create_drill(client, exercise["id"], name="a")
    other = create_drill(client, exercise["id"], name="b")
    create_record(client, drill_id=drill["id"], duration_minutes=15)
    create_record(client, drill_id=drill["id"])  # no duration: a record, zero minutes
    create_record(client, drill_id=other["id"], duration_minutes=40)
    # Names the exercise, not a drill: counted on neither.
    create_record(client, exercise_id=exercise["id"], duration_minutes=99)

    listed = {d["id"]: d for d in client.get("/api/drills").json()}
    assert (listed[drill["id"]]["record_count"], listed[drill["id"]]["total_minutes"]) == (2, 15)
    assert (listed[other["id"]]["record_count"], listed[other["id"]]["total_minutes"]) == (1, 40)
