# CLAUDE.md — Workout Tracker Project Guide

This file is the first thing Claude reads at the start of every session. Keep it up to date as the project evolves.

---

## Repository

- **GitHub:** https://github.com/shan9581/Final-Project
- **Local path:** `C:\Users\shani\Downloads\finalWorkoutProgram\Final-Project`
- **Default branch:** `main`
- **Remote:** `origin` → `https://github.com/shan9581/Final-Project`

Always work from inside `Final-Project/`. Push to `origin main` after every commit.

---

## What This Project Is

A workout tracker web application built as a learning project. The goal is to understand three-tier web architecture (database → server → browser client) by building something useful from scratch.

**Core features:**

- **Calendar-based logging** — home screen is a monthly calendar; click any date to log that day's workout. Dates with logged sets show a dot.
- **Workout split builder** — users create named training days (e.g. "Push Day"), assign exercises to each. My Split is structure-management only; all logging happens through the calendar.
- **Auto-save inputs** — weight and reps fields save automatically 600 ms after the user stops typing (no Log button). Revisiting a date pre-fills all inputs with previously logged values.
- **Quick Setup wizard** — recommends a split template (Push/Pull/Legs, Upper/Lower, Full Body, Bro Split) and sets rep ranges based on the user's goal (Strength or Hypertrophy).
- **Double progression engine** — add one rep per session until hitting the top of the rep range, then add weight and reset reps. Lives in pure Python with no DB calls.
- **Strength trend** — each session is reduced to an estimated 1RM using the Epley formula (`weight × (1 + reps/30)`), graphed over time per exercise.
- **CSV import** — import historical workout data via file upload or paste. Unknown exercises are created automatically.
- **Reset** — header button wipes all data from every table for a clean restart.

---

## Technology Stack

| Layer | Technology |
|---|---|
| Database | SQLite (single `workout.db` file, created automatically) |
| Server | Python 3 + Flask (REST API + static file serving) |
| Client | Plain HTML + CSS + JavaScript (`fetch()` calls, no build step) |
| Charts | Chart.js v4.4.3 (CDN) |
| Tests | pytest |

---

## File Layout

```
Final-Project/
├── CLAUDE.md                  ← this file
├── README.md
├── requirements.txt
├── workout.db                 ← SQLite DB (auto-created, not committed)
│
├── docs/
│   ├── ARCHITECTURE.md
│   ├── TESTING_PLAN.md        ← TDD plan with 32 labelled tests
│   ├── components.mmd
│   ├── data_flow.mmd
│   └── db_schema.mmd
│
├── server/
│   ├── app.py                 ← Flask routes / API endpoints (create_app factory)
│   ├── db.py                  ← SQLite helpers — no business logic
│   ├── recommendation.py      ← Pure functions: recommend(), epley_1rm(), build_trend()
│   ├── presets.py             ← Static data: PRESET_EXERCISES, SPLIT_TEMPLATES, REP_RANGES
│   └── schema.sql             ← CREATE TABLE statements (run on every DB connection)
│
├── client/
│   ├── index.html             ← Views: calendar, session, split, day, detail + modals
│   ├── style.css
│   └── app.js                 ← All frontend logic; SPLIT_TEMPLATES duplicated here for speed
│
└── tests/
    ├── conftest.py            ← pytest fixtures (in-memory DB, temp DB file)
    ├── test_recommendation.py ← Unit tests (U-01 … U-11)
    ├── test_api_contract.py   ← Contract tests (C-01 … C-14)
    └── test_integration.py    ← Integration tests (I-01 … I-07)
```

---

## Running the App

**Always run from `Final-Project/`:**

```bash
# Install dependencies (one-time)
python -m pip install -r requirements.txt

# Start the server
python -m flask --app server/app.py:create_app run
```

Then open **http://127.0.0.1:5000** in your browser.

> The app factory is `create_app` — use `server/app.py:create_app`, not just `server/app.py`.
> After any change to Python files, stop the server (Ctrl+C) and restart it. The auto-reloader does not always catch all changes.

---

## UI Navigation Flow

```
Calendar (home / view-calendar)
  └── Click a date  →  Session View (view-session)
        ├── No session yet: pick a workout day from your split
        └── Session exists: shows exercises with auto-save weight/reps inputs
              └── Click exercise name  →  Exercise Detail (view-detail)
                    └── Back  →  Session View

Header: "Import CSV" | "My Split" | "✕ Reset"

My Split (view-split)
  └── Click a day card  →  Day View (view-day)  [structure only, no logging]
        └── Click exercise name  →  Exercise Detail (view-detail)
  └── "Quick Setup"  →  Setup wizard modal (goal → template → creates days + exercises)
  └── "+ Add Day"    →  Add Day modal
```

