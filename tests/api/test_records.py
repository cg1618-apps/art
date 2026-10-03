"""Records over HTTP: CRUD, the activity, the one-activity and test-target
rules, the option categories, the list's filters and order, and the per-day
summary.

Every refusal has a mirror that succeeds against the same setup. The
wrong-category tests use the `options` fixture, which holds an option of
every category, so a check that never looked at the category cannot pass.
"""

import datetime as dt

import pytest
from sqlalchemy.exc import IntegrityError

from tests.api.helpers import (
    create_drill,
    create_exercise,
    create_goal,
    create_record,
    create_stage,
)


@pytest.fixture
def practice(client):
    """An exercise with one drill: the two things a record can name."""
    exercise = create_exercise(client, name_cn="人偶")
    drill = create_drill(client, exercise["id"], name="骨架五步")
    return {"exercise": exercise, "drill": drill}


@pytest.fixture
def roadmap(client):
    goal = create_goal(client, "L1", name_cn="人體")
    stage = create_stage(client, goal["id"], name_cn="比例")
    return {"goal": goal, "stage": stage}


def test_a_record_round_trips_through_create_read_update_delete(client, options, practice):
    created = create_record(
        client,
        date="2026-10-01",
        location_id=options["location"].id,
        duration_minutes=25,
        drill_id=practice["drill"]["id"],
        method_id=options["other_method"].id,
        tool_id=options["tool"].id,
        references=[{"name": "Pinterest", "url": "pinterest.com/pin/1"}],
        notes="手腕太僵",
    )
    assert created == {
        "id": created["id"],
        "date": "2026-10-01",
        "kind": "practice",
        "activity": {
            "exercise": {"id": practice["exercise"]["id"], "display_name": "人偶"},
            "drill": {"id": practice["drill"]["id"], "display_name": "骨架五步"},
        },
        "stage": None,
        "goal": None,
        "location": {"id": options["location"].id, "value": "台灣・家", "description": None},
        "duration_minutes": 25,
        "method": {
            "id": options["other_method"].id,
            "value": "描寫",
            "description": "看著參考圖畫",
        },
        "tool": {"id": options["tool"].id, "value": "Clip Studio Paint", "description": None},
        "references": [
            {
                "id": created["references"][0]["id"],
                "name": "Pinterest",
                "url": "https://pinterest.com/pin/1",
            }
        ],
        "notes": "手腕太僵",
        "created_at": created["created_at"],
        "updated_at": created["updated_at"],
    }
    assert client.get(f"/api/records/{created['id']}").json() == created

    updated = client.patch(
        f"/api/records/{created['id']}",
        json={
            "drill_id": None,
            "exercise_id": practice["exercise"]["id"],
            "duration_minutes": None,
            "tool_id": None,
            "notes": "",
        },
    )
    assert updated.status_code == 200, updated.text
    body = updated.json()
    assert body["activity"] == {
        "exercise": {"id": practice["exercise"]["id"], "display_name": "人偶"},
        "drill": None,
    }
    assert (body["duration_minutes"], body["tool"], body["notes"]) == (None, None, None)
    assert body["location"]["id"] == options["location"].id  # not sent, untouched
    assert len(body["references"]) == 1  # not sent, untouched

    assert client.delete(f"/api/records/{created['id']}").status_code == 204
    assert client.get(f"/api/records/{created['id']}").status_code == 404


def test_a_record_may_name_neither_a_drill_nor_an_exercise(client):
    record = create_record(client)
    assert record["activity"] is None
    assert record["kind"] == "practice"


def test_a_drill_with_no_name_shows_its_exercises(client, practice):
    unnamed = create_drill(client, practice["exercise"]["id"])
    record = create_record(client, drill_id=unnamed["id"])
    assert record["activity"]["drill"] == {"id": unnamed["id"], "display_name": "人偶"}


# --- one activity -------------------------------------------------------------


def test_a_drill_and_an_exercise_on_one_record_is_422(client, practice):
    response = client.post(
        "/api/records",
        json={
            "date": "2026-10-03",
            "drill_id": practice["drill"]["id"],
            "exercise_id": practice["exercise"]["id"],
        },
    )
    assert response.status_code == 422, response.text
    # The mirror: either one alone is fine.
    create_record(client, drill_id=practice["drill"]["id"])
    create_record(client, exercise_id=practice["exercise"]["id"])


def test_a_patch_adding_a_drill_to_a_record_with_an_exercise_is_422(client, practice):
    record = create_record(client, exercise_id=practice["exercise"]["id"])
    response = client.patch(
        f"/api/records/{record['id']}", json={"drill_id": practice["drill"]["id"]}
    )
    assert response.status_code == 422, response.text
    # The mirror: switching, with the exercise cleared in the same save.
    response = client.patch(
        f"/api/records/{record['id']}",
        json={"drill_id": practice["drill"]["id"], "exercise_id": None},
    )
    assert response.status_code == 200, response.text


