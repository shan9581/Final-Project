# Workout Tracker — Architecture Document

> **Who this is for:** Someone comfortable with Python and basic web concepts, but new to multi-tier application design. Every decision below is explained from first principles.

---

## 1. The Big Picture

This application is split into three separate pieces that each do one job:

| Piece | What it does | Technology |
|---|---|---|
| **Database** | Stores all data permanently | SQLite (one file on disk) |
| **Server** | Owns the data; enforces rules; speaks HTTP | Python + Flask |
| **Client** | What the user sees and clicks | HTML + CSS + JavaScript (runs in the browser) |

This pattern is called a **three-tier architecture**. The client never touches the database directly — it can only ask the server for data, and the server decides what to return.

```
  [ Browser (Client) ]
           |
        HTTP / REST API
           |
    [ Flask Server ]
           |
        SQL queries
           |
    [ SQLite Database ]
```

**Why separate the client and server?**
- The server is the single source of truth. Business rules (like the weight-progression logic) live in one place, so they can't be accidentally bypassed.
- The client is just a display layer. You could swap the browser client for a mobile app and the server wouldn't change at all.

---

## 2. Component Diagram

See `components.mmd` for the full Mermaid diagram. Here is a plain-English tour:

- **`server/app.py`** — The Flask application. Registers all URL routes (the API endpoints).
- **`server/db.py`** — Handles opening the SQLite connection and running SQL queries. No business logic here — just data in, data out.
- **`server/recommendation.py`** — A **pure function** that takes a list of past sets and returns a recommended weight and rep target. It never opens a database connection. This is the heart of the application.
- **`client/index.html`** — The single-page web interface. Uses JavaScript `fetch()` to call the server's API.

---

## 3. The REST API

REST (Representational State Transfer) is a set of conventions for how a client and server talk over HTTP. Each "resource" (exercises, sets) gets its own URL, and standard HTTP verbs express what action to take.

| Method | URL | What it does |
|---|---|---|
| `GET` | `/api/exercises` | List all exercises |
| `POST` | `/api/exercises` | Create a new exercise |
| `GET` | `/api/exercises/<id>` | Get details for one exercise |
| `GET` | `/api/exercises/<id>/history` | Get all logged sets for an exercise |
| `POST` | `/api/exercises/<id>/sets` | Log a new set |
| `GET` | `/api/exercises/<id>/recommendation` | Get the weight/rep recommendation |
| `GET` | `/api/exercises/<id>/trend` | Get the 1RM trend over time |

All responses are JSON. For example, `GET /api/exercises` returns:

```json
[
  { "id": 1, "name": "Bench Press", "rep_range_low": 5, "rep_range_high": 8, "weight_increment": 5.0 }
]
```

---

## 4. The Database Schema

SQLite stores everything in a single `.db` file. The database has two tables:

### `exercises`

Stores the definition of each exercise, including the target rep range and how much weight to add when progressing.

| Column | Type | Meaning |
|---|---|---|
| `id` | INTEGER (PK) | Auto-incrementing unique ID |
| `name` | TEXT | e.g., `"Bench Press"` |
| `rep_range_low` | INTEGER | Bottom of the rep range (e.g., 5) |
| `rep_range_high` | INTEGER | Top of the rep range (e.g., 8) |
| `weight_increment` | REAL | How many lbs/kg to add when progressing (e.g., 5.0) |
| `created_at` | TEXT | ISO 8601 timestamp |

### `sets`

Each row is one set performed on one date. Multiple sets can be logged per session (e.g., 3 sets of Bench Press on 2026-06-01).

