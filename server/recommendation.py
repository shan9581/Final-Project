"""Pure functions for weight recommendation and strength trend.

No database calls, no side effects — all inputs are plain Python dicts/lists.
"""


def epley_1rm(weight, reps):
    """Estimate one-rep max using the Epley formula."""
    return round(weight * (1 + reps / 30), 2)


def build_trend(history):
    """Return one {date, estimated_1rm} entry per unique date, sorted ascending.

    For each date, use the set that produces the highest estimated 1RM.
    history: list of {date, weight, reps} dicts.
    """
    if not history:
        return []

    best_per_date = {}
    for s in history:
        orm = epley_1rm(s["weight"], s["reps"])
        if s["date"] not in best_per_date or orm > best_per_date[s["date"]]:
            best_per_date[s["date"]] = orm

    return [
        {"date": date, "estimated_1rm": orm}
        for date, orm in sorted(best_per_date.items())
    ]


def recommend(history, rep_range_low, rep_range_high, weight_increment):
    """Return the recommended weight and reps for the next session.

    Uses double progression:
      - Below rep ceiling → same weight, add one rep.
      - At or above ceiling → add weight_increment, reset to rep_range_low.

    history: list of {date, weight, reps} dicts (any order).
    Returns: {weight, reps, note}
    """
    if not history:
        return {
            "weight": 0,
            "reps": rep_range_low,
            "note": "No history yet — log your first set to get a recommendation.",
        }

    last_date = max(s["date"] for s in history)
    last_sets = [s for s in history if s["date"] == last_date]

    best = max(last_sets, key=lambda s: (s["reps"], s["weight"]))

    if best["reps"] >= rep_range_high:
        new_weight = best["weight"] + weight_increment
        return {
            "weight": new_weight,
            "reps": rep_range_low,
            "note": f"Great work hitting {best['reps']} reps! Adding weight.",
        }
    else:
        return {
            "weight": best["weight"],
            "reps": best["reps"] + 1,
            "note": f"Keep pushing — aim for one more rep than last time.",
        }
