"""Pure functions for workout statistics. No DB calls, no Flask imports."""
from datetime import date, timedelta
from collections import defaultdict


def epley_1rm(weight, reps):
    if reps <= 0:
        return 0.0
    return float(weight) * (1 + reps / 30)


def _week_start(d):
    """Monday of the week containing date d."""
    return d - timedelta(days=d.weekday())


def _last_n_week_starts(n):
    """List of Monday dates for the last n weeks, oldest first."""
    today = date.today()
    return [_week_start(today) - timedelta(weeks=i) for i in range(n - 1, -1, -1)]


# ── Strength ──────────────────────────────────────────────────────────────────

def compute_prs(history):
    """
    history: [{date, weight, reps}, ...]
    Returns personal record dict, or None if history is empty.
    """
    if not history:
        return None
    best_weight = best_weight_date = None
    best_1rm = 0.0
    best_1rm_date = None
    best_reps = 0
    best_reps_weight = best_reps_date = None

    for s in history:
        w, r, d = float(s["weight"]), int(s["reps"]), s["date"]
        orm = epley_1rm(w, r)
        if best_weight is None or w > best_weight:
            best_weight, best_weight_date = w, d
        if orm > best_1rm:
            best_1rm, best_1rm_date = orm, d
        if r > best_reps:
            best_reps, best_reps_weight, best_reps_date = r, w, d

    return {
        "best_weight":      best_weight,
        "best_weight_date": best_weight_date,
        "best_1rm":         round(best_1rm, 1),
        "best_1rm_date":    best_1rm_date,
        "best_reps":        best_reps,
        "best_reps_weight": best_reps_weight,
        "best_reps_date":   best_reps_date,
    }


def compute_1rm_trend(history):
    """Best estimated 1RM per calendar date, sorted chronologically."""
    by_date = defaultdict(float)
    for s in history:
        orm = epley_1rm(float(s["weight"]), int(s["reps"]))
        if orm > by_date[s["date"]]:
            by_date[s["date"]] = orm
    return [{"date": d, "estimated_1rm": round(v, 1)} for d, v in sorted(by_date.items())]


def compute_recent_prs(exercises_history, days=28):
    """
    Returns PRs whose all-time-best date falls within the last `days` days.
    exercises_history: [{id, name, history: [...]}]
    """
    cutoff = (date.today() - timedelta(days=days)).isoformat()
    recent = []
    for ex in exercises_history:
        prs = compute_prs(ex["history"])
        if not prs:
            continue
        if prs["best_weight_date"] and prs["best_weight_date"] >= cutoff:
            recent.append({
                "exercise": ex["name"],
                "pr_type":  "Weight PR",
                "value":    f'{prs["best_weight"]} lbs',
                "date":     prs["best_weight_date"],
            })
        # Show 1RM PR only when it falls on a different date than weight PR
        if (prs["best_1rm_date"] and prs["best_1rm_date"] >= cutoff
                and prs["best_1rm_date"] != prs["best_weight_date"]):
            recent.append({
                "exercise": ex["name"],
                "pr_type":  "Est. 1RM PR",
                "value":    f'{prs["best_1rm"]} lbs',
                "date":     prs["best_1rm_date"],
            })
    return sorted(recent, key=lambda x: x["date"], reverse=True)


# ── Volume ────────────────────────────────────────────────────────────────────

def compute_weekly_volume(all_sets, num_weeks=12):
    """Total lbs lifted (weight × reps) per week for last num_weeks weeks."""
    weeks = _last_n_week_starts(num_weeks)
    by_week = defaultdict(float)
    for s in all_sets:
        by_week[_week_start(date.fromisoformat(s["date"]))] += float(s["weight"]) * int(s["reps"])
    return [{"week": ws.isoformat(), "volume": round(by_week.get(ws, 0), 1)} for ws in weeks]


def compute_working_sets_per_week(all_sets, num_weeks=12):
    """Number of logged sets per week for last num_weeks weeks."""
    weeks = _last_n_week_starts(num_weeks)
    by_week = defaultdict(int)
    for s in all_sets:
        by_week[_week_start(date.fromisoformat(s["date"]))] += 1
    return [{"week": ws.isoformat(), "sets": by_week.get(ws, 0)} for ws in weeks]