---

## REST API Endpoints

### Exercises

| Method | URL | Description |
|---|---|---|
| GET | `/api/exercises` | List all exercises |
| POST | `/api/exercises` | Create an exercise |
| GET | `/api/exercises/<id>` | Get one exercise |
| GET | `/api/exercises/<id>/history` | All logged sets |
| POST | `/api/exercises/<id>/sets` | Append a set (used by import) |
| PUT | `/api/exercises/<id>/sets/<date>` | Upsert — replace set for this exercise+date (used by auto-save) |
| GET | `/api/exercises/<id>/recommendation` | Next-session recommendation |
| GET | `/api/exercises/<id>/trend` | Estimated 1RM over time |

### Workout Split

| Method | URL | Description |
|---|---|---|
| GET | `/api/workout-days` | List all workout days |
| POST | `/api/workout-days` | Create a day `{ name }` |
| DELETE | `/api/workout-days/<id>` | Delete a day (cascades to assignments) |
| GET | `/api/workout-days/<id>/exercises` | List exercises assigned to a day |
| POST | `/api/workout-days/<id>/exercises` | Add exercise to day — body: `{ exercise_id }` OR `{ name, rep_range_low, rep_range_high, weight_increment }` |
| DELETE | `/api/workout-days/<id>/exercises/<eid>` | Remove exercise from day |

### Setup & Presets

| Method | URL | Description |
|---|---|---|
| GET | `/api/presets` | List ~34 preset exercise names by category |
| GET | `/api/split-templates` | List split templates (PPL, Upper/Lower, etc.) |
| POST | `/api/setup` | Create a full split in one call — body: `{ goal, template }` |

### Sessions & Calendar

| Method | URL | Description |
|---|---|---|
| GET | `/api/sessions/<date>` | Get session + exercises for a date, or null |
| POST | `/api/sessions` | Create/replace session — body: `{ date, workout_day_id }` |
| GET | `/api/sessions/<date>/sets` | All sets logged on a date |
| GET | `/api/calendar/<year>/<month>` | List of dates with logged sets in that month |

### Utilities

| Method | URL | Description |
|---|---|---|
| POST | `/api/import` | Import CSV — body: `{ csv: "..." }` — returns `{ imported, errors }` |
| POST | `/api/reset` | Delete all data from every table |

All requests/responses use JSON. Errors return `{ "error": "..." }` with an appropriate HTTP status code. DELETE and reset routes return 204 with no body.

---

## Database Schema

**`exercises`** — `id`, `name`, `rep_range_low`, `rep_range_high`, `weight_increment`, `created_at`

**`sets`** — `id`, `exercise_id` (FK → exercises), `date` (YYYY-MM-DD), `weight`, `reps`, `logged_at`

**`workout_days`** — `id`, `name`, `position`, `created_at`

**`workout_day_exercises`** — `id`, `workout_day_id` (FK → workout_days, ON DELETE CASCADE), `exercise_id` (FK → exercises), `position`; UNIQUE(workout_day_id, exercise_id)

**`workout_sessions`** — `id`, `date` (UNIQUE), `workout_day_id` (FK → workout_days, ON DELETE CASCADE), `created_at`

Schema is applied via `db.executescript(schema.sql)` on every new connection, so new tables are created automatically on first run.

---

## Key db.py Functions

- `upsert_set(db, exercise_id, date, weight, reps)` — deletes all sets for that exercise+date, inserts one new row. Used by the auto-save PUT endpoint so editing replaces rather than accumulates.
- `reset_all_data(db)` — deletes all rows from sets, workout_sessions, workout_day_exercises, workout_days, exercises in dependency order.
- `get_or_create_exercise(db, name, ...)` — looks up by name, inserts if missing. Used by import and setup.
- `insert_session / get_session` — one session (workout type) per date; `INSERT OR REPLACE` semantics.
- `get_logged_dates_in_month(db, year, month)` — returns list of YYYY-MM-DD strings that have sets, used to draw calendar dots.

---

## CSV Import Format

```
date,exercise,weight,reps
2025-01-15,Bench Press,135,8
2025-01-15,Bench Press,145,6
2025-01-17,Squat,185,5
```

