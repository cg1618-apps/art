"""The timer over HTTP: the single timer, its state machine, elapsed time by
the database clock, saving it as a record, the target and activity rules, and
the constraints at the database level.

Time never comes from sleeping. The whole test runs in one rolled-back
transaction, so PostgreSQL's `now()` is the same instant throughout; a test
that needs time to pass moves `running_since` back with `run_for`, and
asserts a range rather than an exact figure.

Every refusal is set up so it can bite - a second start has a first to
collide with, a refused record write has a stopped timer to leave intact -
and has a mirror that succeeds against the same setup.
"""

import datetime as dt

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from app.models import ActiveTimer
from tests.api.helpers import create_drill, create_exercise, post

STOPWATCH = {"mode": "stopwatch"}
COUNTDOWN = {"mode": "countdown", "target_seconds": 600}


@pytest.fixture
def practice(client):
    """An exercise with one drill: the two things a timer can name."""
    exercise = create_exercise(client, name_cn="人偶")
    drill = create_drill(client, exercise["id"], name="骨架五步")
    return {"exercise": exercise, "drill": drill}


@pytest.fixture
def run_for(db):
    """Make the running stretch `seconds` long by moving `running_since`
    back - the database clock does not move inside a test."""

    def run(seconds: int) -> None:
        db.execute(
            text(
                "UPDATE active_timer"
                " SET running_since = now() - make_interval(secs => :seconds)"
            ),
            {"seconds": seconds},
        )
        db.expire_all()

    return run


def start(client, **body) -> dict:
    return post(client, "/api/timer", {**STOPWATCH, **body})


def stopped(client, run_for, seconds: int = 1500, **body) -> dict:
    """A timer that ran `seconds` and was stopped."""
    start(client, **body)
    run_for(seconds)
    response = client.post("/api/timer/stop")
    assert response.status_code == 200, response.text
    return response.json()


def _time(value: str) -> dt.datetime:
    return dt.datetime.fromisoformat(value)


# --- reading and starting -----------------------------------------------------


def test_get_answers_null_when_there_is_no_timer(client):
    response = client.get("/api/timer")
    assert response.status_code == 200
    assert response.json() is None


def test_a_started_stopwatch_is_running_from_the_database_clock(client, db):
    created = start(client)
    db_now = db.execute(text("SELECT now()")).scalar_one()

    assert created == {
        "id": created["id"],
        "mode": "stopwatch",
        "target_seconds": None,
        "state": "running",
        "started_at": created["started_at"],
        "running_since": created["started_at"],
        "elapsed_seconds": 0,
        "stopped_at": None,
        "now": created["now"],
        "activity": None,
    }
    # Every time is the database's, not the test process's.
    assert _time(created["started_at"]) == db_now
    assert _time(created["now"]) == db_now
    assert client.get("/api/timer").json() == created


def test_a_second_timer_is_refused_while_one_exists(client):
    start(client)
    response = client.post("/api/timer", json=COUNTDOWN)
    assert response.status_code == 409, response.text

    # The mirror: once the first is discarded, the same body starts one.
    assert client.delete("/api/timer").status_code == 204
    assert client.post("/api/timer", json=COUNTDOWN).status_code == 201


def test_a_stopped_timer_still_blocks_a_new_one(client, run_for):
    stopped(client, run_for)
    assert client.post("/api/timer", json=STOPWATCH).status_code == 409


def test_a_countdown_needs_a_target_and_a_stopwatch_refuses_one(client):
    for body in (
        {"mode": "countdown"},
        {"mode": "countdown", "target_seconds": None},
        {"mode": "stopwatch", "target_seconds": 600},
        {"mode": "countdown", "target_seconds": 0},
        {"mode": "interval"},
    ):
        response = client.post("/api/timer", json=body)
        assert response.status_code == 422, (body, response.text)
    assert client.get("/api/timer").json() is None

    # The mirror.
    created = post(client, "/api/timer", COUNTDOWN)
    assert (created["mode"], created["target_seconds"]) == ("countdown", 600)


