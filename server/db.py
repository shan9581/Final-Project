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


def upsert_set(db, exercise_id, date, weight, reps):
    """Replace any existing set for this exercise+date with a single new one."""
    db.execute(
        "DELETE FROM sets WHERE exercise_id = ? AND date = ?",
        (exercise_id, date),
    )
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


# ── Workout Days ──────────────────────────────────────────────────────────────

def get_workout_days(db):
    rows = db.execute(
        "SELECT id, name, position, created_at FROM workout_days ORDER BY position, id"
    ).fetchall()
    return [dict(r) for r in rows]


def get_workout_day(db, day_id):
    row = db.execute(
        "SELECT id, name, position, created_at FROM workout_days WHERE id = ?",
        (day_id,),
    ).fetchone()
    return _row_to_dict(row)


def insert_workout_day(db, name):
    cursor = db.execute("INSERT INTO workout_days (name) VALUES (?)", (name,))
    db.commit()
    return get_workout_day(db, cursor.lastrowid)


def delete_workout_day(db, day_id):
    db.execute("DELETE FROM workout_days WHERE id = ?", (day_id,))
    db.commit()


def get_day_exercises(db, day_id):
    rows = db.execute(
        "SELECT e.id, e.name, e.rep_range_low, e.rep_range_high, e.weight_increment "
        "FROM workout_day_exercises wde "
        "JOIN exercises e ON e.id = wde.exercise_id "
        "WHERE wde.workout_day_id = ? "
        "ORDER BY wde.position, wde.id",
        (day_id,),
    ).fetchall()
    return [dict(r) for r in rows]


def add_exercise_to_day(db, day_id, exercise_id):
    db.execute(
        "INSERT OR IGNORE INTO workout_day_exercises (workout_day_id, exercise_id) VALUES (?, ?)",
        (day_id, exercise_id),
    )
    db.commit()


def remove_exercise_from_day(db, day_id, exercise_id):
    db.execute(
        "DELETE FROM workout_day_exercises WHERE workout_day_id = ? AND exercise_id = ?",
        (day_id, exercise_id),
    )
    db.commit()


def get_or_create_exercise(db, name, rep_range_low=5, rep_range_high=8, weight_increment=5.0):
    row = db.execute(
        "SELECT id, name, rep_range_low, rep_range_high, weight_increment, created_at "
        "FROM exercises WHERE name = ?",
        (name,),
    ).fetchone()
    if row:
        return dict(row)
    return insert_exercise(db, name, rep_range_low, rep_range_high, weight_increment)


# ── Sessions & Calendar ───────────────────────────────────────────────────────

def get_session(db, date):
    row = db.execute(
        "SELECT s.id, s.date, s.workout_day_id, w.name AS workout_day_name "
        "FROM workout_sessions s JOIN workout_days w ON w.id = s.workout_day_id "
        "WHERE s.date = ?",
        (date,),
    ).fetchone()
    return _row_to_dict(row)


def insert_session(db, date, workout_day_id):
    db.execute(
        "INSERT OR REPLACE INTO workout_sessions (date, workout_day_id) VALUES (?, ?)",
        (date, workout_day_id),
    )
    db.commit()
    return get_session(db, date)


def get_logged_dates_in_month(db, year, month):
    prefix = f"{year:04d}-{month:02d}-"
    rows = db.execute(
        "SELECT DISTINCT date FROM sets WHERE date LIKE ? ORDER BY date",
        (f"{prefix}%",),
    ).fetchall()
    return [r["date"] for r in rows]


def get_sets_on_date(db, date):
    rows = db.execute(
        "SELECT id, exercise_id, weight, reps, logged_at FROM sets "
        "WHERE date = ? ORDER BY exercise_id, logged_at",
        (date,),
    ).fetchall()
    return [dict(r) for r in rows]


def update_exercise_rep_ranges(db, exercise_id, rep_range_low, rep_range_high, weight_increment):
    db.execute(
        "UPDATE exercises SET rep_range_low=?, rep_range_high=?, weight_increment=? WHERE id=?",
        (rep_range_low, rep_range_high, weight_increment, exercise_id),
    )
    db.commit()
    return get_exercise(db, exercise_id)
