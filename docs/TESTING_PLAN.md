# Workout Tracker — Testing Plan

> **Who this is for:** Someone who has written Python before but has not used a structured testing approach. This document explains *why* we test, *what kinds* of tests exist, and then lists every test we will write before writing the code.

---

## 1. What is Test-Driven Development (TDD)?

In test-driven development you write the test first, watch it fail (because the code doesn't exist yet), then write just enough code to make it pass. The cycle is:

```
1. Write a failing test   →   RED
2. Write the code         →   GREEN
3. Clean up the code      →   REFACTOR
```

Repeat for every piece of behaviour. The benefit is that every feature is covered by a test from day one, and you can refactor later with confidence.

---

## 2. The Three Kinds of Tests We Use

### Unit Tests
- **What:** Test a single function in complete isolation. No database, no HTTP server, no network.
- **Speed:** Milliseconds. Run after every small change.
- **Analogy:** Testing a single LEGO brick — does it have the right shape?

### Contract Tests
- **What:** Verify that the server's API responses have the right *shape* — correct keys, correct types — without caring about exact values. These tests start a real Flask test server but use an in-memory SQLite database so they don't touch the disk.
- **Speed:** Fast (under a second each), but slower than unit tests.
- **Analogy:** Checking that the blueprint for a LEGO set is correct before building anything.

### Integration Tests
- **What:** Test the entire vertical slice from HTTP request → Flask route → database → HTTP response. Use a real (but temporary) SQLite file on disk. Verify that everything works together.
- **Speed:** Slower — each test creates and destroys a database.
- **Analogy:** Building the full LEGO set and verifying it looks like the picture on the box.

---

## 3. Test Infrastructure

We will use **pytest** as the test runner. Two fixtures are defined in `tests/conftest.py`:

- `app` — creates a Flask app wired to an in-memory SQLite database (`:memory:`). Used by contract tests.
- `client` — wraps the `app` fixture to give a test HTTP client. Used by contract tests.
- `db_path` — creates a real temporary `.db` file, runs schema setup, yields the path, then deletes the file. Used by integration tests.

---

## 4. Test List

Each test is written as a *behaviour statement* so it reads like a specification.

---

### 4.1 Unit Tests — `tests/test_recommendation.py`

These tests only import `server/recommendation.py`. No Flask, no SQLite.

| # | Label | Test behaviour |
|---|---|---|
| U-01 | UNIT | `recommend()` with empty history returns weight=0, reps=rep_range_low, and a non-empty note string |
| U-02 | UNIT | When the last session's best set is below the rep range ceiling, `recommend()` keeps the same weight and returns reps+1 |
| U-03 | UNIT | When the last session's best set equals the rep range ceiling, `recommend()` returns weight+increment and reps=rep_range_low |
| U-04 | UNIT | When there are multiple sets on the last session date, `recommend()` uses the set with the highest rep count as the "best set" |
| U-05 | UNIT | When two sets on the last session date have equal reps, `recommend()` uses the heavier set to break the tie |
| U-06 | UNIT | `recommend()` only looks at the most recent date, not at older sessions |
| U-07 | UNIT | `epley_1rm(weight=100, reps=5)` returns 116.67 (rounded to 2 decimal places) |
| U-08 | UNIT | `epley_1rm(weight=100, reps=1)` returns 103.33 (1 rep is still a valid input) |
| U-09 | UNIT | `build_trend(history)` returns one dict per unique date, each with `date` and `estimated_1rm` keys |
| U-10 | UNIT | `build_trend(history)` picks the set that produces the *highest* 1RM for each date, not just the first set |
| U-11 | UNIT | `build_trend([])` returns an empty list without raising an error |

---

### 4.2 Contract Tests — `tests/test_api_contract.py`

These tests use Flask's test client. They check HTTP status codes and JSON response shapes.

#### Exercises endpoint

| # | Label | Test behaviour |
|---|---|---|
| C-01 | CONTRACT | `GET /api/exercises` returns status 200 and a JSON array |
| C-02 | CONTRACT | Each item in the `GET /api/exercises` response has keys: `id`, `name`, `rep_range_low`, `rep_range_high`, `weight_increment` |
| C-03 | CONTRACT | `POST /api/exercises` with valid JSON returns status 201 and the created object including an `id` |
| C-04 | CONTRACT | `POST /api/exercises` with missing `name` field returns status 400 and a JSON object with an `error` key |
| C-05 | CONTRACT | `GET /api/exercises/<id>` for a nonexistent id returns status 404 and a JSON object with an `error` key |

#### Sets endpoint

| # | Label | Test behaviour |
|---|---|---|
| C-06 | CONTRACT | `POST /api/exercises/<id>/sets` with valid JSON returns status 201 and has keys: `id`, `exercise_id`, `date`, `weight`, `reps` |
| C-07 | CONTRACT | `POST /api/exercises/<id>/sets` with missing `weight` field returns status 400 |
| C-08 | CONTRACT | `POST /api/exercises/<id>/sets` with missing `reps` field returns status 400 |
| C-09 | CONTRACT | `POST /api/exercises/<id>/sets` with missing `date` field returns status 400 |
| C-10 | CONTRACT | `GET /api/exercises/<id>/history` returns status 200 and a JSON array where each item has `date`, `weight`, `reps` |

#### Recommendation endpoint

| # | Label | Test behaviour |
|---|---|---|
| C-11 | CONTRACT | `GET /api/exercises/<id>/recommendation` returns status 200 and has keys: `weight`, `target_reps`, `note` |
| C-12 | CONTRACT | `GET /api/exercises/<id>/recommendation` for an exercise with no history has `note` that is a non-empty string |

#### Trend endpoint

| # | Label | Test behaviour |
|---|---|---|
| C-13 | CONTRACT | `GET /api/exercises/<id>/trend` returns status 200 and a JSON array |
| C-14 | CONTRACT | Each item in the trend array has keys: `date` (string) and `estimated_1rm` (number) |

---

### 4.3 Integration Tests — `tests/test_integration.py`

These tests start the server against a real temporary SQLite database file and exercise full vertical slices.

| # | Label | Test behaviour |
|---|---|---|
| I-01 | INTEGRATION | Creating an exercise via `POST /api/exercises`, then calling `GET /api/exercises`, returns the created exercise in the list |
| I-02 | INTEGRATION | Logging a set via `POST /api/exercises/<id>/sets`, then calling `GET /api/exercises/<id>/history`, returns that set in the history |
| I-03 | INTEGRATION | After logging a set at the rep range ceiling, `GET /api/exercises/<id>/recommendation` returns a weight equal to the logged weight plus the exercise's `weight_increment` |
| I-04 | INTEGRATION | After logging a set below the rep range ceiling, `GET /api/exercises/<id>/recommendation` returns the same weight and reps+1 |
| I-05 | INTEGRATION | Logging sets on three different dates and calling `GET /api/exercises/<id>/trend` returns exactly three items in ascending date order |
| I-06 | INTEGRATION | Deleting all sets for an exercise (or using a fresh exercise) causes `GET /api/exercises/<id>/recommendation` to return the "no history" note |
| I-07 | INTEGRATION | Data from one exercise does not appear in another exercise's history (isolation check) |

---

## 5. What We Are Deliberately Not Testing

| Thing | Why we skip it |
|---|---|
| The SQLite library itself | It is third-party, well-tested code |
| HTML rendering / CSS layout | Covered by manual visual inspection; browser differences make automated testing brittle |
| Flask's routing internals | Same reason — third-party, well-tested |
| Behaviour when the disk is full | Edge case not worth the complexity for a learning project |

---

## 6. Running the Tests

```bash
# Install dependencies (one-time)
pip install -r requirements.txt

# Run all tests with a short summary
pytest tests/ -v

# Run only unit tests
pytest tests/test_recommendation.py -v

# Run only contract tests
pytest tests/test_api_contract.py -v

# Run only integration tests
pytest tests/test_integration.py -v

# Run and see coverage report
pytest tests/ --cov=server --cov-report=term-missing
```

---

## 7. Test Count Summary

| Type | Count | File |
|---|---|---|
| Unit | 11 | `tests/test_recommendation.py` |
| Contract | 14 | `tests/test_api_contract.py` |
| Integration | 7 | `tests/test_integration.py` |
| **Total** | **32** | |
