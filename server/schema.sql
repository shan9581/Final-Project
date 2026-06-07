CREATE TABLE IF NOT EXISTS exercises (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    rep_range_low INTEGER NOT NULL DEFAULT 5,
    rep_range_high INTEGER NOT NULL DEFAULT 8,
    weight_increment REAL NOT NULL DEFAULT 5.0,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS sets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    exercise_id INTEGER NOT NULL REFERENCES exercises(id),
    date TEXT NOT NULL,
    weight REAL NOT NULL,
    reps INTEGER NOT NULL,
    logged_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS workout_days (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    position INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS workout_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL UNIQUE,
    workout_day_id INTEGER NOT NULL REFERENCES workout_days(id) ON DELETE CASCADE,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS workout_day_exercises (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    workout_day_id INTEGER NOT NULL REFERENCES workout_days(id) ON DELETE CASCADE,
    exercise_id INTEGER NOT NULL REFERENCES exercises(id),
    position INTEGER NOT NULL DEFAULT 0,
    UNIQUE(workout_day_id, exercise_id)
);