# --- the state machine --------------------------------------------------------


def test_pause_resume_and_stop_move_through_the_states(client):
    start(client)

    paused = client.post("/api/timer/pause")
    assert paused.status_code == 200, paused.text
    assert (paused.json()["state"], paused.json()["running_since"]) == ("paused", None)

    resumed = client.post("/api/timer/resume")
    assert resumed.status_code == 200, resumed.text
    assert resumed.json()["state"] == "running"
    assert resumed.json()["running_since"] is not None

    done = client.post("/api/timer/stop")
    assert done.status_code == 200, done.text
    assert done.json()["state"] == "stopped"
    assert done.json()["running_since"] is None
    assert done.json()["stopped_at"] == done.json()["now"]


def test_a_paused_timer_can_be_stopped(client):
    start(client)
    client.post("/api/timer/pause")
    response = client.post("/api/timer/stop")
    assert response.status_code == 200, response.text
    assert response.json()["state"] == "stopped"


def test_a_transition_from_the_wrong_state_is_409_and_changes_nothing(client, run_for):
    start(client)
    # Running: resume is refused, pause (the mirror) is not.
    assert client.post("/api/timer/resume").status_code == 409
    assert client.post("/api/timer/pause").status_code == 200

    # Paused: pause is refused, resume (the mirror) is not.
    assert client.post("/api/timer/pause").status_code == 409
    assert client.post("/api/timer/resume").status_code == 200

    run_for(60)
    before = client.post("/api/timer/stop").json()
    for action in ("pause", "resume", "stop"):
        response = client.post(f"/api/timer/{action}")
        assert response.status_code == 409, (action, response.text)
    assert client.get("/api/timer").json() == before


def test_every_action_on_no_timer_is_404(client):
    for method, path, body in (
        ("PATCH", "/api/timer", {"target_seconds": 60}),
        ("POST", "/api/timer/pause", None),
        ("POST", "/api/timer/resume", None),
        ("POST", "/api/timer/stop", None),
        ("POST", "/api/timer/record", {"date": "2026-10-03"}),
        ("DELETE", "/api/timer", None),
    ):
        response = client.request(method, path, json=body)
        assert response.status_code == 404, (method, path, response.text)


# --- elapsed time -------------------------------------------------------------


def test_pause_folds_the_running_stretch_into_elapsed(client, run_for):
    start(client)
    run_for(90)

    running = client.get("/api/timer").json()
    # While running nothing is folded in: the live figure is computed from
    # `now` and `running_since`.
    assert running["elapsed_seconds"] == 0
    live = (_time(running["now"]) - _time(running["running_since"])).total_seconds()
    assert 90 <= live < 91

    paused = client.post("/api/timer/pause").json()
    assert 90 <= paused["elapsed_seconds"] <= 91
    assert paused["running_since"] is None


def test_resume_and_stop_accumulate_and_stop_freezes_the_figure(client, run_for):
    start(client)
    run_for(90)
    client.post("/api/timer/pause")
    client.post("/api/timer/resume")
    run_for(30)

    final = client.post("/api/timer/stop").json()
    assert 120 <= final["elapsed_seconds"] <= 122
    assert final["state"] == "stopped"

    # Frozen: nothing is running, so a later read says the same.
    assert client.get("/api/timer").json()["elapsed_seconds"] == final["elapsed_seconds"]


def test_a_fraction_of_a_second_is_rounded_down(client, db):
    start(client)
    db.execute(text("UPDATE active_timer SET running_since = now() - interval '59.9 seconds'"))
    db.expire_all()
    assert client.post("/api/timer/pause").json()["elapsed_seconds"] == 59


def test_started_at_does_not_move_on_resume(client, run_for):
    created = start(client)
    run_for(30)
    client.post("/api/timer/pause")
    resumed = client.post("/api/timer/resume").json()
    assert resumed["started_at"] == created["started_at"]


# --- patching -----------------------------------------------------------------