| Column | Type | Meaning |
|---|---|---|
| `id` | INTEGER (PK) | Auto-incrementing unique ID |
| `exercise_id` | INTEGER (FK) | Which exercise this set belongs to |
| `date` | TEXT | Date of the session (`YYYY-MM-DD`) |
| `weight` | REAL | Weight used (lbs or kg — user's choice) |
| `reps` | INTEGER | Reps completed |
| `logged_at` | TEXT | ISO 8601 timestamp of when it was entered |

See `db_schema.mmd` for the entity-relationship diagram.

---

## 5. The Weight-Recommendation Engine

This is the most important piece of logic in the application. It lives entirely in `server/recommendation.py` and is a **pure function** — given the same inputs, it always returns the same output, and it has no side effects (no database calls, no randomness, no network requests).

### What is double progression?

Double progression is a simple strength-training principle:
1. Pick a weight and a rep range (e.g., 5–8 reps).
2. Each session, try to do one more rep than last time, keeping the weight the same.
3. Once you hit the top of the rep range, add weight (the `weight_increment`) and reset reps to the bottom of the range.

### The algorithm

```
function recommend(history, rep_range_low, rep_range_high, weight_increment):

    if history is empty:
        return { weight: 0, reps: rep_range_low, note: "No history — enter your starting weight" }

    last_session = the most recent date's sets
    best_set     = the set from last_session with the most reps
                   (ties broken by heaviest weight)

    if best_set.reps >= rep_range_high:
        # Hit the top — time to add weight
        return { weight: best_set.weight + weight_increment, reps: rep_range_low }
    else:
        # Still climbing — add one rep, keep the weight
        return { weight: best_set.weight, reps: best_set.reps + 1 }
```

### Why a pure function?

Testing a function that calls a database is painful: you need a real (or fake) database, you need to populate it with test data, and the test becomes slow and brittle. A pure function can be tested with a simple list of dictionaries — no setup, no teardown, instant.

---

## 6. Strength Trend (Estimated 1-Rep Max)

Different sessions may use different weights and rep counts, making them hard to compare directly. The **Epley formula** converts any (weight, reps) pair into an estimated one-rep max (1RM) — the weight you could theoretically lift exactly once:

```
1RM = weight × (1 + reps / 30)
```

For each session date, we pick the **best set** (the one that produces the highest 1RM) and record it. Plotting these values over time gives a trend line that shows whether you are getting stronger.

**Example:**

| Date | Weight | Reps | Estimated 1RM |
|---|---|---|---|
| 2026-05-01 | 100 lb | 5 | 100 × (1 + 5/30) = **116.7 lb** |
| 2026-05-08 | 100 lb | 6 | 100 × (1 + 6/30) = **120.0 lb** |
| 2026-05-15 | 105 lb | 5 | 105 × (1 + 5/30) = **122.5 lb** |

---

## 7. File Layout

```
Final-Project/
├── docs/
│   ├── ARCHITECTURE.md       ← this file
│   ├── TESTING_PLAN.md
│   ├── components.mmd        ← Mermaid component diagram
│   ├── data_flow.mmd         ← Mermaid sequence diagram
│   └── db_schema.mmd         ← Mermaid ER diagram
│
├── server/
│   ├── app.py                ← Flask routes
│   ├── db.py                 ← Database helpers
│   ├── recommendation.py     ← Pure recommendation function
│   └── schema.sql            ← SQL to create tables
│
├── client/
│   ├── index.html
│   ├── style.css
│   └── app.js
│
├── tests/
│   ├── test_recommendation.py   ← Unit tests (no DB)
│   ├── test_api_contract.py     ← Contract tests (shape of responses)
│   └── test_integration.py      ← Integration tests (full stack)
│
├── requirements.txt
└── README.md
```

---

## 8. Key Design Decisions and Trade-offs

| Decision | Why | What we gave up |
|---|---|---|
| SQLite instead of PostgreSQL | Zero setup; database is one file you can copy | Not suitable for many simultaneous users |
| Separate client HTML file | Client and server are truly decoupled | Slightly more boilerplate than server-rendered HTML |
| Pure recommendation function | Easy to unit-test; clear inputs and outputs | Logic can't be customized per-request without passing more arguments |
| One `sets` table (no `sessions` table) | Simpler schema | Grouping by session requires a `GROUP BY date` query |
| Epley formula for 1RM | Simple, well-known, accurate enough | More complex formulas (Brzycki, Lombardi) may be more accurate for high reps |
