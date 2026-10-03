"""System options over HTTP: the registry, CRUD, duplicates, and the counted
delete.

Every refusal sets up the thing it refuses and has a mirror that succeeds.
"""

from app.constants import OPTION_CATEGORIES
from app.models import Note, NoteTopic


def create_option(client, **body):
    response = client.post("/api/options", json=body)
    assert response.status_code == 201, response.text
    return response.json()


def test_categories_are_the_registry_in_order(client):
    body = client.get("/api/options/categories").json()
    assert [c["key"] for c in body] == [
        "note_category", "topic", "method", "source", "location", "tool", "reference_group",
    ]
    assert [c["key"] for c in body] == list(OPTION_CATEGORIES)
    assert body[0] == {
        "key": "note_category",
        "label": "筆記分類",
        "description": OPTION_CATEGORIES["note_category"].description,
    }


def test_an_option_round_trips_through_create_list_update_delete(client):
    created = create_option(
        client, category="method", value="速寫", description="限時快速畫", remark="常用"
    )
    assert created == {
        "id": created["id"],
        "category": "method",
        "value": "速寫",
        "description": "限時快速畫",
        "remark": "常用",
        "sort_order": 0,
        "in_use": 0,
    }

    listed = client.get("/api/options", params={"category": "method"}).json()
    assert listed == [created]

    updated = client.patch(
        f"/api/options/{created['id']}", json={"value": "速寫練習", "remark": None}
    )
    assert updated.status_code == 200, updated.text
    body = updated.json()
    assert (body["value"], body["remark"], body["description"]) == ("速寫練習", None, "限時快速畫")

    deleted = client.delete(f"/api/options/{created['id']}", params={"in_use": 0})
    assert deleted.status_code == 204, deleted.text
    assert client.get("/api/options").json() == []


def test_a_new_option_goes_last_in_its_category_unless_placed(client):
    first = create_option(client, category="topic", value="線條")
    second = create_option(client, category="topic", value="形狀")
    placed = create_option(client, category="topic", value="透視", sort_order=0)
    other = create_option(client, category="method", value="描寫")
    assert (first["sort_order"], second["sort_order"]) == (0, 1)
    assert other["sort_order"] == 0  # counted per category
    values = [o["value"] for o in client.get("/api/options", params={"category": "topic"}).json()]
    # sort_order, then id: 線條 and 透視 share 0, and 線條 is older.
    assert values == ["線條", "透視", "形狀"]
    assert placed["sort_order"] == 0


def test_the_list_is_in_registry_order_then_sort_order(client, make_option):
    make_option("method", "描寫", sort_order=0)
    make_option("topic", "人體", sort_order=5)
    make_option("topic", "透視", sort_order=1)
    make_option("note_category", "名詞", sort_order=9)
    body = client.get("/api/options").json()
    assert [(o["category"], o["value"]) for o in body] == [
        ("note_category", "名詞"),
        ("topic", "透視"),
        ("topic", "人體"),
        ("method", "描寫"),
    ]


def test_an_unregistered_category_is_refused(client):
    response = client.post("/api/options", json={"category": "colour", "value": "紅"})
    assert response.status_code == 422, response.text
    assert client.get("/api/options", params={"category": "colour"}).status_code == 422


def test_a_blank_value_is_refused(client):
    response = client.post("/api/options", json={"category": "topic", "value": "   "})
    assert response.status_code == 422, response.text


def test_a_value_is_stored_trimmed(client):
    assert create_option(client, category="topic", value="  透視 ")["value"] == "透視"


def test_a_duplicate_value_is_409_ignoring_case_and_whitespace(client):
    create_option(client, category="topic", value="Hand")
    for value in ("Hand", "hand", " HAND "):
        response = client.post("/api/options", json={"category": "topic", "value": value})
        assert response.status_code == 409, (value, response.text)
        assert "detail" in response.json()


def test_the_same_value_in_another_category_is_not_a_duplicate(client):
    """The mirror: uniqueness is per category."""
    create_option(client, category="topic", value="速寫")
    create_option(client, category="method", value="速寫")


def test_a_rename_onto_another_value_is_409_but_onto_itself_is_fine(client):
    one = create_option(client, category="topic", value="線條")
    create_option(client, category="topic", value="形狀")
    clash = client.patch(f"/api/options/{one['id']}", json={"value": "形狀 "})
    assert clash.status_code == 409, clash.text
    recase = client.patch(f"/api/options/{one['id']}", json={"value": " 線條 "})
    assert recase.status_code == 200, recase.text


def test_the_database_refuses_a_duplicate_too(db, make_option):
    """The unique index holds the rule for a row written without the API."""
    import pytest
    from sqlalchemy.exc import IntegrityError

    make_option("topic", "Hand")
    with pytest.raises(IntegrityError):
        make_option("topic", " hand ")


def test_a_category_cannot_change(client):
    option = create_option(client, category="topic", value="透視")
    response = client.patch(f"/api/options/{option['id']}", json={"category": "method"})
    assert response.status_code == 422, response.text
    # Even to the category it already has: the field is not writable.
    same = client.patch(f"/api/options/{option['id']}", json={"category": "topic"})
    assert same.status_code == 422, same.text


