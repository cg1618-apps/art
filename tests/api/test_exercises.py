"""Exercises over HTTP: CRUD with names, aliases, stage, topics and
resources; the list's order, filters and counts; and the refused delete.

Every refusal sets up the thing it refuses and has a mirror that succeeds:
the wrong-category tests use the `options` fixture, which holds an option of
every category, and the delete refusals create the drill or record first.
"""

from tests.api.helpers import (
    create_drill,
    create_exercise,
    create_goal,
    create_record,
    create_stage,
)


def test_an_exercise_round_trips_through_create_read_update_delete(client, options):
    goal = create_goal(client, "L0")
    stage = create_stage(client, goal["id"], name_cn="線條與形狀")
    created = create_exercise(
        client,
        name_cn="線條",
        name_en="Lines",
        name_alt="lines",
        aliases=["直線", "曲線"],
        stage_id=stage["id"],
        topic_ids=[options["topic"].id],
        description="穩定的直線與曲線。",
        remark="用手肘",
        resources=[{"name": "Line of Action", "url": "line-of-action.com"}],
    )
    assert created == {
        "id": created["id"],
        "display_name": "線條",
        "name_cn": "線條",
        "name_en": "Lines",
        "name_alt": "lines",
        "stage": {"id": stage["id"], "number": 0, "display_name": "線條與形狀"},
        "topics": [{"id": options["topic"].id, "value": "透視", "description": "空間的遠近"}],
        "description": "穩定的直線與曲線。",
        "drill_count": 0,
        "record_count": 0,
        "total_minutes": 0,
        "updated_at": created["updated_at"],
        "aliases": sorted(["直線", "曲線"]),
        "remark": "用手肘",
        "resources": [
            {
                "id": created["resources"][0]["id"],
                "name": "Line of Action",
                "url": "https://line-of-action.com",
            }
        ],
        "drills": [],
        "created_at": created["created_at"],
    }
    assert client.get(f"/api/exercises/{created['id']}").json() == created

    updated = client.patch(
        f"/api/exercises/{created['id']}",
        json={"stage_id": None, "aliases": ["直線"], "topic_ids": [], "remark": ""},
    )
    assert updated.status_code == 200, updated.text
    body = updated.json()
    assert (body["stage"], body["aliases"], body["topics"], body["remark"]) == (
        None,
        ["直線"],
        [],
        None,
    )
    assert body["description"] == "穩定的直線與曲線。"  # not sent, untouched
    assert len(body["resources"]) == 1  # not sent, untouched

    assert client.delete(f"/api/exercises/{created['id']}").status_code == 204
    assert client.get(f"/api/exercises/{created['id']}").status_code == 404


def test_an_exercise_needs_a_name(client):
    for body in ({}, {"name_cn": "  "}, {"name_en": "", "description": "x"}):
        response = client.post("/api/exercises", json=body)
        assert response.status_code == 422, (body, response.text)


def test_a_patch_cannot_clear_the_last_name_but_may_clear_one_of_two(client):
    exercise = create_exercise(client, name_cn="線條", name_en=None)
    response = client.patch(f"/api/exercises/{exercise['id']}", json={"name_cn": None})
    assert response.status_code == 422, response.text
    both = create_exercise(client, name_cn="線條", name_en="Lines")
    response = client.patch(f"/api/exercises/{both['id']}", json={"name_cn": None})
    assert response.status_code == 200, response.text
    assert response.json()["display_name"] == "Lines"


def test_a_topic_that_is_a_method_option_is_refused(client, options):
    response = client.post(
        "/api/exercises", json={"name_cn": "線條", "topic_ids": [options["method"].id]}
    )
    assert response.status_code == 422, response.text
    assert "method" in response.json()["detail"]


def test_a_topic_that_is_a_topic_option_is_accepted(client, options):
    """The mirror, with the same fixture."""
    created = create_exercise(client, topic_ids=[options["topic"].id, options["other_topic"].id])
    assert [t["value"] for t in created["topics"]] == ["透視", "人體"]


def test_a_stage_that_does_not_exist_is_422(client):
    response = client.post("/api/exercises", json={"name_cn": "線條", "stage_id": 999999})
    assert response.status_code == 422, response.text


def test_null_for_a_list_is_refused(client):
    exercise = create_exercise(client)
    for field in ("aliases", "topic_ids", "resources"):
        response = client.patch(f"/api/exercises/{exercise['id']}", json={field: None})
        assert response.status_code == 422, (field, response.text)


def test_the_detail_carries_its_drills_in_order_with_names_falling_back(client, options):
    exercise = create_exercise(client, name_cn="人偶")
    second = create_drill(client, exercise["id"], name="骨架五步", position=1)
    first = create_drill(client, exercise["id"], position=0, source_id=options["source"].id)
    drills = client.get(f"/api/exercises/{exercise['id']}").json()["drills"]
    assert [d["id"] for d in drills] == [first["id"], second["id"]]
    assert [d["display_name"] for d in drills] == ["人偶", "骨架五步"]
    assert drills[0]["source"]["value"] == "Character Art School"
    assert drills[0]["exercise"] == {"id": exercise["id"], "display_name": "人偶"}


