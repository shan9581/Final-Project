# CLAUDE.md — Workout Tracker Project Guide

This file is the first thing Claude reads at the start of every session. Keep it up to date as the project evolves.

---

## What This Project Is

A workout tracker web application built as a learning project. The goal is to understand three-tier web architecture (database → server → browser client) by building something useful from scratch.

**Core feature:** A weight-recommendation engine that uses *double progression* — add one rep per session until you hit the top of a rep range, then add weight and reset reps. The engine is a pure Python function (no database calls inside it) so it can be unit-tested in isolation.

**Strength trend:** Each session is reduced to an estimated one-rep max using the Epley formula (`1RM = weight × (1 + reps/30)`), enabling a per-exercise strength trend over time.

---

## Technology Stack

| Layer | Technology |
|---|---|
| Database | SQLite (single `.db` file) |
| Server | Python 3 + Flask (REST API) |
| Client | Plain HTML + CSS + JavaScript (`fetch()` calls) |
| Tests | pytest |

---

## File Layout

```
Final-Project/
├── CLAUDE.md                  ← this file
├── README.md
├── requirements.txt
│
├── docs/
│   ├── ARCHITECTURE.md        ← full architecture explanation (undergrad-level)
│   ├── TESTING_PLAN.md        ← TDD plan with 32 labelled tests
│   ├── components.mmd         ← Mermaid component diagram
│   ├── data_flow.mmd          ← Mermaid sequence diagram
│   └── db_schema.mmd          ← Mermaid ER diagram
│
├── server/
│   ├── app.py                 ← Flask routes / API endpoints
│   ├── db.py                  ← SQLite helpers (no business logic)
│   ├── recommendation.py      ← Pure functions: recommend(), epley_1rm(), build_trend()
│   └── schema.sql             ← CREATE TABLE statements
│
├── client/
│   ├── index.html
│   ├── style.css
│   └── app.js
│
└── tests/
    ├── conftest.py            ← pytest fixtures (in-memory DB, temp DB file)
    ├── test_recommendation.py ← Unit tests (U-01 … U-11)
    ├── test_api_contract.py   ← Contract tests (C-01 … C-14)
    └── test_integration.py    ← Integration tests (I-01 … I-07)
```

---

## REST API Endpoints

| Method | URL | Description |
|---|---|---|
| GET | `/api/exercises` | List all exercises |
| POST | `/api/exercises` | Create an exercise |
| GET | `/api/exercises/<id>` | Get one exercise |
| GET | `/api/exercises/<id>/history` | All logged sets |
| POST | `/api/exercises/<id>/sets` | Log a set |
| GET | `/api/exercises/<id>/recommendation` | Next-session recommendation |
| GET | `/api/exercises/<id>/trend` | Estimated 1RM over time |

All requests and responses use JSON. Errors return `{ "error": "..." }` with an appropriate HTTP status code.

---

## Database Schema

**`exercises`** — `id`, `name`, `rep_range_low`, `rep_range_high`, `weight_increment`, `created_at`

**`sets`** — `id`, `exercise_id` (FK), `date` (YYYY-MM-DD), `weight`, `reps`, `logged_at`

---

## The Recommendation Engine

Lives entirely in `server/recommendation.py`. Three pure functions:

- **`recommend(history, rep_range_low, rep_range_high, weight_increment)`** — returns `{ weight, reps, note }`. Uses the last session's best set (highest reps; ties broken by heaviest weight). If best reps ≥ rep_range_high → add weight_increment, reset to rep_range_low. Otherwise → same weight, reps+1.
- **`epley_1rm(weight, reps)`** — returns `weight * (1 + reps / 30)`.
- **`build_trend(history)`** — returns `[{ date, estimated_1rm }, ...]`, one entry per unique date, using the set that produces the highest 1RM that day.

**Rule:** These functions must never make database calls or have side effects. They receive plain Python lists/dicts and return plain Python dicts.

---

## Running the App

**Always run from the project root (`Final-Project/`):**

```bash
# Install dependencies (one-time)
python -m pip install -r requirements.txt

# Start the server
python -m flask --app server/app.py run
```

Then open **http://127.0.0.1:5000** in your browser.

> If you run `flask` from a different directory it will pick up the wrong `server/app.py`. Always `cd` into `Final-Project` first.

---

## Testing Approach

TDD: tests are written before code. Three tiers:

- **Unit** (`test_recommendation.py`) — pure functions only, no DB, no Flask
- **Contract** (`test_api_contract.py`) — Flask test client + in-memory SQLite; verifies response shapes
- **Integration** (`test_integration.py`) — Flask test client + real temp `.db` file; verifies full vertical slices

Run all tests: `pytest tests/ -v`

---

## Development Rules for Claude

1. **Write tests before implementation** (TDD). The `TESTING_PLAN.md` lists all 32 tests; implement them first, then make them pass.
2. **Keep `recommendation.py` pure.** Never add a database import or network call to that file.
3. **Commit frequently** — after each logical unit of work (e.g., after tests pass for a module, after a feature is complete). Push to `origin main` after every commit.
4. **Update this file** when the project structure, API, or key decisions change.
5. **Target explanations at early undergrad level** — the user is learning, so prefer clear code and clear explanations over clever abstractions.
6. **No premature abstraction** — three similar lines beat a helper function that isn't needed yet.

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
| `client/` (HTML, CSS, JS) | Done |
| `requirements.txt` / `README.md` | Done |
