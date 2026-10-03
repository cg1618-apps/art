"""Stages over HTTP: CRUD with resources, the name rule, the date-iff-status
rule, moving between goals, and the number every stage is shown with.

Every refusal has a mirror that succeeds against the same setup.
"""


def create_goal(client, code="L0", **body):
    body.setdefault("name_cn", code)
    response = client.post("/api/goals", json={"code": code, **body})
    assert response.status_code == 201, response.text
    return response.json()


def create_stage(client, goal_id, **body):
    body.setdefault("name_cn", "線條")
    response = client.post("/api/stages", json={"goal_id": goal_id, **body})
    assert response.status_code == 201, response.text
    return response.json()


def test_a_stage_round_trips_through_create_read_update_delete(client):
    goal = create_goal(client, "L0", name_cn="基礎", name_en="Foundations")
    created = create_stage(
        client,
        goal["id"],
        name_cn="線條與形狀",
        name_en="Lines and shapes",
        description="只有 2D。",
        test="一頁穩定的線條。",
        status="in_progress",
        remark="用手肘",
        resources=[{"name": "講座", "url": "example.com/lines"}],
    )
    assert created == {
        "id": created["id"],
        "number": 0,
        "display_name": "線條與形狀",
        "name_cn": "線條與形狀",
        "name_en": "Lines and shapes",
        "name_alt": None,
        "position": 0,
        "description": "只有 2D。",
        "test": "一頁穩定的線條。",
        "status": "in_progress",
        "passed_on": None,
        "goal": {"id": goal["id"], "code": "L0", "display_name": "基礎"},
        "remark": "用手肘",
        "resources": [
            {
                "id": created["resources"][0]["id"],
                "name": "講座",
                "url": "https://example.com/lines",
            }
        ],
    }
    assert client.get(f"/api/stages/{created['id']}").json() == created

    updated = client.patch(
        f"/api/stages/{created['id']}", json={"status": "passed", "passed_on": "2026-10-03"}
    )
    assert updated.status_code == 200, updated.text
    body = updated.json()
    assert (body["status"], body["passed_on"]) == ("passed", "2026-10-03")
    assert len(body["resources"]) == 1  # not sent, untouched

    assert client.delete(f"/api/stages/{created['id']}").status_code == 204
    assert client.get(f"/api/stages/{created['id']}").status_code == 404
    assert client.get(f"/api/goals/{goal['id']}").json()["stages"] == []


def test_a_new_stage_goes_last_in_its_goal_unless_placed(client):
    goal = create_goal(client, "L0")
    other = create_goal(client, "L1")
    first = create_stage(client, goal["id"], name_cn="一")
    second = create_stage(client, goal["id"], name_cn="二")
    elsewhere = create_stage(client, other["id"], name_cn="別")
    placed = create_stage(client, goal["id"], name_cn="零", position=-1)
    assert (first["position"], second["position"]) == (0, 1)
    assert elsewhere["position"] == 0  # counted per goal
    assert placed["position"] == -1
    names = [s["name_cn"] for s in client.get(f"/api/goals/{goal['id']}").json()["stages"]]
    assert names == ["零", "一", "二"]


def test_a_stage_needs_a_goal_that_exists(client):
    assert client.post("/api/stages", json={"name_cn": "x"}).status_code == 422
    response = client.post("/api/stages", json={"goal_id": 999999, "name_cn": "x"})
    assert response.status_code == 422, response.text
    assert "999999" in response.json()["detail"]
    # The mirror: a goal that exists is accepted.
    goal = create_goal(client)
    assert create_stage(client, goal["id"])["goal"]["id"] == goal["id"]


def test_a_stage_needs_a_name(client):
    goal = create_goal(client)
    for body in ({}, {"name_cn": "  "}, {"name_en": "", "test": "x"}):
        response = client.post("/api/stages", json={"goal_id": goal["id"], **body})
        assert response.status_code == 422, (body, response.text)


def test_a_patch_cannot_clear_the_last_name(client):
    stage = create_stage(client, create_goal(client)["id"], name_cn="線條", name_en=None)
    response = client.patch(f"/api/stages/{stage['id']}", json={"name_cn": None})
    assert response.status_code == 422, response.text
    response = client.patch(
        f"/api/stages/{stage['id']}", json={"name_cn": None, "name_alt": "Lines"}
    )
    assert response.status_code == 200, response.text
    assert response.json()["display_name"] == "Lines"


def test_null_goal_position_status_or_resources_is_refused(client):
    stage = create_stage(client, create_goal(client)["id"])
    for field in ("goal_id", "position", "status", "resources"):
        response = client.patch(f"/api/stages/{stage['id']}", json={field: None})
        assert response.status_code == 422, (field, response.text)


def test_an_unknown_status_is_refused(client):
    goal = create_goal(client)
    response = client.post(
        "/api/stages", json={"goal_id": goal["id"], "name_cn": "x", "status": "done"}
    )
    assert response.status_code == 422, response.text


def test_a_missing_stage_is_404(client):
    assert client.get("/api/stages/999999").status_code == 404
    assert client.patch("/api/stages/999999", json={"remark": "x"}).status_code == 404
    assert client.delete("/api/stages/999999").status_code == 404


# --- passed_on only when passed --------------------------------------------------


