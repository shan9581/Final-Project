"""Unit tests for server/recommendation.py — no database, no Flask."""
import pytest
from server.recommendation import recommend, epley_1rm, build_trend


# ── Helpers ──────────────────────────────────────────────────────────────────

def make_set(date, weight, reps):
    return {"date": date, "weight": weight, "reps": reps}


# ── epley_1rm ─────────────────────────────────────────────────────────────────

def test_U07_epley_standard():
    """U-07: epley_1rm(100, 5) == 116.67"""
    assert epley_1rm(100, 5) == 116.67


def test_U08_epley_single_rep():
    """U-08: epley_1rm(100, 1) == 103.33"""
    assert epley_1rm(100, 1) == 103.33


# ── recommend ────────────────────────────────────────────────────────────────

def test_U01_empty_history():
    """U-01: Empty history → weight=0, reps=rep_range_low, note is non-empty string."""
    result = recommend([], rep_range_low=5, rep_range_high=8, weight_increment=5.0)
    assert result["weight"] == 0
    assert result["reps"] == 5
    assert isinstance(result["note"], str) and len(result["note"]) > 0


def test_U02_below_ceiling_adds_rep():
    """U-02: Last session below ceiling → same weight, reps+1."""
    history = [make_set("2026-06-01", 100, 6)]
    result = recommend(history, rep_range_low=5, rep_range_high=8, weight_increment=5.0)
    assert result["weight"] == 100
    assert result["reps"] == 7


def test_U03_at_ceiling_adds_weight():
    """U-03: Last session at ceiling → weight+increment, reset to rep_range_low."""
    history = [make_set("2026-06-01", 100, 8)]
    result = recommend(history, rep_range_low=5, rep_range_high=8, weight_increment=5.0)
    assert result["weight"] == 105
    assert result["reps"] == 5


def test_U04_multiple_sets_uses_highest_reps():
    """U-04: Multiple sets on last date → use set with highest reps."""
    history = [
        make_set("2026-06-01", 100, 5),
        make_set("2026-06-01", 100, 7),
        make_set("2026-06-01", 100, 6),
    ]
    result = recommend(history, rep_range_low=5, rep_range_high=8, weight_increment=5.0)
    assert result["reps"] == 8  # 7 + 1


def test_U05_tie_broken_by_heavier_weight():
    """U-05: Equal reps → use heavier weight to determine best set."""
    history = [
        make_set("2026-06-01", 95, 7),
        make_set("2026-06-01", 100, 7),
    ]
    result = recommend(history, rep_range_low=5, rep_range_high=8, weight_increment=5.0)
    assert result["weight"] == 100
    assert result["reps"] == 8


def test_U06_only_uses_last_date():
    """U-06: Older sessions ignored; only the most recent date is used."""
    history = [
        make_set("2026-05-01", 120, 8),  # old session — at ceiling, heavy
        make_set("2026-06-01", 80, 5),   # recent session — below ceiling
    ]
    result = recommend(history, rep_range_low=5, rep_range_high=8, weight_increment=5.0)
    # Must be based on the 2026-06-01 set, not the 2026-05-01 set
    assert result["weight"] == 80
    assert result["reps"] == 6


# ── build_trend ───────────────────────────────────────────────────────────────

def test_U09_trend_one_entry_per_date():
    """U-09: build_trend returns one dict per unique date with 'date' and 'estimated_1rm'."""
    history = [
        make_set("2026-06-01", 100, 5),
        make_set("2026-06-08", 100, 6),
    ]
    trend = build_trend(history)
    assert len(trend) == 2
    for entry in trend:
        assert "date" in entry
        assert "estimated_1rm" in entry


def test_U10_trend_picks_best_1rm_per_day():
    """U-10: build_trend picks the set with the highest 1RM for each date."""
    history = [
        make_set("2026-06-01", 100, 3),   # 1RM ≈ 110.0
        make_set("2026-06-01", 100, 8),   # 1RM ≈ 126.67  ← should win
    ]
    trend = build_trend(history)
    assert len(trend) == 1
    assert trend[0]["estimated_1rm"] == epley_1rm(100, 8)


def test_U11_trend_empty_history():
    """U-11: build_trend([]) returns empty list without raising."""
    assert build_trend([]) == []
