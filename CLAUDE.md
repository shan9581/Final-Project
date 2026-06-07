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

- **Workout split builder** — users create named training days (e.g. "Push Day"), assign exercises to each, and log sets day by day.
- **Quick Setup wizard** — recommends a split template (Push/Pull/Legs, Upper/Lower, Full Body, Bro Split) and sets rep ranges based on the user's goal (Strength or Hypertrophy).
- **Double progression engine** — add one rep per session until hitting the top of the rep range, then add weight and reset reps. Lives in pure Python with no DB calls.
- **Strength trend** — each session is reduced to an estimated 1RM using the Epley formula (`weight × (1 + reps/30)`), graphed over time per exercise.

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
│   ├── index.html             ← Three views: split home, day view, exercise detail
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
Split Home (view-split)
  └── Click a day card  →  Day View (view-day)
        └── Click exercise name  →  Exercise Detail (view-detail)
              └── Back button  →  Day View
  └── "Quick Setup"  →  Setup wizard modal (goal → template → creates days + exercises)
  └── "+ Add Day"    →  Add Day modal
```

---

## REST API Endpoints

### Exercises (original)

| Method | URL | Description |
|---|---|---|
| GET | `/api/exercises` | List all exercises |
| POST | `/api/exercises` | Create an exercise |
| GET | `/api/exercises/<id>` | Get one exercise |
| GET | `/api/exercises/<id>/history` | All logged sets |
| POST | `/api/exercises/<id>/sets` | Log a set |
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

All requests/responses use JSON. Errors return `{ "error": "..." }` with an appropriate HTTP status code. DELETE routes return 204 with no body.

---

## Database Schema

**`exercises`** — `id`, `name`, `rep_range_low`, `rep_range_high`, `weight_increment`, `created_at`

**`sets`** — `id`, `exercise_id` (FK → exercises), `date` (YYYY-MM-DD), `weight`, `reps`, `logged_at`

**`workout_days`** — `id`, `name`, `position`, `created_at`

**`workout_day_exercises`** — `id`, `workout_day_id` (FK → workout_days, ON DELETE CASCADE), `exercise_id` (FK → exercises), `position`; UNIQUE(workout_day_id, exercise_id)

Schema is applied via `db.executescript(schema.sql)` on every new connection, so new tables are created automatically on first run.

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
