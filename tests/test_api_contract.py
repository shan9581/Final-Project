"""Contract tests — verify HTTP status codes and JSON response shapes.

Uses Flask test client + in-memory SQLite. Does NOT check exact values,
only that the right keys exist and types are correct.
"""
import pytest


# ── Helpers ───────────────────────────────────────────────────────────────────

def create_exercise(client, name="Bench Press", low=5, high=8, increment=5.0):
    return client.post("/api/exercises", json={
        "name": name,
        "rep_range_low": low,
        "rep_range_high": high,
        "weight_increment": increment,
    })


def log_set(client, exercise_id, date="2026-06-01", weight=100.0, reps=6):
    return client.post(f"/api/exercises/{exercise_id}/sets", json={
        "date": date, "weight": weight, "reps": reps,
    })


# ── Exercises ─────────────────────────────────────────────────────────────────

def test_C01_list_exercises_returns_200_array(client):
    """C-01: GET /api/exercises → 200, JSON array."""
    r = client.get("/api/exercises")
    assert r.status_code == 200
    assert isinstance(r.get_json(), list)


def test_C02_list_exercises_item_shape(client):
    """C-02: Each exercise has the required keys."""
    create_exercise(client)
    r = client.get("/api/exercises")
    item = r.get_json()[0]
    for key in ("id", "name", "rep_range_low", "rep_range_high", "weight_increment"):
        assert key in item, f"Missing key: {key}"


def test_C03_create_exercise_returns_201_with_id(client):
    """C-03: POST /api/exercises valid → 201, includes id."""
    r = create_exercise(client)
    assert r.status_code == 201
    body = r.get_json()
    assert "id" in body
    assert body["name"] == "Bench Press"


def test_C04_create_exercise_missing_name_returns_400(client):
    """C-04: POST /api/exercises missing name → 400 with error key."""
    r = client.post("/api/exercises", json={"rep_range_low": 5})
    assert r.status_code == 400
    assert "error" in r.get_json()


def test_C05_get_nonexistent_exercise_returns_404(client):
    """C-05: GET /api/exercises/99999 → 404 with error key."""
    r = client.get("/api/exercises/99999")
    assert r.status_code == 404
    assert "error" in r.get_json()


# ── Sets ──────────────────────────────────────────────────────────────────────

def test_C06_log_set_returns_201_with_shape(client):
    """C-06: POST /api/exercises/<id>/sets valid → 201, required keys present."""
    create_exercise(client)
    ex_id = client.get("/api/exercises").get_json()[0]["id"]
    r = log_set(client, ex_id)
    assert r.status_code == 201
    body = r.get_json()
    for key in ("id", "exercise_id", "date", "weight", "reps"):
        assert key in body, f"Missing key: {key}"


def test_C07_log_set_missing_weight_returns_400(client):
    """C-07: POST sets missing weight → 400."""
    create_exercise(client)
    ex_id = client.get("/api/exercises").get_json()[0]["id"]
    r = client.post(f"/api/exercises/{ex_id}/sets", json={"date": "2026-06-01", "reps": 5})
    assert r.status_code == 400


def test_C08_log_set_missing_reps_returns_400(client):
    """C-08: POST sets missing reps → 400."""
    create_exercise(client)
    ex_id = client.get("/api/exercises").get_json()[0]["id"]
    r = client.post(f"/api/exercises/{ex_id}/sets", json={"date": "2026-06-01", "weight": 100})
    assert r.status_code == 400


def test_C09_log_set_missing_date_returns_400(client):
    """C-09: POST sets missing date → 400."""
    create_exercise(client)
    ex_id = client.get("/api/exercises").get_json()[0]["id"]
    r = client.post(f"/api/exercises/{ex_id}/sets", json={"weight": 100, "reps": 5})
    assert r.status_code == 400


def test_C10_history_returns_200_array_with_shape(client):
    """C-10: GET history → 200, array where each item has date/weight/reps."""
    create_exercise(client)
    ex_id = client.get("/api/exercises").get_json()[0]["id"]
    log_set(client, ex_id)
    r = client.get(f"/api/exercises/{ex_id}/history")
    assert r.status_code == 200
    item = r.get_json()[0]
    for key in ("date", "weight", "reps"):
        assert key in item


# ── Recommendation ────────────────────────────────────────────────────────────

def test_C11_recommendation_returns_200_with_shape(client):
    """C-11: GET recommendation → 200, has weight/target_reps/note."""
    create_exercise(client)
    ex_id = client.get("/api/exercises").get_json()[0]["id"]
    log_set(client, ex_id)
    r = client.get(f"/api/exercises/{ex_id}/recommendation")
    assert r.status_code == 200
    body = r.get_json()
    for key in ("weight", "target_reps", "note"):
        assert key in body


def test_C12_recommendation_no_history_has_note(client):
    """C-12: Recommendation with no history → note is non-empty string."""
    create_exercise(client)
    ex_id = client.get("/api/exercises").get_json()[0]["id"]
    r = client.get(f"/api/exercises/{ex_id}/recommendation")
    assert r.status_code == 200
    note = r.get_json().get("note", "")
    assert isinstance(note, str) and len(note) > 0


# ── Trend ─────────────────────────────────────────────────────────────────────

def test_C13_trend_returns_200_array(client):
    """C-13: GET trend → 200, JSON array."""
    create_exercise(client)
    ex_id = client.get("/api/exercises").get_json()[0]["id"]
    r = client.get(f"/api/exercises/{ex_id}/trend")
    assert r.status_code == 200
    assert isinstance(r.get_json(), list)


def test_C14_trend_item_shape(client):
    """C-14: Each trend item has date (string) and estimated_1rm (number)."""
    create_exercise(client)
    ex_id = client.get("/api/exercises").get_json()[0]["id"]
    log_set(client, ex_id)
    r = client.get(f"/api/exercises/{ex_id}/trend")
    item = r.get_json()[0]
    assert isinstance(item["date"], str)
    assert isinstance(item["estimated_1rm"], (int, float))