def compute_category_totals(all_sets_with_category, num_weeks=12):
    """
    Total volume per muscle group category over last num_weeks weeks.
    Sets without a category are counted separately as uncategorized.
    Returns {"totals": {cat: volume}, "uncategorized_count": N}
    """
    cutoff = (_week_start(date.today()) - timedelta(weeks=num_weeks)).isoformat()
    totals = defaultdict(float)
    uncategorized = 0
    for s in all_sets_with_category:
        if s["date"] < cutoff:
            continue
        cat = s.get("category")
        if cat:
            totals[cat] += float(s["weight"]) * int(s["reps"])
        else:
            uncategorized += 1
    return {"totals": dict(totals), "uncategorized_count": uncategorized}


# ── Consistency ───────────────────────────────────────────────────────────────

def compute_streaks(session_dates):
    """
    Consecutive-day streaks from a list of YYYY-MM-DD session dates.
    Allows a 1-day gap if today hasn't been logged yet.
    """
    if not session_dates:
        return {"current_streak": 0, "longest_streak": 0}

    dates = sorted(set(date.fromisoformat(d) for d in session_dates))
    longest = cur = 1
    for i in range(1, len(dates)):
        if (dates[i] - dates[i - 1]).days == 1:
            cur += 1
            longest = max(longest, cur)
        else:
            cur = 1

    today = date.today()
    date_set = set(dates)
    current = 0
    check = today if today in date_set else today - timedelta(days=1)
    while check in date_set:
        current += 1
        check -= timedelta(days=1)

    return {"current_streak": current, "longest_streak": longest}


def compute_workouts_per_week(session_dates, num_weeks=12):
    """Number of sessions per week for last num_weeks weeks."""
    weeks = _last_n_week_starts(num_weeks)
    by_week = defaultdict(int)
    for d in session_dates:
        by_week[_week_start(date.fromisoformat(d))] += 1
    return [{"week": ws.isoformat(), "count": by_week.get(ws, 0)} for ws in weeks]


def compute_heatmap(session_dates, num_weeks=52):
    """
    One entry per calendar day for the last num_weeks weeks.
    count is 1 if a session was logged that day, else 0.
    """
    today = date.today()
    start = _week_start(today) - timedelta(weeks=num_weeks - 1)
    date_set = set(session_dates)
    result = []
    d = start
    while d <= today:
        result.append({"date": d.isoformat(), "count": 1 if d.isoformat() in date_set else 0})
        d += timedelta(days=1)
    return result


# ── Diagnostics ───────────────────────────────────────────────────────────────

def compute_stalled_lifts(exercises_history, weeks=4):
    """
    Exercises with less than 1% estimated-1RM improvement over last `weeks` weeks.
    Requires at least one session both before and within the window.
    """
    cutoff = (date.today() - timedelta(weeks=weeks)).isoformat()
    stalled = []
    for ex in exercises_history:
        h = ex["history"]
        pre  = [s for s in h if s["date"] <  cutoff]
        post = [s for s in h if s["date"] >= cutoff]
        if not pre or not post:
            continue
        best_before = max(epley_1rm(float(s["weight"]), int(s["reps"])) for s in pre)
        best_after  = max(epley_1rm(float(s["weight"]), int(s["reps"])) for s in post)
        if best_after < best_before * 1.01:
            stalled.append({
                "exercise":    ex["name"],
                "current_1rm": round(best_after, 1),
                "last_date":   max(s["date"] for s in post),
            })
    return sorted(stalled, key=lambda x: x["exercise"])


def compute_muscle_balance(all_sets_with_category, num_weeks=4):
    """
    Volume share per category for last num_weeks weeks.
    Excludes uncategorized sets so percentages sum to 100 over known groups.
    """
    cutoff = (_week_start(date.today()) - timedelta(weeks=num_weeks)).isoformat()
    by_cat = defaultdict(float)
    for s in all_sets_with_category:
        cat = s.get("category")
        if cat and s["date"] >= cutoff:
            by_cat[cat] += float(s["weight"]) * int(s["reps"])
    total = sum(by_cat.values())
    if total == 0:
        return {}
    return {
        cat: {"volume": round(vol, 1), "pct": round(vol / total * 100, 1)}
        for cat, vol in sorted(by_cat.items(), key=lambda x: -x[1])
    }


def compute_exercise_frequency(exercises_history, num_weeks=4):
    """Sessions per week for each exercise trained in the last num_weeks weeks."""
    cutoff = (date.today() - timedelta(weeks=num_weeks)).isoformat()
    result = []
    for ex in exercises_history:
        dates_in = set(s["date"] for s in ex["history"] if s["date"] >= cutoff)
        if dates_in:
            result.append({
                "exercise": ex["name"],
                "sessions": len(dates_in),
                "per_week": round(len(dates_in) / num_weeks, 1),
            })
    return sorted(result, key=lambda x: -x["per_week"])
