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
