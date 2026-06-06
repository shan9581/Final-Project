"""SQLite helpers — plain SQL in, plain Python dicts out. No business logic."""
import sqlite3
import os


def get_db(db_path):
    """Open a SQLite connection, create tables if they don't exist yet."""
    db = sqlite3.connect(db_path)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys = ON")

    schema_path = os.path.join(os.path.dirname(__file__), "schema.sql")
    with open(schema_path) as f:
        db.executescript(f.read())

    return db


def _row_to_dict(row):
    return dict(row) if row else None


# ── Exercises ─────────────────────────────────────────────────────────────────

def get_exercises(db):
    rows = db.execute(
        "SELECT id, name, rep_range_low, rep_range_high, weight_increment, created_at "
        "FROM exercises ORDER BY name"
    ).fetchall()
    return [dict(r) for r in rows]


def get_exercise(db, exercise_id):
    row = db.execute(
        "SELECT id, name, rep_range_low, rep_range_high, weight_increment, created_at "
        "FROM exercises WHERE id = ?",
        (exercise_id,),
    ).fetchone()
    return _row_to_dict(row)


def insert_exercise(db, name, rep_range_low, rep_range_high, weight_increment):
    cursor = db.execute(
        "INSERT INTO exercises (name, rep_range_low, rep_range_high, weight_increment) "
        "VALUES (?, ?, ?, ?)",
        (name, rep_range_low, rep_range_high, weight_increment),
    )
    db.commit()
    return get_exercise(db, cursor.lastrowid)


# ── Sets ──────────────────────────────────────────────────────────────────────

def get_history(db, exercise_id):
    rows = db.execute(
        "SELECT date, weight, reps FROM sets "
        "WHERE exercise_id = ? ORDER BY date ASC, logged_at ASC",
        (exercise_id,),
    ).fetchall()
    return [dict(r) for r in rows]


def insert_set(db, exercise_id, date, weight, reps):
    cursor = db.execute(
        "INSERT INTO sets (exercise_id, date, weight, reps) VALUES (?, ?, ?, ?)",
        (exercise_id, date, weight, reps),
    )
    db.commit()
    row = db.execute(
        "SELECT id, exercise_id, date, weight, reps, logged_at FROM sets WHERE id = ?",
        (cursor.lastrowid,),
    ).fetchone()
    return dict(row)
