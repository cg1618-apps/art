"""Goals over HTTP: CRUD, the name and code rules, the date-iff-status rule,
and the refused delete of a goal that still has stages.

Every refusal sets up the thing it refuses and has a mirror that succeeds. The
delete refusal in particular creates a stage first: a test database holds no
stages, and a "goal with stages is refused" check over an empty table would
pass without ever firing.
"""


def create_goal(client, **body):
    body.setdefault("code", "L0")
    body.setdefault("name_cn", "基礎")
    response = client.post("/api/goals", json=body)
    assert response.status_code == 201, response.text
    return response.json()


def create_stage(client, goal_id, **body):
    body.setdefault("name_cn", "線條")
    response = client.post("/api/stages", json={"goal_id": goal_id, **body})
    assert response.status_code == 201, response.text
    return response.json()


def test_a_goal_round_trips_through_create_read_update_delete(client):
    created = create_goal(
        client,
        code=" L0 ",
        name_cn="基礎",
        name_en="Foundations",
        name_alt="F",
        description="能穩定地畫出線條。",
        test="一頁穩定的線條。",
        status="active",
        remark="每天十分鐘",
    )
    assert created == {
        "id": created["id"],
        "code": "L0",
        "display_name": "基礎",
        "name_cn": "基礎",
        "name_en": "Foundations",
        "name_alt": "F",
        "position": 0,
        "description": "能穩定地畫出線條。",
        "test": "一頁穩定的線條。",
        "status": "active",
        "achieved_on": None,
        "remark": "每天十分鐘",
        "stages": [],
    }
    assert client.get(f"/api/goals/{created['id']}").json() == created
    assert client.get("/api/goals").json() == [created]

    updated = client.patch(
        f"/api/goals/{created['id']}", json={"name_en": "Basics", "remark": ""}
    )
    assert updated.status_code == 200, updated.text
    body = updated.json()
    assert (body["name_en"], body["remark"]) == ("Basics", None)
    assert body["description"] == "能穩定地畫出線條。"  # not sent, untouched

    assert client.delete(f"/api/goals/{created['id']}").status_code == 204
    assert client.get(f"/api/goals/{created['id']}").status_code == 404


def test_a_new_goal_goes_last_unless_placed(client):
    first = create_goal(client, code="L0")
    second = create_goal(client, code="L1")
    placed = create_goal(client, code="L-1", position=-1)
    assert (first["position"], second["position"], placed["position"]) == (0, 1, -1)
    assert [g["code"] for g in client.get("/api/goals").json()] == ["L-1", "L0", "L1"]


def test_a_goal_needs_a_name(client):
    for body in ({"code": "L0"}, {"code": "L0", "name_cn": "  "}):
        response = client.post("/api/goals", json=body)
        assert response.status_code == 422, (body, response.text)


def test_a_patch_cannot_clear_the_last_name(client):
    goal = create_goal(client, name_cn="基礎", name_en=None)
    response = client.patch(f"/api/goals/{goal['id']}", json={"name_cn": None})
    assert response.status_code == 422, response.text
    # The mirror: clearing one name while another remains is fine.
    response = client.patch(
        f"/api/goals/{goal['id']}", json={"name_cn": None, "name_en": "Foundations"}
    )
    assert response.status_code == 200, response.text
    assert response.json()["display_name"] == "Foundations"


def test_a_goal_needs_a_code(client):
    for body in ({"name_cn": "x"}, {"name_cn": "x", "code": "  "}, {"name_cn": "x", "code": None}):
        response = client.post("/api/goals", json=body)
        assert response.status_code == 422, (body, response.text)
    goal = create_goal(client)
    assert client.patch(f"/api/goals/{goal['id']}", json={"code": None}).status_code == 422


def test_a_duplicate_code_is_409_and_a_different_one_is_not(client):
    goal = create_goal(client, code="L0")
    duplicate = client.post("/api/goals", json={"code": " L0 ", "name_cn": "x"})
    assert duplicate.status_code == 409, duplicate.text
    assert duplicate.json()["detail"]
    # The mirror: another code is accepted.
    other = create_goal(client, code="L1")

    renamed = client.patch(f"/api/goals/{other['id']}", json={"code": "L0"})
    assert renamed.status_code == 409, renamed.text
    # Re-sending a goal's own code is not a duplicate of itself.
    same = client.patch(f"/api/goals/{goal['id']}", json={"code": "L0"})
    assert same.status_code == 200, same.text


def test_an_unknown_status_is_refused(client):
    response = client.post("/api/goals", json={"code": "L0", "name_cn": "x", "status": "done"})
    assert response.status_code == 422, response.text


def test_null_position_or_status_is_refused(client):
    goal = create_goal(client)
    for field in ("position", "status"):
        response = client.patch(f"/api/goals/{goal['id']}", json={field: None})
        assert response.status_code == 422, (field, response.text)


def test_unknown_fields_are_refused(client):
    response = client.post("/api/goals", json={"code": "L0", "name_cn": "x", "stages": []})
    assert response.status_code == 422, response.text


def test_a_missing_goal_is_404(client):
    assert client.get("/api/goals/999999").status_code == 404
    assert client.patch("/api/goals/999999", json={"remark": "x"}).status_code == 404
    assert client.delete("/api/goals/999999").status_code == 404