def test_the_database_refuses_both_too(db, practice):
    from app.models import Record

    db.add(
        Record(
            date=dt.date(2026, 10, 3),
            drill_id=practice["drill"]["id"],
            exercise_id=practice["exercise"]["id"],
        )
    )
    with pytest.raises(IntegrityError):
        db.flush()


def test_unknown_drill_exercise_stage_or_goal_ids_are_422(client):
    for body in (
        {"drill_id": 999999},
        {"exercise_id": 999999},
        {"kind": "test", "stage_id": 999999},
        {"kind": "test", "goal_id": 999999},
    ):
        response = client.post("/api/records", json={"date": "2026-10-03", **body})
        assert response.status_code == 422, (body, response.text)


# --- test target --------------------------------------------------------------


def test_a_test_needs_exactly_one_of_stage_and_goal(client, roadmap):
    for extra in ({}, {"stage_id": roadmap["stage"]["id"], "goal_id": roadmap["goal"]["id"]}):
        response = client.post(
            "/api/records", json={"date": "2026-10-03", "kind": "test", **extra}
        )
        assert response.status_code == 422, (extra, response.text)

    # The mirrors: one or the other.
    of_stage = create_record(client, kind="test", stage_id=roadmap["stage"]["id"])
    assert of_stage["stage"] == {
        "id": roadmap["stage"]["id"],
        "number": 0,
        "display_name": "比例",
    }
    assert of_stage["goal"] is None
    of_goal = create_record(client, kind="test", goal_id=roadmap["goal"]["id"])
    assert of_goal["goal"] == {
        "id": roadmap["goal"]["id"],
        "code": "L1",
        "display_name": "人體",
    }


def test_a_stage_or_goal_on_a_record_that_is_not_a_test_is_422(client, roadmap):
    for kind in ("practice", "piece"):
        for extra in ({"stage_id": roadmap["stage"]["id"]}, {"goal_id": roadmap["goal"]["id"]}):
            response = client.post(
                "/api/records", json={"date": "2026-10-03", "kind": kind, **extra}
            )
            assert response.status_code == 422, (kind, extra, response.text)
        # The mirror: the same kind with neither.
        create_record(client, kind=kind)


def test_the_database_refuses_both_on_a_record_that_is_not_a_test(db, roadmap):
    """`(kind = 'test') = (count = 1)` would let this through; the check
    must not."""
    from app.models import Record

    db.add(
        Record(
            date=dt.date(2026, 10, 3),
            kind="practice",
            stage_id=roadmap["stage"]["id"],
            goal_id=roadmap["goal"]["id"],
        )
    )
    with pytest.raises(IntegrityError):
        db.flush()


def test_setting_kind_away_from_test_clears_the_target(client, roadmap):
    record = create_record(client, kind="test", stage_id=roadmap["stage"]["id"])
    response = client.patch(f"/api/records/{record['id']}", json={"kind": "piece"})
    assert response.status_code == 200, response.text
    assert (response.json()["kind"], response.json()["stage"]) == ("piece", None)

    # But sending a target with a kind that cannot carry one is refused.
    response = client.patch(
        f"/api/records/{record['id']}",
        json={"kind": "practice", "goal_id": roadmap["goal"]["id"]},
    )
    assert response.status_code == 422, response.text


def test_a_test_record_restricts_its_stage_and_goal(client, roadmap):
    """The stage and goal deletes are refused with the count, and go once the
    record is gone."""
    stage_test = create_record(client, kind="test", stage_id=roadmap["stage"]["id"])
    response = client.delete(f"/api/stages/{roadmap['stage']['id']}")
    assert response.status_code == 409, response.text
    assert response.json()["records"] == 1
    assert client.delete(f"/api/records/{stage_test['id']}").status_code == 204
    assert client.delete(f"/api/stages/{roadmap['stage']['id']}").status_code == 204

    goal_test = create_record(client, kind="test", goal_id=roadmap["goal"]["id"])
    response = client.delete(f"/api/goals/{roadmap['goal']['id']}")
    assert response.status_code == 409, response.text
    assert response.json()["records"] == 1
    assert client.delete(f"/api/records/{goal_test['id']}").status_code == 204
    assert client.delete(f"/api/goals/{roadmap['goal']['id']}").status_code == 204


# --- option categories --------------------------------------------------------