def test_a_countdown_target_can_be_changed_but_not_cleared(client):
    post(client, "/api/timer", COUNTDOWN)

    response = client.patch("/api/timer", json={"target_seconds": None})
    assert response.status_code == 422, response.text

    response = client.patch("/api/timer", json={"target_seconds": 1800})
    assert response.status_code == 200, response.text
    assert response.json()["target_seconds"] == 1800


def test_a_stopwatch_cannot_be_given_a_target(client):
    start(client)
    response = client.patch("/api/timer", json={"target_seconds": 600})
    assert response.status_code == 422, response.text
    # The mirror: an empty patch on the same timer is fine.
    assert client.patch("/api/timer", json={}).status_code == 200


def test_the_mode_is_fixed_once_started(client):
    start(client)
    response = client.patch("/api/timer", json={"mode": "countdown"})
    assert response.status_code == 422, response.text


def test_a_stopped_timer_can_still_be_patched(client, run_for, practice):
    stopped(client, run_for)
    response = client.patch("/api/timer", json={"drill_id": practice["drill"]["id"]})
    assert response.status_code == 200, response.text
    assert response.json()["activity"]["drill"]["id"] == practice["drill"]["id"]


# --- the activity -------------------------------------------------------------


def test_a_timer_on_a_drill_shows_the_drill_and_its_exercise(client, practice):
    created = start(client, drill_id=practice["drill"]["id"])
    assert created["activity"] == {
        "exercise": {"id": practice["exercise"]["id"], "display_name": "人偶"},
        "drill": {"id": practice["drill"]["id"], "display_name": "骨架五步"},
    }


def test_a_timer_on_an_exercise_has_no_drill(client, practice):
    created = start(client, exercise_id=practice["exercise"]["id"])
    assert created["activity"] == {
        "exercise": {"id": practice["exercise"]["id"], "display_name": "人偶"},
        "drill": None,
    }


def test_a_timer_names_a_drill_or_an_exercise_not_both(client, practice):
    both = {"drill_id": practice["drill"]["id"], "exercise_id": practice["exercise"]["id"]}
    response = client.post("/api/timer", json={**STOPWATCH, **both})
    assert response.status_code == 422, response.text

    # PATCH is checked against the merged row: adding an exercise to a timer
    # on a drill is refused; swapping one for the other is not.
    start(client, drill_id=practice["drill"]["id"])
    response = client.patch("/api/timer", json={"exercise_id": practice["exercise"]["id"]})
    assert response.status_code == 422, response.text
    response = client.patch(
        "/api/timer", json={"drill_id": None, "exercise_id": practice["exercise"]["id"]}
    )
    assert response.status_code == 200, response.text
    assert response.json()["activity"]["drill"] is None


def test_unknown_activity_ids_are_422(client, practice):
    for body in ({"drill_id": 999999}, {"exercise_id": 999999}):
        response = client.post("/api/timer", json={**STOPWATCH, **body})
        assert response.status_code == 422, (body, response.text)
    assert client.get("/api/timer").json() is None


def test_deleting_the_drill_nulls_the_timers_activity(client, practice):
    start(client, drill_id=practice["drill"]["id"])
    assert client.get("/api/timer").json()["activity"] is not None

    assert client.delete(f"/api/drills/{practice['drill']['id']}").status_code == 204
    timer = client.get("/api/timer").json()
    assert timer is not None
    assert timer["activity"] is None


def test_deleting_the_exercise_nulls_the_timers_activity(client):
    exercise = create_exercise(client, name_cn="手")
    start(client, exercise_id=exercise["id"])
    assert client.get("/api/timer").json()["activity"] is not None

    assert client.delete(f"/api/exercises/{exercise['id']}").status_code == 204
    assert client.get("/api/timer").json()["activity"] is None


# --- saving it as a record ----------------------------------------------------


