"""Notes over HTTP: CRUD, the lists, wrong-category refusals, and search.

Every wrong-category refusal uses the `options` fixture, which holds an option
of EVERY category: a category check over a table holding only the right
category would pass without ever firing. Each refusal has its mirror - the
right category accepted - using that same fixture, so a green proves the check
did the refusing.
"""


def create_note(client, **body):
    body.setdefault("name_cn", "透視")
    response = client.post("/api/notes", json=body)
    assert response.status_code == 201, response.text
    return response.json()


def test_a_note_round_trips_through_create_read_update_delete(client, options):
    created = create_note(
        client,
        name_cn="消失點",
        name_en="vanishing point",
        name_alt="VP",
        aliases=["滅點", "VP點"],
        category_id=options["note_category"].id,
        topic_ids=[options["topic"].id],
        summary="平行線在畫面上交會的點。",
        body="# 一點透視\n\n- 地平線",
        remark="再補例子",
        resources=[{"name": "教學", "url": "https://example.com/vp"}],
    )
    read = client.get(f"/api/notes/{created['id']}").json()
    assert read == created
    assert read["display_name"] == "消失點"
    assert read["category"] == {
        "id": options["note_category"].id,
        "value": "名詞",
        "description": None,
    }
    assert read["topics"] == [
        {"id": options["topic"].id, "value": "透視", "description": "空間的遠近"}
    ]
    assert read["aliases"] == sorted(["滅點", "VP點"])
    assert read["resources"][0]["name"] == "教學"
    assert read["resources"][0]["url"] == "https://example.com/vp"
    assert read["visibility"] == "private"
    assert read["created_at"] and read["updated_at"]

    updated = client.patch(
        f"/api/notes/{created['id']}",
        json={"category_id": None, "aliases": [], "topic_ids": [], "visibility": "unlisted"},
    )
    assert updated.status_code == 200, updated.text
    body = updated.json()
    assert (body["category"], body["aliases"], body["topics"]) == (None, [], [])
    assert body["visibility"] == "unlisted"
    assert body["summary"] == "平行線在畫面上交會的點。"  # not sent, untouched
    assert len(body["resources"]) == 1  # not sent, untouched

    assert client.delete(f"/api/notes/{created['id']}").status_code == 204
    assert client.get(f"/api/notes/{created['id']}").status_code == 404


def test_a_note_needs_a_name(client):
    for body in ({}, {"name_cn": "  "}, {"name_en": "", "summary": "x"}):
        response = client.post("/api/notes", json=body)
        assert response.status_code == 422, (body, response.text)


def test_any_one_name_slot_is_enough_and_display_name_falls_back(client):
    assert create_note(client, name_cn=None, name_en="gesture")["display_name"] == "gesture"
    assert create_note(client, name_cn=None, name_alt="GD")["display_name"] == "GD"


def test_a_patch_cannot_clear_the_last_name(client):
    note = create_note(client, name_cn="透視", name_en=None)
    response = client.patch(f"/api/notes/{note['id']}", json={"name_cn": None})
    assert response.status_code == 422, response.text
    # The mirror: clearing one name while another remains is fine.
    response = client.patch(
        f"/api/notes/{note['id']}", json={"name_cn": None, "name_en": "perspective"}
    )
    assert response.status_code == 200, response.text
    assert response.json()["display_name"] == "perspective"


def test_the_same_alias_twice_is_refused(client):
    response = client.post("/api/notes", json={"name_cn": "透視", "aliases": ["VP", " vp "]})
    assert response.status_code == 422, response.text


def test_aliases_are_trimmed_and_empties_dropped(client):
    note = create_note(client, aliases=[" 滅點 ", "", "  "])
    assert note["aliases"] == ["滅點"]


def test_an_unknown_visibility_is_refused(client):
    response = client.post("/api/notes", json={"name_cn": "x", "visibility": "secret"})
    assert response.status_code == 422, response.text


# --- wrong-category refusals, each with its mirror ----------------------------