- `date` — YYYY-MM-DD
- `exercise` — any name; created automatically if it doesn't exist
- `weight` — lbs, decimals ok; use `0` for bodyweight
- `reps` — whole number
- Multiple rows per exercise per date are allowed (import uses `insert_set`, not `upsert_set`)

**Prompt to give Claude for formatting raw notes into this CSV:**

> Convert the following workout log into a CSV with exactly these four columns in this order: `date,exercise,weight,reps`. Rules: date must be YYYY-MM-DD; exercise names capitalized consistently; weight in pounds (numbers only, use 0 for bodyweight); reps as whole numbers; one row per set; output only the raw CSV with no explanation or code fences. My workout data: [paste here]

---

## server/presets.py

Three exports:

- **`PRESET_EXERCISES`** — list of `{ name, category }` dicts (~34 exercises across Push / Pull / Legs / Core)
- **`SPLIT_TEMPLATES`** — list of `{ id, name, description, days: [{ name, exercises[] }] }` — 4 templates: `ppl`, `upper_lower`, `full_body`, `bro_split`
- **`REP_RANGES`** — `{ "strength": { rep_range_low:3, rep_range_high:6, weight_increment:5.0 }, "hypertrophy": { ..., 8, 12, 2.5 } }`

`SPLIT_TEMPLATES` is also duplicated in `client/app.js` as a JS constant so the Quick Setup wizard renders instantly without a network call.

---

## The Recommendation Engine

Lives entirely in `server/recommendation.py`. Three pure functions:

- **`recommend(history, rep_range_low, rep_range_high, weight_increment)`** — returns `{ weight, reps, note }`. Uses the last session's best set (highest reps; ties broken by heaviest weight). If best reps ≥ rep_range_high → add weight, reset to rep_range_low. Otherwise → same weight, reps+1.
- **`epley_1rm(weight, reps)`** — returns `weight * (1 + reps / 30)`.
- **`build_trend(history)`** — returns `[{ date, estimated_1rm }, ...]`, one entry per unique date.

**Rule:** These functions must never make database calls or have side effects.

---

## Testing Approach

32 tests across three tiers. Run with: `pytest tests/ -v`

- **Unit** (`test_recommendation.py`) — pure functions only, no DB, no Flask
- **Contract** (`test_api_contract.py`) — Flask test client + in-memory SQLite; verifies response shapes
- **Integration** (`test_integration.py`) — Flask test client + real temp `.db` file; verifies full vertical slices

All 32 tests must pass before committing.

---

## Development Rules for Claude

1. **Keep `recommendation.py` pure.** Never add a database import or network call to that file.
2. **Commit after each logical unit of work** and push to `origin main`.
3. **Update this file** when the project structure, API, or key decisions change.
4. **Target explanations at early undergrad level** — prefer clear code over clever abstractions.
5. **No premature abstraction** — three similar lines beat a helper function that isn't needed yet.
6. **`SPLIT_TEMPLATES` lives in two places** — `server/presets.py` (source of truth for the API) and `client/app.js` (duplicate for instant rendering). Keep them in sync when editing templates.
7. **Always restart the Flask server** after Python file changes — the dev auto-reloader does not always catch everything.
8. **Logging only through the calendar** — My Split (view-split / view-day) is structure management only. Never add log forms there.
9. **Auto-save uses upsert** — the session log uses `PUT /api/exercises/<id>/sets/<date>` (one set per exercise per date). Import uses `POST` (multiple sets allowed). Don't conflate the two.

---

## Current Status

| Milestone | Status |
|---|---|
| Architecture docs + Mermaid diagrams | Done |
| Testing plan (32 tests) | Done |
| Test files (conftest + 3 test modules) | Done |
| `server/schema.sql` | Done |
| `server/db.py` | Done |
| `server/recommendation.py` | Done |
| `server/app.py` | Done |
| `server/presets.py` | Done |
| `client/` (HTML, CSS, JS) | Done |
| `requirements.txt` / `README.md` | Done |
| Workout split builder (day-based logging) | Done |
| Quick Setup wizard (goal + split template) | Done |
| Preset exercise library + exercise picker | Done |
| Calendar-based UI (date → pick day → log sets) | Done |
| Auto-save inputs with pre-fill on revisit | Done |
| CSV import (file upload or paste) | Done |
| Reset button (clear all data) | Done |