# --- the list -----------------------------------------------------------------


def _names(client, **params):
    return [e["display_name"] for e in client.get("/api/exercises", params=params).json()]


def test_the_list_is_in_roadmap_order_with_the_unstaged_last(client):
    l0 = create_goal(client, "L0", position=0)
    l1 = create_goal(client, "L1", position=1)
    later = create_stage(client, l1["id"], name_cn="比例")
    earlier = create_stage(client, l0["id"], name_cn="線條與形狀")
    create_exercise(client, name_cn="動態速寫")
    create_exercise(client, name_cn="人偶", stage_id=later["id"])
    create_exercise(client, name_cn="2D 形狀", stage_id=earlier["id"])
    create_exercise(client, name_cn="人體比例", stage_id=later["id"])
    create_exercise(client, name_cn="對照畫")
    assert _names(client) == ["2D 形狀", "人偶", "人體比例", "動態速寫", "對照畫"]

    assert _names(client, stage_id=later["id"]) == ["人偶", "人體比例"]
    assert _names(client, no_stage="true") == ["動態速寫", "對照畫"]


def test_search_matches_names_aliases_and_description(client):
    create_exercise(client, name_cn="線條", aliases=["warm-up"])
    create_exercise(client, name_cn="手", description="手的比例與結構")
    create_exercise(client, name_cn="頭部", name_en="Head")
    assert _names(client, q="WARM") == ["線條"]
    assert _names(client, q="比例") == ["手"]
    assert _names(client, q="head") == ["頭部"]
    assert _names(client, q="%") == []


def test_the_topic_filter_means_any_of(client, options):
    create_exercise(client, name_cn="透視方塊", topic_ids=[options["topic"].id])
    create_exercise(client, name_cn="人偶", topic_ids=[options["other_topic"].id])
    create_exercise(client, name_cn="線條")
    assert _names(client, topic_id=[options["topic"].id]) == ["透視方塊"]
    assert _names(client, topic_id=[options["topic"].id, options["other_topic"].id]) == [
        "人偶",
        "透視方塊",
    ]


def test_counts_include_records_naming_it_directly_or_through_a_drill(client):
    exercise = create_exercise(client, name_cn="線條")
    other = create_exercise(client, name_cn="手")
    drill = create_drill(client, exercise["id"], name="基本線條")
    create_drill(client, exercise["id"], name="綜合線條")
    create_record(client, exercise_id=exercise["id"], duration_minutes=10)
    create_record(client, drill_id=drill["id"], duration_minutes=15)
    create_record(client, drill_id=drill["id"])  # no duration: a record, zero minutes
    create_record(client, exercise_id=other["id"], duration_minutes=99)

    listed = {e["id"]: e for e in client.get("/api/exercises").json()}
    assert (
        listed[exercise["id"]]["drill_count"],
        listed[exercise["id"]]["record_count"],
        listed[exercise["id"]]["total_minutes"],
    ) == (2, 3, 25)
    assert (listed[other["id"]]["record_count"], listed[other["id"]]["total_minutes"]) == (1, 99)

    detail = client.get(f"/api/exercises/{exercise['id']}").json()
    assert (detail["drill_count"], detail["record_count"], detail["total_minutes"]) == (2, 3, 25)


# --- delete -------------------------------------------------------------------


def test_an_exercise_with_drills_is_not_deleted(client):
    exercise = create_exercise(client)
    drill = create_drill(client, exercise["id"])
    response = client.delete(f"/api/exercises/{exercise['id']}")
    assert response.status_code == 409, response.text
    body = response.json()
    assert (body["drills"], body["records"]) == (1, 0)
    assert body["detail"]

    # The mirror, on the same exercise: the drill removed, the delete goes.
    assert client.delete(f"/api/drills/{drill['id']}").status_code == 204
    assert client.delete(f"/api/exercises/{exercise['id']}").status_code == 204


def test_an_exercise_named_by_a_record_is_not_deleted(client):
    exercise = create_exercise(client)
    record = create_record(client, exercise_id=exercise["id"])
    response = client.delete(f"/api/exercises/{exercise['id']}")
    assert response.status_code == 409, response.text
    assert (response.json()["drills"], response.json()["records"]) == (0, 1)
    assert client.get(f"/api/exercises/{exercise['id']}").status_code == 200

    assert client.delete(f"/api/records/{record['id']}").status_code == 204
    assert client.delete(f"/api/exercises/{exercise['id']}").status_code == 204


def test_deleting_its_stage_leaves_the_exercise_with_no_stage(client):
    goal = create_goal(client)
    stage = create_stage(client, goal["id"])
    exercise = create_exercise(client, stage_id=stage["id"])
    assert exercise["stage"]["id"] == stage["id"]

    assert client.delete(f"/api/stages/{stage['id']}").status_code == 204
    after = client.get(f"/api/exercises/{exercise['id']}")
    assert after.status_code == 200, after.text
    assert after.json()["stage"] is None


def test_a_missing_exercise_is_404(client):
    assert client.get("/api/exercises/999999").status_code == 404
    assert client.patch("/api/exercises/999999", json={"remark": "x"}).status_code == 404
    assert client.delete("/api/exercises/999999").status_code == 404
