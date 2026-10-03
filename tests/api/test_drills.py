"""Drills over HTTP: CRUD with source, source links and resources, the name
falling back to the exercise's, the positive-number rules, moving between
exercises, and the refused delete.

Every refusal has a mirror that succeeds against the same setup.
"""

from tests.api.helpers import create_drill, create_exercise, create_record


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