def test_a_category_that_is_a_topic_option_is_refused(client, options):
    bad = options["topic"].id
    response = client.post("/api/notes", json={"name_cn": "x", "category_id": bad})
    assert response.status_code == 422, response.text
    assert str(bad) in response.json()["detail"]


def test_a_category_that_is_a_note_category_option_is_accepted(client, options):
    note = create_note(client, category_id=options["note_category"].id)
    assert note["category"]["id"] == options["note_category"].id


def test_a_topic_that_is_a_method_option_is_refused(client, options):
    bad = options["method"].id
    response = client.post(
        "/api/notes", json={"name_cn": "x", "topic_ids": [options["topic"].id, bad]}
    )
    assert response.status_code == 422, response.text
    assert str(bad) in response.json()["detail"]


def test_a_topic_that_is_a_topic_option_is_accepted(client, options):
    note = create_note(client, topic_ids=[options["topic"].id, options["other_topic"].id])
    assert {t["id"] for t in note["topics"]} == {options["topic"].id, options["other_topic"].id}


def test_a_patch_naming_the_wrong_category_is_refused_and_changes_nothing(client, options):
    note = create_note(client, category_id=options["note_category"].id)
    response = client.patch(
        f"/api/notes/{note['id']}",
        json={"category_id": options["method"].id, "summary": "changed"},
    )
    assert response.status_code == 422, response.text
    assert str(options["method"].id) in response.json()["detail"]
    after = client.get(f"/api/notes/{note['id']}").json()
    assert after["category"]["id"] == options["note_category"].id
    assert after["summary"] is None
    # The mirror: the other note_category option is accepted.
    ok = client.patch(
        f"/api/notes/{note['id']}", json={"category_id": options["other_note_category"].id}
    )
    assert ok.status_code == 200, ok.text
    assert ok.json()["category"]["value"] == "小技巧"


def test_a_patch_naming_a_wrong_topic_is_refused(client, options):
    note = create_note(client)
    bad = client.patch(f"/api/notes/{note['id']}", json={"topic_ids": [options["note_category"].id]})
    assert bad.status_code == 422, bad.text
    good = client.patch(f"/api/notes/{note['id']}", json={"topic_ids": [options["topic"].id]})
    assert good.status_code == 200, good.text


def test_unknown_option_ids_are_422_naming_the_id(client, options):
    for body in ({"category_id": 999999}, {"topic_ids": [999999]}):
        response = client.post("/api/notes", json={"name_cn": "x", **body})
        assert response.status_code == 422, (body, response.text)
        assert "999999" in response.json()["detail"]


# --- lists: resources, topics, null ---------------------------------------------


def test_resources_are_ordered_and_replaced_whole(client):
    note = create_note(
        client,
        resources=[
            {"name": "一", "url": "https://example.com/1"},
            {"url": "example.com/2"},
            {"name": "三", "url": "http://example.com/3"},
        ],
    )
    assert [(r["name"], r["url"]) for r in note["resources"]] == [
        ("一", "https://example.com/1"),
        (None, "https://example.com/2"),
        ("三", "http://example.com/3"),
    ]
    replaced = client.patch(
        f"/api/notes/{note['id']}",
        json={"resources": [{"url": "https://example.com/3"}, {"url": "https://example.com/1"}]},
    ).json()
    assert [r["url"] for r in replaced["resources"]] == [
        "https://example.com/3",
        "https://example.com/1",
    ]
    cleared = client.patch(f"/api/notes/{note['id']}", json={"resources": []}).json()
    assert cleared["resources"] == []


def test_a_resource_must_be_an_http_link(client):
    for url in ("javascript:alert(1)", "   ", "ftp://example.com/x"):
        response = client.post(
            "/api/notes", json={"name_cn": "x", "resources": [{"url": url}]}
        )
        assert response.status_code == 422, (url, response.text)


