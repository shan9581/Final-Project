# Workout Tracker

A progressive-overload workout tracker built with Flask + SQLite + plain HTML/CSS/JS. Log your sets on a calendar, get smart weight/rep recommendations, import historical data, and track your progress with a full stats dashboard.

## Features

- **Calendar-based logging** — home screen is a monthly calendar; click any date to log that day's workout. Dates with logged sets show a dot.
- **Workout split builder** — create named training days (e.g. "Push Day"), assign exercises to each. Quick Setup wizard generates a full split from a template in two clicks.
- **Auto-save inputs** — weight and reps save automatically 600 ms after you stop typing. Revisiting a date pre-fills all inputs with previously logged values.
- **Double progression engine** — hit the top of your rep range → add weight and reset reps. Otherwise → same weight, one more rep. Runs as pure Python with no database calls.
- **Strength trend** — each session is reduced to an estimated 1RM using the Epley formula (`weight × (1 + reps/30)`), graphed over time per exercise.
- **CSV import** — import historical workout data via file upload or paste. Unknown exercises are created automatically. Imported dates appear on the calendar like any other session.
- **Stats page** — four sections:
  - **Strength Progression** — personal records table, estimated 1RM trend chart, recent PRs (last 4 weeks)
  - **Volume** — weekly volume bar chart, working sets per week, volume by muscle group (doughnut)
  - **Consistency** — current/longest streak, workouts per week, GitHub-style activity heatmap
  - **Diagnostics** — stalled lifts, muscle balance, exercise frequency
- **Reset** — wipe all data for a clean start.

## Tech Stack

| Layer | Technology |
|---|---|
| Database | SQLite (auto-created `workout.db`) |
| Server | Python 3 + Flask |
| Client | HTML + CSS + JavaScript (no build step) |
| Charts | Chart.js v4.4.3 |
| Tests | pytest (32 tests) |

## Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Start the server (run from the Final-Project/ directory)
python -m flask --app server/app.py:create_app run
```

Then open **http://127.0.0.1:5000** in your browser.

## Run Tests

```bash
pytest tests/ -v
```

All 32 tests should pass.

## CSV Import Format

To import historical workout data, use a CSV with these four columns:

```
date,exercise,weight,reps
2025-01-15,Bench Press,135,8
2025-01-15,Squat,185,5
2025-01-17,Deadlift,225,3
```

- `date` — YYYY-MM-DD
- `exercise` — any name; new exercises are created automatically
- `weight` — lbs (use `0` for bodyweight exercises)
- `reps` — whole number

**Prompt to convert raw notes to this format (give to any AI):**
> Convert the following workout log into a CSV with exactly these four columns in this order: `date,exercise,weight,reps`. Rules: date must be YYYY-MM-DD; exercise names capitalized consistently; weight in pounds (numbers only, use 0 for bodyweight); reps as whole numbers; one row per set; output only the raw CSV with no explanation or code fences. My workout data: [paste here]

## How Progression Works

The double progression engine lives in `server/recommendation.py`:

1. Look at the last session's best set (highest reps; ties broken by heaviest weight).
2. If reps ≥ rep range ceiling → add `weight_increment` lbs, reset to rep range floor.
3. Otherwise → same weight, reps + 1.

Rep ranges and weight increments are set per exercise. The Quick Setup wizard sets these automatically based on your goal (Strength: 3–6 reps, +5 lb; Hypertrophy: 8–12 reps, +2.5 lb).

## Project Structure

```
Final-Project/
├── server/
│   ├── app.py           — Flask routes / REST API
│   ├── db.py            — SQLite helpers
│   ├── recommendation.py — Double progression engine (pure functions)
│   ├── stats.py         — Statistics functions (pure functions)
│   ├── presets.py       — Preset exercises and split templates
│   └── schema.sql       — Database schema
├── client/
│   ├── index.html       — All views and modals
│   ├── style.css
│   └── app.js           — All frontend logic
└── tests/
    ├── conftest.py
    ├── test_recommendation.py
    ├── test_api_contract.py
    └── test_integration.py
```