def test_passed_on_with_another_status_is_refused(client):
    goal = create_goal(client)
    for status in ("not_started", "in_progress"):
        response = client.post(
            "/api/stages",
            json={
                "goal_id": goal["id"],
                "name_cn": "x",
                "status": status,
                "passed_on": "2026-10-03",
            },
        )
        assert response.status_code == 422, (status, response.text)
    # The mirror.
    passed = create_stage(client, goal["id"], status="passed", passed_on="2026-10-03")
    assert passed["passed_on"] == "2026-10-03"


def test_setting_status_away_from_passed_clears_the_date(client):
    stage = create_stage(
        client, create_goal(client)["id"], status="passed", passed_on="2026-10-03"
    )
    body = client.patch(f"/api/stages/{stage['id']}", json={"status": "in_progress"}).json()
    assert (body["status"], body["passed_on"]) == ("in_progress", None)


def test_a_patch_dating_an_unpassed_stage_is_refused_and_changes_nothing(client):
    stage = create_stage(client, create_goal(client)["id"])
    response = client.patch(
        f"/api/stages/{stage['id']}", json={"passed_on": "2026-10-03", "remark": "changed"}
    )
    assert response.status_code == 422, response.text
    after = client.get(f"/api/stages/{stage['id']}").json()
    assert (after["passed_on"], after["remark"]) == (None, None)
    # The mirror: passing it with the date is accepted.
    ok = client.patch(
        f"/api/stages/{stage['id']}", json={"status": "passed", "passed_on": "2026-10-03"}
    )
    assert ok.status_code == 200, ok.text


# --- moving, and the numbers ------------------------------------------------------


def test_moving_a_stage_lands_it_last_in_the_new_goal_and_renumbers(client):
    l0 = create_goal(client, "L0", position=0)
    l1 = create_goal(client, "L1", position=1)
    a = create_stage(client, l0["id"], name_cn="A")
    b = create_stage(client, l0["id"], name_cn="B")
    c = create_stage(client, l1["id"], name_cn="C")
    d = create_stage(client, l1["id"], name_cn="D")
    assert [a["number"], b["number"], c["number"], d["number"]] == [0, 1, 2, 3]

    moved = client.patch(f"/api/stages/{a['id']}", json={"goal_id": l1["id"]})
    assert moved.status_code == 200, moved.text
    body = moved.json()
    assert body["goal"] == {"id": l1["id"], "code": "L1", "display_name": "L1"}
    assert body["position"] == 2  # after C (0) and D (1)
    assert body["number"] == 3

    roadmap = client.get("/api/goals").json()
    assert [(s["name_cn"], s["number"]) for g in roadmap for s in g["stages"]] == [
        ("B", 0),
        ("C", 1),
        ("D", 2),
        ("A", 3),
    ]


def test_moving_a_stage_with_a_position_puts_it_there(client):
    l0 = create_goal(client, "L0", position=0)
    l1 = create_goal(client, "L1", position=1)
    a = create_stage(client, l0["id"], name_cn="A")
    create_stage(client, l1["id"], name_cn="C", position=0)
    body = client.patch(
        f"/api/stages/{a['id']}", json={"goal_id": l1["id"], "position": -1}
    ).json()
    assert (body["position"], body["number"]) == (-1, 0)


def test_moving_to_a_goal_that_does_not_exist_is_refused(client):
    goal = create_goal(client)
    stage = create_stage(client, goal["id"])
    response = client.patch(f"/api/stages/{stage['id']}", json={"goal_id": 999999})
    assert response.status_code == 422, response.text
    assert client.get(f"/api/stages/{stage['id']}").json()["goal"]["id"] == goal["id"]


def test_re_sending_the_same_goal_does_not_move_the_stage(client):
    goal = create_goal(client)
    first = create_stage(client, goal["id"], name_cn="一")
    create_stage(client, goal["id"], name_cn="二")
    body = client.patch(
        f"/api/stages/{first['id']}", json={"goal_id": goal["id"], "remark": "x"}
    ).json()
    assert (body["position"], body["number"]) == (0, 0)


# --- resources --------------------------------------------------------------------


def test_resources_are_ordered_and_replaced_whole(client):
    stage = create_stage(
        client,
        create_goal(client)["id"],
        resources=[
            {"name": "一", "url": "https://example.com/1"},
            {"url": "example.com/2"},
        ],
    )
    assert [(r["name"], r["url"]) for r in stage["resources"]] == [
        ("一", "https://example.com/1"),
        (None, "https://example.com/2"),
    ]
    replaced = client.patch(
        f"/api/stages/{stage['id']}", json={"resources": [{"url": "https://example.com/3"}]}
    ).json()
    assert [r["url"] for r in replaced["resources"]] == ["https://example.com/3"]
    cleared = client.patch(f"/api/stages/{stage['id']}", json={"resources": []}).json()
    assert cleared["resources"] == []


def test_a_resource_must_be_an_http_link(client):
    goal = create_goal(client)
    for url in ("javascript:alert(1)", "   ", "ftp://example.com/x"):
        response = client.post(
            "/api/stages",
            json={"goal_id": goal["id"], "name_cn": "x", "resources": [{"url": url}]},
        )
        assert response.status_code == 422, (url, response.text)


def test_deleting_a_stage_takes_its_resources(client, db):
    from app.models import StageResource

    stage = create_stage(
        client, create_goal(client)["id"], resources=[{"url": "https://example.com/1"}]
    )
    assert client.delete(f"/api/stages/{stage['id']}").status_code == 204
    db.expire_all()
    assert db.query(StageResource).filter_by(stage_id=stage["id"]).count() == 0
