"""Building the rows a test needs over HTTP, so every test file says the same
thing the same way. Each asserts its own status, so a setup that fails is
reported as the setup, not as the assertion after it."""


def post(client, path: str, body: dict) -> dict:
    response = client.post(path, json=body)
    assert response.status_code == 201, (path, response.text)
    return response.json()


def create_goal(client, code="L0", **body):
    body.setdefault("name_cn", code)
    return post(client, "/api/goals", {"code": code, **body})


def create_stage(client, goal_id, **body):
    body.setdefault("name_cn", "線條")
    return post(client, "/api/stages", {"goal_id": goal_id, **body})


def create_exercise(client, **body):
    body.setdefault("name_cn", "線條")
    return post(client, "/api/exercises", body)


def create_drill(client, exercise_id, **body):
    return post(client, "/api/drills", {"exercise_id": exercise_id, **body})


def create_record(client, **body):
    body.setdefault("date", "2026-10-03")
    return post(client, "/api/records", body)
