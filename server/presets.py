REP_RANGES = {
    "strength":    {"rep_range_low": 3,  "rep_range_high": 6,  "weight_increment": 5.0},
    "hypertrophy": {"rep_range_low": 8,  "rep_range_high": 12, "weight_increment": 2.5},
}

SPLIT_TEMPLATES = [
    {
        "id": "ppl",
        "name": "Push / Pull / Legs",
        "description": "3 days — the most popular split for intermediate lifters",
        "days": [
            {"name": "Push Day", "exercises": ["Bench Press", "Overhead Press", "Incline Bench Press", "Tricep Pushdown", "Lateral Raises"]},
            {"name": "Pull Day", "exercises": ["Deadlift", "Pull-ups", "Barbell Row", "Barbell Curl", "Face Pulls"]},
            {"name": "Legs Day", "exercises": ["Squat", "Romanian Deadlift", "Leg Press", "Leg Curl", "Calf Raises"]},
        ],
    },
    {
        "id": "upper_lower",
        "name": "Upper / Lower",
        "description": "2 days — ideal for beginners or 4-day programs",
        "days": [
            {"name": "Upper Body", "exercises": ["Bench Press", "Barbell Row", "Overhead Press", "Barbell Curl", "Tricep Pushdown"]},
            {"name": "Lower Body", "exercises": ["Squat", "Romanian Deadlift", "Leg Press", "Leg Curl", "Calf Raises"]},
        ],
    },
    {
        "id": "full_body",
        "name": "Full Body",
        "description": "1 day — great for 3x/week training",
        "days": [
            {"name": "Full Body", "exercises": ["Squat", "Bench Press", "Barbell Row", "Overhead Press", "Romanian Deadlift"]},
        ],
    },
    {
        "id": "bro_split",
        "name": "Bro Split",
        "description": "5 days — one muscle group per session",
        "days": [
            {"name": "Chest Day",     "exercises": ["Bench Press", "Incline Bench Press", "Dips"]},
            {"name": "Back Day",      "exercises": ["Deadlift", "Pull-ups", "Barbell Row", "Cable Row"]},
            {"name": "Shoulders Day", "exercises": ["Overhead Press", "Lateral Raises", "Face Pulls", "Dumbbell Shoulder Press"]},
            {"name": "Arms Day",      "exercises": ["Barbell Curl", "Dumbbell Curl", "Hammer Curl", "Tricep Pushdown", "Skull Crushers"]},
            {"name": "Legs Day",      "exercises": ["Squat", "Romanian Deadlift", "Leg Press", "Leg Curl", "Calf Raises"]},
        ],
    },
]

PRESET_EXERCISES = [
    # Push
    {"name": "Bench Press",             "category": "Push"},
    {"name": "Incline Bench Press",     "category": "Push"},
    {"name": "Overhead Press",          "category": "Push"},
    {"name": "Dumbbell Shoulder Press", "category": "Push"},
    {"name": "Lateral Raises",          "category": "Push"},
    {"name": "Tricep Pushdown",         "category": "Push"},
    {"name": "Skull Crushers",          "category": "Push"},
    {"name": "Dips",                    "category": "Push"},
    # Pull
    {"name": "Deadlift",        "category": "Pull"},
    {"name": "Pull-ups",        "category": "Pull"},
    {"name": "Lat Pulldown",    "category": "Pull"},
    {"name": "Barbell Row",     "category": "Pull"},
    {"name": "Dumbbell Row",    "category": "Pull"},
    {"name": "Cable Row",       "category": "Pull"},
    {"name": "Barbell Curl",    "category": "Pull"},
    {"name": "Dumbbell Curl",   "category": "Pull"},
    {"name": "Hammer Curl",     "category": "Pull"},
    {"name": "Face Pulls",      "category": "Pull"},
    # Legs
    {"name": "Squat",                  "category": "Legs"},
    {"name": "Front Squat",            "category": "Legs"},
    {"name": "Romanian Deadlift",      "category": "Legs"},
    {"name": "Leg Press",              "category": "Legs"},
    {"name": "Leg Curl",               "category": "Legs"},
    {"name": "Leg Extension",          "category": "Legs"},
    {"name": "Lunges",                 "category": "Legs"},
    {"name": "Bulgarian Split Squat",  "category": "Legs"},
    {"name": "Hip Thrust",             "category": "Legs"},
    {"name": "Calf Raises",            "category": "Legs"},
    # Core
    {"name": "Plank",         "category": "Core"},
    {"name": "Crunches",      "category": "Core"},
    {"name": "Leg Raises",    "category": "Core"},
    {"name": "Russian Twist", "category": "Core"},
    {"name": "Cable Crunch",  "category": "Core"},
]