def test_saving_a_stopped_timer_creates_the_record_and_removes_the_timer(
    client, run_for, practice
):
    stopped(client, run_for, drill_id=practice["drill"]["id"])

    response = client.post(
        "/api/timer/record",
        json={"date": "2026-10-03", "duration_minutes": 25, "drill_id": practice["drill"]["id"]},
    )
    assert response.status_code == 201, response.text
    record = response.json()
    assert (record["date"], record["duration_minutes"]) == ("2026-10-03", 25)
    assert record["activity"]["drill"]["id"] == practice["drill"]["id"]

    assert client.get(f"/api/records/{record['id']}").json() == record
    assert client.get("/api/timer").json() is None


def test_a_refused_record_write_leaves_the_timer_intact(client, run_for, practice):
    before = stopped(client, run_for)

    for body in (
        # The record service's own rules, not a copy of them.
        {"drill_id": practice["drill"]["id"], "exercise_id": practice["exercise"]["id"]},
        {"drill_id": 999999},
        {"kind": "test"},
        {"duration_minutes": -1},
    ):
        response = client.post("/api/timer/record", json={"date": "2026-10-03", **body})
        assert response.status_code == 422, (body, response.text)
        assert client.get("/api/timer").json() == before, body
    assert client.get("/api/records").json() == []

    # The mirror: the same timer, a valid body.
    response = client.post("/api/timer/record", json={"date": "2026-10-03"})
    assert response.status_code == 201, response.text
    assert client.get("/api/timer").json() is None


def test_only_a_stopped_timer_is_saved_as_a_record(client):
    start(client)
    for _ in ("running", "paused"):
        response = client.post("/api/timer/record", json={"date": "2026-10-03"})
        assert response.status_code == 409, response.text
        client.post("/api/timer/pause")
    assert client.get("/api/records").json() == []
    assert client.get("/api/timer").json()["state"] == "paused"

    # The mirror.
    client.post("/api/timer/stop")
    assert client.post("/api/timer/record", json={"date": "2026-10-03"}).status_code == 201


# --- discarding ---------------------------------------------------------------


def test_discard_deletes_it_in_any_state(client):
    for prepare in ((), ("pause",), ("stop",)):
        start(client)
        for action in prepare:
            client.post(f"/api/timer/{action}")
        assert client.delete("/api/timer").status_code == 204, prepare
        assert client.get("/api/timer").json() is None


# --- the database -------------------------------------------------------------


def test_the_database_holds_at_most_one_timer(db):
    db.add(ActiveTimer(mode="stopwatch", running_since=dt.datetime.now(dt.UTC)))
    db.flush()  # the mirror: the first is accepted

    db.add(ActiveTimer(mode="stopwatch", running_since=dt.datetime.now(dt.UTC)))
    with pytest.raises(IntegrityError, match="uq_active_timer_single"):
        db.flush()


@pytest.mark.parametrize(
    ("fields", "constraint"),
    [
        ({"mode": "countdown"}, "ck_active_timer_target"),
        ({"mode": "stopwatch", "target_seconds": 60}, "ck_active_timer_target"),
        ({"mode": "countdown", "target_seconds": 0}, "ck_active_timer_target_positive"),
        ({"mode": "stopwatch", "elapsed_seconds": -1}, "ck_active_timer_elapsed_non_negative"),
        ({"mode": "interval"}, "ck_active_timer_mode"),
        (
            {"mode": "stopwatch", "running_since": "now", "stopped_at": "now"},
            "ck_active_timer_state",
        ),
    ],
)
def test_the_database_refuses_an_impossible_timer(db, fields, constraint):
    now = dt.datetime.now(dt.UTC)
    fields = {k: now if v == "now" else v for k, v in fields.items()}
    db.add(ActiveTimer(**fields))
    with pytest.raises(IntegrityError, match=constraint):
        db.flush()


def test_the_database_refuses_both_activities(db, client, practice):
    db.add(
        ActiveTimer(
            mode="stopwatch",
            drill_id=practice["drill"]["id"],
            exercise_id=practice["exercise"]["id"],
        )
    )
    with pytest.raises(IntegrityError, match="ck_active_timer_one_activity"):
        db.flush()
