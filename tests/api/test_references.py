"""References over HTTP: CRUD, the link, the group refusals, the filters, and
the option delete counting a reference.

Every wrong-category refusal uses the `options` fixture, which holds an option
of EVERY category - two `reference_group` ones among them - so a category
check has something of the wrong category to refuse. Each refusal has its
mirror using the same fixture.
"""

from tests.api.helpers import post


def create_reference(client, **body):
    body.setdefault("name", "表情集")
    body.setdefault("url", "https://example.com/faces")
    return post(client, "/api/references", body)


def test_a_reference_round_trips_through_create_read_update_delete(client, options):
    created = create_reference(
        client,
        name=" 手的姿勢 ",
        url="https://example.com/hands",
        group_ids=[options["reference_group"].id],
        notes="**看指節**\n\n第二行",
    )
    read = client.get(f"/api/references/{created['id']}").json()
    assert read == created
    assert read["name"] == "手的姿勢"
    assert read["url"] == "https://example.com/hands"
    assert read["groups"] == [
        {"id": options["reference_group"].id, "value": "表情", "description": None}
    ]
    assert read["notes"] == "**看指節**\n\n第二行"
    assert read["created_at"] and read["updated_at"]
    assert set(read) == {"id", "name", "url", "groups", "notes", "created_at", "updated_at"}

    updated = client.patch(
        f"/api/references/{created['id']}", json={"name": "手", "notes": ""}
    )
    assert updated.status_code == 200, updated.text
    body = updated.json()
    assert (body["name"], body["notes"]) == ("手", None)
    assert body["url"] == "https://example.com/hands"  # not sent, untouched
    assert [g["id"] for g in body["groups"]] == [options["reference_group"].id]  # untouched

    assert client.delete(f"/api/references/{created['id']}").status_code == 204
    assert client.get(f"/api/references/{created['id']}").status_code == 404


def test_a_reference_needs_a_name_and_a_url(client):
    for body in (
        {"url": "https://example.com"},
        {"name": "  ", "url": "https://example.com"},
        {"name": "x"},
        {"name": "x", "url": "  "},
        {"name": "x", "url": None},
    ):
        response = client.post("/api/references", json=body)
        assert response.status_code == 422, (body, response.text)


def test_the_url_must_be_an_http_link(client):
    for url in ("javascript:alert(1)", "ftp://example.com/x", "mailto:a@example.com"):
        response = client.post("/api/references", json={"name": "x", "url": url})
        assert response.status_code == 422, (url, response.text)


def test_a_url_with_no_scheme_gets_https(client):
    assert create_reference(client, url="example.com/poses")["url"] == "https://example.com/poses"
    assert create_reference(client, url="http://example.com/a")["url"] == "http://example.com/a"


def test_a_patch_cannot_null_or_blank_the_name_or_the_url(client):
    reference = create_reference(client)
    for body in ({"name": None}, {"name": ""}, {"url": None}, {"url": " "}, {"url": "javascript:x"}):
        response = client.patch(f"/api/references/{reference['id']}", json=body)
        assert response.status_code == 422, (body, response.text)
    # The mirror: a new link is accepted and normalised.
    ok = client.patch(f"/api/references/{reference['id']}", json={"url": "example.org"})
    assert ok.status_code == 200, ok.text
    assert ok.json()["url"] == "https://example.org"


def test_unknown_fields_are_refused(client):
    response = client.post(
        "/api/references", json={"name": "x", "url": "https://example.com", "visibility": "public"}
    )
    assert response.status_code == 422, response.text


def test_a_missing_reference_is_404(client):
    assert client.get("/api/references/999999").status_code == 404
    assert client.patch("/api/references/999999", json={"name": "x"}).status_code == 404
    assert client.delete("/api/references/999999").status_code == 404


# --- groups: the category refusal, list replacement, null ----------------------


def test_a_group_that_is_a_topic_option_is_refused(client, options):
    bad = options["topic"].id
    response = client.post(
        "/api/references",
        json={
            "name": "x",
            "url": "https://example.com",
            "group_ids": [options["reference_group"].id, bad],
        },
    )
    assert response.status_code == 422, response.text
    assert str(bad) in response.json()["detail"]
    # Refused before anything was written.
    assert client.get("/api/references").json() == []


def test_a_group_that_is_a_reference_group_option_is_accepted(client, options):
    reference = create_reference(
        client, group_ids=[options["other_reference_group"].id, options["reference_group"].id]
    )
    assert {g["id"] for g in reference["groups"]} == {
        options["reference_group"].id,
        options["other_reference_group"].id,
    }


def test_a_patch_naming_a_wrong_group_is_refused_and_changes_nothing(client, options):
    reference = create_reference(client, group_ids=[options["reference_group"].id])
    response = client.patch(
        f"/api/references/{reference['id']}",
        json={"group_ids": [options["note_category"].id], "name": "changed"},
    )
    assert response.status_code == 422, response.text
    after = client.get(f"/api/references/{reference['id']}").json()
    assert after["name"] == "表情集"
    assert [g["id"] for g in after["groups"]] == [options["reference_group"].id]


def test_unknown_group_ids_are_422_naming_the_id(client):
    response = client.post(
        "/api/references", json={"name": "x", "url": "https://example.com", "group_ids": [999999]}
    )
    assert response.status_code == 422, response.text
    assert "999999" in response.json()["detail"]