# --- achieved_on only when achieved ----------------------------------------------


def test_achieved_on_with_another_status_is_refused(client):
    for status in ("planned", "active"):
        response = client.post(
            "/api/goals",
            json={"code": "L0", "name_cn": "x", "status": status, "achieved_on": "2026-10-01"},
        )
        assert response.status_code == 422, (status, response.text)


def test_achieved_on_with_achieved_is_accepted_and_may_be_left_out(client):
    dated = create_goal(client, code="L0", status="achieved", achieved_on="2026-10-01")
    assert (dated["status"], dated["achieved_on"]) == ("achieved", "2026-10-01")
    undated = create_goal(client, code="L1", status="achieved")
    assert (undated["status"], undated["achieved_on"]) == ("achieved", None)


def test_setting_status_away_from_achieved_clears_the_date(client):
    goal = create_goal(client, status="achieved", achieved_on="2026-10-01")
    body = client.patch(f"/api/goals/{goal['id']}", json={"status": "active"}).json()
    assert (body["status"], body["achieved_on"]) == ("active", None)


def test_a_patch_dating_an_unachieved_goal_is_refused_and_changes_nothing(client):
    goal = create_goal(client, status="active")
    response = client.patch(
        f"/api/goals/{goal['id']}", json={"achieved_on": "2026-10-01", "remark": "changed"}
    )
    assert response.status_code == 422, response.text
    after = client.get(f"/api/goals/{goal['id']}").json()
    assert (after["achieved_on"], after["remark"]) == (None, None)
    # Leaving achieved while sending a date is refused too, not silently dropped.
    response = client.patch(
        f"/api/goals/{goal['id']}", json={"status": "planned", "achieved_on": "2026-10-01"}
    )
    assert response.status_code == 422, response.text
    # The mirror: the date with achieved is accepted.
    ok = client.patch(
        f"/api/goals/{goal['id']}", json={"status": "achieved", "achieved_on": "2026-10-01"}
    )
    assert ok.status_code == 200, ok.text
    assert ok.json()["achieved_on"] == "2026-10-01"


# --- delete is refused while the goal has stages ---------------------------------


def test_deleting_a_goal_with_stages_is_409_naming_the_count(client):
    goal = create_goal(client)
    # Load-bearing: without stages there is nothing to refuse.
    create_stage(client, goal["id"], name_cn="一")
    create_stage(client, goal["id"], name_cn="二")
    response = client.delete(f"/api/goals/{goal['id']}")
    assert response.status_code == 409, response.text
    body = response.json()
    assert body["stages"] == 2
    assert body["detail"]
    assert len(client.get(f"/api/goals/{goal['id']}").json()["stages"]) == 2


def test_a_goal_whose_stages_are_gone_can_be_deleted(client):
    """The mirror, on the same goal: the stage removed, the delete goes."""
    goal = create_goal(client)
    stage = create_stage(client, goal["id"])
    assert client.delete(f"/api/goals/{goal['id']}").status_code == 409
    assert client.delete(f"/api/stages/{stage['id']}").status_code == 204
    assert client.delete(f"/api/goals/{goal['id']}").status_code == 204


# --- stages under their goal, numbered across the roadmap -------------------------


def test_the_list_numbers_stages_across_goals_in_roadmap_order(client):
    later = create_goal(client, code="L1", position=1)
    first = create_goal(client, code="L0", position=0)
    # Created out of order on purpose: numbering follows positions, not ids.
    b = create_stage(client, later["id"], name_cn="B")
    a2 = create_stage(client, first["id"], name_cn="A2", position=1)
    a1 = create_stage(client, first["id"], name_cn="A1", position=0)

    body = client.get("/api/goals").json()
    assert [g["code"] for g in body] == ["L0", "L1"]
    assert [(s["display_name"], s["number"]) for s in body[0]["stages"]] == [("A1", 0), ("A2", 1)]
    assert [(s["display_name"], s["number"]) for s in body[1]["stages"]] == [("B", 2)]
    assert set(body[0]["stages"][0]) == {
        "id",
        "number",
        "display_name",
        "name_cn",
        "name_en",
        "name_alt",
        "position",
        "description",
        "test",
        "status",
        "passed_on",
    }
    assert {s["id"] for s in body[0]["stages"]} == {a1["id"], a2["id"]}
    # One goal read alone carries the same, roadmap-wide, numbers.
    alone = client.get(f"/api/goals/{later['id']}").json()
    assert [s["number"] for s in alone["stages"]] == [2]
    assert alone["stages"][0]["id"] == b["id"]


def test_reordering_goals_renumbers_their_stages(client):
    l0 = create_goal(client, code="L0", position=0)
    l1 = create_goal(client, code="L1", position=1)
    s0 = create_stage(client, l0["id"])
    s1 = create_stage(client, l1["id"])
    client.patch(f"/api/goals/{l1['id']}", json={"position": -1})
    assert client.get(f"/api/stages/{s1['id']}").json()["number"] == 0
    assert client.get(f"/api/stages/{s0['id']}").json()["number"] == 1