def test_value_and_sort_order_cannot_be_cleared(client):
    option = create_option(client, category="topic", value="透視")
    for body in ({"value": None}, {"sort_order": None}, {"value": ""}):
        response = client.patch(f"/api/options/{option['id']}", json=body)
        assert response.status_code == 422, (body, response.text)


def test_a_missing_option_is_404(client):
    assert client.patch("/api/options/999999", json={"value": "x"}).status_code == 404
    assert client.delete("/api/options/999999", params={"in_use": 0}).status_code == 404


# --- in use, and the counted delete -------------------------------------------


def _note_using(db, *, category=None, topics=()):
    note = Note(name="筆記", category_id=category.id if category else None)
    db.add(note)
    db.flush()
    for topic in topics:
        db.add(NoteTopic(note_id=note.id, option_id=topic.id))
    db.flush()
    return note


def test_in_use_counts_category_references_and_topic_links(client, db, options):
    _note_using(db, category=options["note_category"], topics=[options["topic"]])
    _note_using(db, category=options["note_category"])
    _note_using(db, topics=[options["topic"], options["other_topic"]])
    counts = {o["id"]: o["in_use"] for o in client.get("/api/options").json()}
    assert counts[options["note_category"].id] == 2
    assert counts[options["topic"].id] == 2
    assert counts[options["other_topic"].id] == 1
    assert counts[options["method"].id] == 0


def test_delete_requires_the_count(client, options):
    response = client.delete(f"/api/options/{options['method'].id}")
    assert response.status_code == 422, response.text


def test_a_stale_count_refuses_and_says_what_moved(client, db, options):
    _note_using(db, topics=[options["topic"]])
    _note_using(db, topics=[options["topic"]])
    response = client.delete(f"/api/options/{options['topic'].id}", params={"in_use": 1})
    assert response.status_code == 409, response.text
    body = response.json()
    assert (body["field"], body["expected"], body["actual"]) == ("in_use", 1, 2)
    assert body["detail"]
    # Nothing was removed.
    ids = [o["id"] for o in client.get("/api/options").json()]
    assert options["topic"].id in ids


def test_the_right_count_deletes_cascading_topics_and_nulling_categories(client, db, options):
    """The mirror of the stale-count refusal, with the same kind of links."""
    tagged = _note_using(db, topics=[options["topic"], options["other_topic"]])
    filed = _note_using(db, category=options["note_category"], topics=[options["topic"]])
    tagged_id, filed_id = tagged.id, filed.id

    topic = client.delete(f"/api/options/{options['topic'].id}", params={"in_use": 2})
    assert topic.status_code == 204, topic.text
    category = client.delete(
        f"/api/options/{options['note_category'].id}", params={"in_use": 1}
    )
    assert category.status_code == 204, category.text

    tagged_now = client.get(f"/api/notes/{tagged_id}").json()
    assert [t["value"] for t in tagged_now["topics"]] == ["人體"]
    filed_now = client.get(f"/api/notes/{filed_id}").json()
    assert filed_now["category"] is None
    assert filed_now["topics"] == []
    # The notes themselves survive.
    assert filed_now["name"] == "筆記"


# --- the references the Record + Exercise module adds -------------------------


def _record_and_drill_using(client, options):
    """One drill with a source, one exercise with a topic, and a record naming
    a location, a method and a tool - every reference this module adds."""
    from tests.api.helpers import create_drill, create_exercise, create_record

    exercise = create_exercise(client, topic_ids=[options["topic"].id])
    drill = create_drill(client, exercise["id"], source_id=options["source"].id)
    record = create_record(
        client,
        drill_id=drill["id"],
        location_id=options["location"].id,
        method_id=options["method"].id,
        tool_id=options["tool"].id,
    )
    return exercise, drill, record


def test_in_use_counts_exercise_drill_and_record_references(client, options):
    _record_and_drill_using(client, options)
    counts = {o["id"]: o["in_use"] for o in client.get("/api/options").json()}
    for key in ("topic", "source", "location", "method", "tool"):
        assert counts[options[key].id] == 1, key
    # The mirror: an option nothing names counts nothing.
    assert counts[options["other_method"].id] == 0


def test_deleting_options_nulls_single_references_and_cascades_exercise_topics(client, options):
    exercise, drill, record = _record_and_drill_using(client, options)
    for key in ("topic", "source", "location", "method", "tool"):
        response = client.delete(f"/api/options/{options[key].id}", params={"in_use": 1})
        assert response.status_code == 204, (key, response.text)

    assert client.get(f"/api/exercises/{exercise['id']}").json()["topics"] == []
    assert client.get(f"/api/drills/{drill['id']}").json()["source"] is None
    after = client.get(f"/api/records/{record['id']}").json()
    assert (after["location"], after["method"], after["tool"]) == (None, None, None)
    # The rows themselves survive.
    assert after["activity"]["drill"]["id"] == drill["id"]