def test_group_ids_sent_replace_the_list_and_empty_clears_it(client, options):
    a = options["reference_group"].id
    b = options["other_reference_group"].id
    reference = create_reference(client, group_ids=[a])

    replaced = client.patch(f"/api/references/{reference['id']}", json={"group_ids": [b]})
    assert replaced.status_code == 200, replaced.text
    assert [g["id"] for g in replaced.json()["groups"]] == [b]

    cleared = client.patch(f"/api/references/{reference['id']}", json={"group_ids": []})
    assert cleared.json()["groups"] == []


def test_null_for_the_group_list_is_refused(client, options):
    reference = create_reference(client, group_ids=[options["reference_group"].id])
    response = client.patch(f"/api/references/{reference['id']}", json={"group_ids": None})
    assert response.status_code == 422, response.text
    after = client.get(f"/api/references/{reference['id']}").json()
    assert [g["id"] for g in after["groups"]] == [options["reference_group"].id]


def test_a_group_only_patch_moves_updated_at(client, db, options):
    from sqlalchemy import text

    reference = create_reference(client)
    db.execute(
        text("UPDATE reference SET updated_at = updated_at - interval '1 day' WHERE id = :id"),
        {"id": reference["id"]},
    )
    db.expire_all()
    before = client.get(f"/api/references/{reference['id']}").json()["updated_at"]
    after = client.patch(
        f"/api/references/{reference['id']}", json={"group_ids": [options["reference_group"].id]}
    ).json()["updated_at"]
    assert after > before


# --- the library ----------------------------------------------------------------


def _names(client, **params):
    response = client.get("/api/references", params=params)
    assert response.status_code == 200, response.text
    return [r["name"] for r in response.json()]


def test_the_list_is_ordered_by_name_ignoring_case_then_id(client):
    first = create_reference(client, name="same")
    for name in ("比例", "anatomy", "Bones"):
        create_reference(client, name=name)
    second = create_reference(client, name="Same")
    names = _names(client)
    assert names == sorted(["比例", "anatomy", "Bones", "same", "Same"], key=str.casefold)
    ids = [r["id"] for r in client.get("/api/references").json() if r["name"].casefold() == "same"]
    assert ids == [first["id"], second["id"]]


def test_search_matches_the_name_the_url_and_the_notes(client):
    create_reference(client, name="Hands", url="https://a.example/x")
    create_reference(client, name="二號", url="https://posemaniacs.example/")
    create_reference(client, name="三號", notes="這裡有很多表情")
    create_reference(client, name="四號")  # matches none of the terms

    assert _names(client, q="hand") == ["Hands"]
    assert _names(client, q="posemaniacs") == ["二號"]
    assert _names(client, q="表情") == ["三號"]
    assert _names(client, q="%") == []


def test_group_filter_means_any_of_and_no_group_keeps_the_ungrouped(client, options):
    a = options["reference_group"].id
    b = options["other_reference_group"].id
    create_reference(client, name="甲", group_ids=[a])
    create_reference(client, name="乙", group_ids=[b])
    create_reference(client, name="丙", group_ids=[a, b])
    create_reference(client, name="丁")

    # 乙 is grouped, in the other group: the row the filter must exclude.
    assert _names(client, group_id=a) == sorted(["甲", "丙"])
    assert _names(client, group_id=[a, b]) == sorted(["甲", "乙", "丙"])
    assert _names(client, no_group=True) == ["丁"]
    # The filters narrow each other: in group a AND in no group is nothing.
    assert _names(client, group_id=a, no_group=True) == []
    assert _names(client, q="乙", group_id=[a, b]) == ["乙"]


def test_a_summary_row_carries_an_excerpt_not_the_notes(client, options):
    long_notes = "第一段\n\n" + "字" * 200
    create_reference(client, notes=long_notes, group_ids=[options["reference_group"].id])
    create_reference(client, name="無筆記")
    rows = {r["name"]: r for r in client.get("/api/references").json()}
    row = rows["表情集"]
    assert set(row) == {"id", "name", "url", "groups", "notes_excerpt", "updated_at"}
    assert row["notes_excerpt"].startswith("第一段 字")
    assert row["notes_excerpt"].endswith("…")
    assert len(row["notes_excerpt"]) == 121
    assert row["groups"][0]["value"] == "表情"
    assert rows["無筆記"]["notes_excerpt"] is None


# --- options: a group in use ------------------------------------------------------


def test_an_option_delete_counts_the_references_in_the_group(client, options):
    group = options["reference_group"].id
    first = create_reference(client, group_ids=[group])
    create_reference(client, name="二", group_ids=[group, options["other_reference_group"].id])

    counts = {o["id"]: o["in_use"] for o in client.get("/api/options").json()}
    assert counts[group] == 2
    assert counts[options["other_reference_group"].id] == 1

    stale = client.delete(f"/api/options/{group}", params={"in_use": 1})
    assert stale.status_code == 409, stale.text
    assert (stale.json()["expected"], stale.json()["actual"]) == (1, 2)

    deleted = client.delete(f"/api/options/{group}", params={"in_use": 2})
    assert deleted.status_code == 204, deleted.text
    # The links went; the references stay.
    after = client.get(f"/api/references/{first['id']}").json()
    assert after["groups"] == []