def test_null_for_a_list_is_refused(client):
    note = create_note(client)
    for field in ("aliases", "topic_ids", "resources"):
        response = client.patch(f"/api/notes/{note['id']}", json={field: None})
        assert response.status_code == 422, (field, response.text)


def test_null_visibility_is_refused(client):
    note = create_note(client)
    response = client.patch(f"/api/notes/{note['id']}", json={"visibility": None})
    assert response.status_code == 422, response.text


def test_unknown_fields_are_refused(client):
    response = client.post("/api/notes", json={"name_cn": "x", "tags": []})
    assert response.status_code == 422, response.text


def test_a_missing_note_is_404(client):
    assert client.get("/api/notes/999999").status_code == 404
    assert client.patch("/api/notes/999999", json={"summary": "x"}).status_code == 404
    assert client.delete("/api/notes/999999").status_code == 404


def test_a_list_only_patch_moves_updated_at(client, db, options):
    from sqlalchemy import text

    note = create_note(client)
    # Backdate it, so a bump is visible within one transaction's clock.
    db.execute(
        text("UPDATE note SET updated_at = updated_at - interval '1 day' WHERE id = :id"),
        {"id": note["id"]},
    )
    db.expire_all()
    before = client.get(f"/api/notes/{note['id']}").json()["updated_at"]
    after = client.patch(
        f"/api/notes/{note['id']}", json={"topic_ids": [options["topic"].id]}
    ).json()["updated_at"]
    assert after > before


# --- search -------------------------------------------------------------------


def _names(client, **params):
    return [n["display_name"] for n in client.get("/api/notes", params=params).json()]


def test_the_list_is_ordered_by_display_name(client):
    for name in ("比例", "Anatomy", "構圖"):
        create_note(client, name_cn=name)
    assert _names(client) == sorted(["比例", "Anatomy", "構圖"], key=str.casefold)


def test_search_matches_names_aliases_and_summary_but_not_body(client):
    create_note(client, name_cn="一號", name_en="Foreshortening")
    create_note(client, name_cn="二號", name_alt="FSX")
    create_note(client, name_cn="三號", aliases=["縮短法"])
    create_note(client, name_cn="四號", summary="關於短縮的說明")
    create_note(client, name_cn="五號", body="正文裡寫著縮短法和 foreshortening")

    assert _names(client, q="foreshort") == ["一號"]
    assert _names(client, q="fsx") == ["二號"]
    assert _names(client, q="縮短") == ["三號"]
    assert _names(client, q="短縮") == ["四號"]
    # Body only: no match at all.
    assert _names(client, q="正文") == []


def test_search_treats_wildcards_literally(client):
    create_note(client, name_cn="一號")
    assert _names(client, q="%") == []
    assert _names(client, q="_") == []


def test_topic_and_category_filters_mean_any_of_and_narrow_each_other(client, options):
    a = options["topic"].id
    b = options["other_topic"].id
    cat = options["note_category"].id
    create_note(client, name_cn="甲", topic_ids=[a], category_id=cat)
    create_note(client, name_cn="乙", topic_ids=[b])
    create_note(client, name_cn="丙")

    assert _names(client, topic_id=a) == ["甲"]
    assert sorted(_names(client, topic_id=[a, b])) == sorted(["甲", "乙"])
    assert _names(client, category_id=cat) == ["甲"]
    assert _names(client, category_id=cat, topic_id=b) == []
    assert _names(client, q="乙", topic_id=[a, b]) == ["乙"]


def test_a_summary_row_carries_category_and_topics_but_not_the_body(client, options):
    create_note(
        client,
        category_id=options["note_category"].id,
        topic_ids=[options["topic"].id],
        body="長文",
    )
    row = client.get("/api/notes").json()[0]
    assert set(row) == {
        "id",
        "display_name",
        "name_cn",
        "name_en",
        "name_alt",
        "category",
        "topics",
        "summary",
        "visibility",
        "updated_at",
    }
    assert row["category"]["value"] == "名詞"
    assert [t["value"] for t in row["topics"]] == ["透視"]
