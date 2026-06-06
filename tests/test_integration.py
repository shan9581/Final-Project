"""Integration tests — full vertical slices with a real temporary SQLite file."""
import pytest
from server.app import create_app


@pytest.fixture
def int_client(db_path):
    """Flask test client backed by a real SQLite file."""
    app = create_app({"DATABASE": db_path, "TESTING": True})
    return app.test_client()


def _create_exercise(client, name="Squat", low=5, high=8, increment=5.0):
    r = client.post("/api/exercises", json={
        "name": name, "rep_range_low": low,
        "rep_range_high": high, "weight_increment": increment,
    })
    return r.get_json()["id"]


def _log_set(client, ex_id, date, weight, reps):
    return client.post(f"/api/exercises/{ex_id}/sets",
                       json={"date": date, "weight": weight, "reps": reps})


def test_I01_created_exercise_appears_in_list(int_client):
    """I-01: Create exercise → GET list includes it."""
    _create_exercise(int_client, "Deadlift")
    exercises = int_client.get("/api/exercises").get_json()
    assert any(e["name"] == "Deadlift" for e in exercises)


def test_I02_logged_set_appears_in_history(int_client):
    """I-02: Log set → GET history includes it."""
    ex_id = _create_exercise(int_client)
    _log_set(int_client, ex_id, "2026-06-01", 100, 6)
    history = int_client.get(f"/api/exercises/{ex_id}/history").get_json()
    assert len(history) == 1
    assert history[0]["weight"] == 100
    assert history[0]["reps"] == 6


def test_I03_recommendation_after_ceiling_adds_weight(int_client):
    """I-03: Log at ceiling → recommendation weight = logged weight + increment."""
    ex_id = _create_exercise(int_client, low=5, high=8, increment=5.0)
    _log_set(int_client, ex_id, "2026-06-01", 100, 8)  # at ceiling
    rec = int_client.get(f"/api/exercises/{ex_id}/recommendation").get_json()
    assert rec["weight"] == 105.0
    assert rec["target_reps"] == 5


def test_I04_recommendation_below_ceiling_adds_rep(int_client):
    """I-04: Log below ceiling → same weight, reps+1."""
    ex_id = _create_exercise(int_client, low=5, high=8, increment=5.0)
    _log_set(int_client, ex_id, "2026-06-01", 100, 6)
    rec = int_client.get(f"/api/exercises/{ex_id}/recommendation").get_json()
    assert rec["weight"] == 100.0
    assert rec["target_reps"] == 7


def test_I05_trend_has_one_entry_per_date_sorted(int_client):
    """I-05: Sets on 3 different dates → trend has 3 items in ascending order."""
    ex_id = _create_exercise(int_client)
    for date, w, r in [("2026-06-01", 100, 5), ("2026-06-08", 100, 6), ("2026-06-15", 105, 5)]:
        _log_set(int_client, ex_id, date, w, r)
    trend = int_client.get(f"/api/exercises/{ex_id}/trend").get_json()
    assert len(trend) == 3
    dates = [t["date"] for t in trend]
    assert dates == sorted(dates)


def test_I06_no_history_recommendation_has_note(int_client):
    """I-06: No history → recommendation returns no-history note."""
    ex_id = _create_exercise(int_client)
    rec = int_client.get(f"/api/exercises/{ex_id}/recommendation").get_json()
    assert rec["weight"] == 0
    assert isinstance(rec["note"], str) and len(rec["note"]) > 0


def test_I07_exercise_data_isolation(int_client):
    """I-07: Sets for one exercise don't appear in another's history."""
    ex1 = _create_exercise(int_client, "Bench Press")
    ex2 = _create_exercise(int_client, "Overhead Press")
    _log_set(int_client, ex1, "2026-06-01", 100, 6)
    history2 = int_client.get(f"/api/exercises/{ex2}/history").get_json()
    assert len(history2) == 0