@pytest.mark.parametrize(
    ("field", "wrong", "right"),
    [
        ("location_id", "tool", "location"),
        ("method_id", "location", "method"),
        ("tool_id", "method", "tool"),
    ],
)
def test_each_option_field_takes_only_its_own_category(client, options, field, wrong, right):
    response = client.post(
        "/api/records", json={"date": "2026-10-03", field: options[wrong].id}
    )
    assert response.status_code == 422, response.text
    assert wrong in response.json()["detail"]

    record = create_record(client, **{field: options[right].id})
    patched = client.patch(f"/api/records/{record['id']}", json={field: options[wrong].id})
    assert patched.status_code == 422, patched.text
    assert client.get(f"/api/records/{record['id']}").json()[field[:-3]]["id"] == options[right].id


# --- other rules --------------------------------------------------------------


def test_a_negative_duration_is_refused_and_zero_is_not(client):
    response = client.post("/api/records", json={"date": "2026-10-03", "duration_minutes": -1})
    assert response.status_code == 422, response.text
    assert create_record(client, duration_minutes=0)["duration_minutes"] == 0


def test_date_and_kind_cannot_be_cleared_and_date_is_required(client):
    assert client.post("/api/records", json={}).status_code == 422
    record = create_record(client)
    for body in ({"date": None}, {"kind": None}, {"references": None}):
        response = client.patch(f"/api/records/{record['id']}", json=body)
        assert response.status_code == 422, (body, response.text)


def test_an_unknown_kind_is_refused(client):
    response = client.post("/api/records", json={"date": "2026-10-03", "kind": "study"})
    assert response.status_code == 422, response.text


# --- the list -----------------------------------------------------------------


def test_the_list_is_newest_first(client):
    older = create_record(client, date="2026-10-01")
    newer = create_record(client, date="2026-10-03")
    same_day_later = create_record(client, date="2026-10-03")
    ids = [r["id"] for r in client.get("/api/records").json()]
    assert ids == [same_day_later["id"], newer["id"], older["id"]]


def test_exercise_id_matches_records_naming_it_directly_and_through_its_drills(
    client, practice
):
    direct = create_record(client, exercise_id=practice["exercise"]["id"])
    through = create_record(client, drill_id=practice["drill"]["id"])
    other = create_exercise(client, name_cn="手")
    create_record(client, exercise_id=other["id"])
    create_record(client)

    ids = {
        r["id"]
        for r in client.get(
            "/api/records", params={"exercise_id": practice["exercise"]["id"]}
        ).json()
    }
    assert ids == {direct["id"], through["id"]}

    by_drill = client.get("/api/records", params={"drill_id": practice["drill"]["id"]}).json()
    assert [r["id"] for r in by_drill] == [through["id"]]


def test_the_list_filters_by_date_range_kind_stage_and_goal(client, roadmap):
    early = create_record(client, date="2026-09-30")
    inside = create_record(client, date="2026-10-01", kind="piece")
    last_day = create_record(client, date="2026-10-02", kind="test", stage_id=roadmap["stage"]["id"])
    goal_test = create_record(client, date="2026-10-05", kind="test", goal_id=roadmap["goal"]["id"])

    def ids(**params):
        return [r["id"] for r in client.get("/api/records", params=params).json()]

    assert ids(**{"from": "2026-10-01", "to": "2026-10-02"}) == [last_day["id"], inside["id"]]
    assert ids(**{"to": "2026-09-30"}) == [early["id"]]
    assert ids(kind="piece") == [inside["id"]]
    assert ids(kind="test") == [goal_test["id"], last_day["id"]]
    assert ids(stage_id=roadmap["stage"]["id"], kind="test") == [last_day["id"]]
    assert ids(goal_id=roadmap["goal"]["id"]) == [goal_test["id"]]


# --- summary ------------------------------------------------------------------


def test_the_summary_sums_minutes_per_day_counting_a_record_with_no_duration(client):
    create_record(client, date="2026-10-01", duration_minutes=10)
    create_record(client, date="2026-10-01", duration_minutes=15)
    create_record(client, date="2026-10-01")  # a record, zero minutes
    create_record(client, date="2026-10-02")
    create_record(client, date="2026-10-04", duration_minutes=30)

    response = client.get("/api/records/summary")
    assert response.status_code == 200, response.text
    assert response.json() == [
        {"date": "2026-10-01", "minutes": 25, "records": 3},
        {"date": "2026-10-02", "minutes": 0, "records": 1},
        {"date": "2026-10-04", "minutes": 30, "records": 1},
    ]
    ranged = client.get("/api/records/summary", params={"from": "2026-10-02", "to": "2026-10-04"})
    assert [d["date"] for d in ranged.json()] == ["2026-10-02", "2026-10-04"]


def test_a_missing_record_is_404(client):
    assert client.get("/api/records/999999").status_code == 404
    assert client.patch("/api/records/999999", json={"notes": "x"}).status_code == 404
    assert client.delete("/api/records/999999").status_code == 404
