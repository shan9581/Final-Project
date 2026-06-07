"""Flask application — REST API + static client serving."""
import os
from flask import Flask, jsonify, request, send_from_directory, g
from server.db import (
    get_db, get_exercises, get_exercise, insert_exercise, get_history, insert_set, upsert_set,
    get_workout_days, get_workout_day, insert_workout_day, delete_workout_day,
    get_day_exercises, add_exercise_to_day, remove_exercise_from_day, get_or_create_exercise,
    update_exercise_rep_ranges, reset_all_data, get_or_create_imported_day,
    get_session, insert_session, get_logged_dates_in_month, get_sets_on_date,
)
from server.recommendation import recommend, build_trend
from server.presets import PRESET_EXERCISES, SPLIT_TEMPLATES, REP_RANGES
from server.stats import (
    compute_prs, compute_1rm_trend, compute_recent_prs,
    compute_weekly_volume, compute_working_sets_per_week, compute_category_totals,
    compute_streaks, compute_workouts_per_week, compute_heatmap,
    compute_stalled_lifts, compute_muscle_balance, compute_exercise_frequency,
)

CLIENT_DIR = os.path.join(os.path.dirname(__file__), "..", "client")


def create_app(config=None):
    app = Flask(__name__, static_folder=None)
    app.config["DATABASE"] = os.path.join(os.path.dirname(__file__), "..", "workout.db")

    if config:
        app.config.update(config)

    # ── Database connection per request ──────────────────────────────────────

    def get_conn():
        if "db" not in g:
            g.db = get_db(app.config["DATABASE"])
        return g.db

    @app.teardown_appcontext
    def close_db(exc):
        db = g.pop("db", None)
        if db is not None:
            db.close()

    # ── Client static files ───────────────────────────────────────────────────

    @app.route("/")
    def index():
        return send_from_directory(os.path.abspath(CLIENT_DIR), "index.html")

    @app.route("/<path:filename>")
    def static_client(filename):
        return send_from_directory(os.path.abspath(CLIENT_DIR), filename)

    # ── Exercises ─────────────────────────────────────────────────────────────

    @app.route("/api/exercises", methods=["GET"])
    def list_exercises():
        return jsonify(get_exercises(get_conn()))

    @app.route("/api/exercises", methods=["POST"])
    def create_exercise():
        data = request.get_json(silent=True) or {}
        if not data.get("name"):
            return jsonify({"error": "name is required"}), 400
        exercise = insert_exercise(
            get_conn(),
            name=data["name"],
            rep_range_low=int(data.get("rep_range_low", 5)),
            rep_range_high=int(data.get("rep_range_high", 8)),
            weight_increment=float(data.get("weight_increment", 5.0)),
        )
        return jsonify(exercise), 201

    @app.route("/api/exercises/<int:exercise_id>", methods=["GET"])
    def get_one_exercise(exercise_id):
        exercise = get_exercise(get_conn(), exercise_id)
        if exercise is None:
            return jsonify({"error": "exercise not found"}), 404
        return jsonify(exercise)

    # ── Sets ──────────────────────────────────────────────────────────────────

    @app.route("/api/exercises/<int:exercise_id>/history", methods=["GET"])
    def exercise_history(exercise_id):
        if get_exercise(get_conn(), exercise_id) is None:
            return jsonify({"error": "exercise not found"}), 404
        return jsonify(get_history(get_conn(), exercise_id))

    @app.route("/api/exercises/<int:exercise_id>/sets", methods=["POST"])
    def log_set(exercise_id):
        if get_exercise(get_conn(), exercise_id) is None:
            return jsonify({"error": "exercise not found"}), 404
        data = request.get_json(silent=True) or {}
        missing = [f for f in ("date", "weight", "reps") if f not in data]
        if missing:
            return jsonify({"error": f"missing fields: {', '.join(missing)}"}), 400
        new_set = insert_set(
            get_conn(),
            exercise_id=exercise_id,
            date=data["date"],
            weight=float(data["weight"]),
            reps=int(data["reps"]),
        )
        return jsonify(new_set), 201

    @app.route("/api/exercises/<int:exercise_id>/sets/<date>", methods=["PUT"])
    def put_set(exercise_id, date):
        if get_exercise(get_conn(), exercise_id) is None:
            return jsonify({"error": "exercise not found"}), 404
        data = request.get_json(silent=True) or {}
        missing = [f for f in ("weight", "reps") if f not in data]
        if missing:
            return jsonify({"error": f"missing fields: {', '.join(missing)}"}), 400
        updated = upsert_set(
            get_conn(),
            exercise_id=exercise_id,
            date=date,
            weight=float(data["weight"]),
            reps=int(data["reps"]),
        )
        return jsonify(updated)

    # ── Recommendation ────────────────────────────────────────────────────────

    @app.route("/api/exercises/<int:exercise_id>/recommendation", methods=["GET"])
    def exercise_recommendation(exercise_id):
        exercise = get_exercise(get_conn(), exercise_id)
        if exercise is None:
            return jsonify({"error": "exercise not found"}), 404
        history = get_history(get_conn(), exercise_id)
        result = recommend(
            history,
            rep_range_low=exercise["rep_range_low"],
            rep_range_high=exercise["rep_range_high"],
            weight_increment=exercise["weight_increment"],
        )
        return jsonify({
            "weight": result["weight"],
            "target_reps": result["reps"],
            "note": result["note"],
        })

    # ── Trend ─────────────────────────────────────────────────────────────────

    @app.route("/api/exercises/<int:exercise_id>/trend", methods=["GET"])
    def exercise_trend(exercise_id):
        if get_exercise(get_conn(), exercise_id) is None:
            return jsonify({"error": "exercise not found"}), 404
        history = get_history(get_conn(), exercise_id)
        return jsonify(build_trend(history))

    # ── Presets & Templates ───────────────────────────────────────────────────

    @app.route("/api/presets", methods=["GET"])
    def list_presets():
        return jsonify(PRESET_EXERCISES)

    @app.route("/api/split-templates", methods=["GET"])
    def list_split_templates():
        return jsonify(SPLIT_TEMPLATES)

    @app.route("/api/setup", methods=["POST"])
    def setup_split():
        data = request.get_json(silent=True) or {}
        goal = data.get("goal")
        template_id = data.get("template")

        if goal not in REP_RANGES:
            return jsonify({"error": "goal must be 'strength' or 'hypertrophy'"}), 400

        template = next((t for t in SPLIT_TEMPLATES if t["id"] == template_id), None)
        if template is None:
            return jsonify({"error": "unknown template"}), 400

        rep_config = REP_RANGES[goal]
        db = get_conn()
        created = []
        for day_def in template["days"]:
            day = insert_workout_day(db, name=day_def["name"])
            for ex_name in day_def["exercises"]:
                ex = get_or_create_exercise(db, name=ex_name, **rep_config)
                update_exercise_rep_ranges(db, ex["id"], **rep_config)
                add_exercise_to_day(db, day["id"], ex["id"])
            created.append(day)
        return jsonify(created), 201

    # ── Workout Days ──────────────────────────────────────────────────────────

    @app.route("/api/workout-days", methods=["GET"])
    def list_workout_days():
        return jsonify(get_workout_days(get_conn()))

    @app.route("/api/workout-days", methods=["POST"])
    def create_workout_day():
        data = request.get_json(silent=True) or {}
        if not data.get("name"):
            return jsonify({"error": "name is required"}), 400
        day = insert_workout_day(get_conn(), name=data["name"])
        return jsonify(day), 201

    @app.route("/api/workout-days/<int:day_id>", methods=["DELETE"])
    def delete_day(day_id):
        if get_workout_day(get_conn(), day_id) is None:
            return jsonify({"error": "workout day not found"}), 404
        delete_workout_day(get_conn(), day_id)
        return "", 204

    @app.route("/api/workout-days/<int:day_id>/exercises", methods=["GET"])
    def list_day_exercises(day_id):
        if get_workout_day(get_conn(), day_id) is None:
            return jsonify({"error": "workout day not found"}), 404
        return jsonify(get_day_exercises(get_conn(), day_id))

    @app.route("/api/workout-days/<int:day_id>/exercises", methods=["POST"])
    def add_day_exercise(day_id):
        if get_workout_day(get_conn(), day_id) is None:
            return jsonify({"error": "workout day not found"}), 404
        data = request.get_json(silent=True) or {}
        if "exercise_id" in data:
            exercise = get_exercise(get_conn(), int(data["exercise_id"]))
            if exercise is None:
                return jsonify({"error": "exercise not found"}), 404
        elif "name" in data:
            exercise = get_or_create_exercise(
                get_conn(),
                name=data["name"],
                rep_range_low=int(data.get("rep_range_low", 5)),
                rep_range_high=int(data.get("rep_range_high", 8)),
                weight_increment=float(data.get("weight_increment", 5.0)),
            )
        else:
            return jsonify({"error": "exercise_id or name is required"}), 400
        add_exercise_to_day(get_conn(), day_id, exercise["id"])
        return jsonify(exercise), 201

    @app.route("/api/workout-days/<int:day_id>/exercises/<int:exercise_id>", methods=["DELETE"])
    def remove_day_exercise(day_id, exercise_id):
        remove_exercise_from_day(get_conn(), day_id, exercise_id)
        return "", 204

    # ── Sessions & Calendar ───────────────────────────────────────────────────

    @app.route("/api/sessions/<date>", methods=["GET"])
    def get_session_route(date):
        session = get_session(get_conn(), date)
        if session is None:
            return jsonify(None)
        exercises = get_day_exercises(get_conn(), session["workout_day_id"])
        return jsonify({"session": session, "exercises": exercises})

    @app.route("/api/sessions", methods=["POST"])
    def create_session():
        data = request.get_json(silent=True) or {}
        date = data.get("date")
        workout_day_id = data.get("workout_day_id")
        if not date or not workout_day_id:
            return jsonify({"error": "date and workout_day_id are required"}), 400
        session = insert_session(get_conn(), date, int(workout_day_id))
        exercises = get_day_exercises(get_conn(), session["workout_day_id"])
        return jsonify({"session": session, "exercises": exercises}), 201

    @app.route("/api/sessions/<date>/sets", methods=["GET"])
    def session_sets(date):
        return jsonify(get_sets_on_date(get_conn(), date))

    @app.route("/api/calendar/<int:year>/<int:month>", methods=["GET"])
    def calendar_dates(year, month):
        return jsonify(get_logged_dates_in_month(get_conn(), year, month))

    # ── Stats ─────────────────────────────────────────────────────────────────

    @app.route("/api/stats", methods=["GET"])
    def get_stats():
        db = get_conn()
        category_map = {ex["name"]: ex["category"] for ex in PRESET_EXERCISES}

        exercises = get_exercises(db)
        exh = [
            {"id": ex["id"], "name": ex["name"], "history": get_history(db, ex["id"])}
            for ex in exercises
        ]

        rows = db.execute(
            "SELECT s.date, s.weight, s.reps, e.name AS exercise_name "
            "FROM sets s JOIN exercises e ON e.id = s.exercise_id ORDER BY s.date"
        ).fetchall()
        all_sets = [dict(r) for r in rows]
        all_sets_cat = [{**s, "category": category_map.get(s["exercise_name"])} for s in all_sets]

        session_dates = [
            r["date"] for r in
            db.execute("SELECT date FROM workout_sessions ORDER BY date").fetchall()
        ]

        prs    = {ex["name"]: compute_prs(ex["history"]) for ex in exh if ex["history"]}
        trends = {ex["name"]: compute_1rm_trend(ex["history"]) for ex in exh if len(ex["history"]) >= 2}
        cat    = compute_category_totals(all_sets_cat)

        return jsonify({
            "strength": {
                "prs":        prs,
                "trends":     trends,
                "recent_prs": compute_recent_prs(exh),
            },
            "volume": {
                "weekly":             compute_weekly_volume(all_sets),
                "working_sets":       compute_working_sets_per_week(all_sets),
                "category_totals":    cat["totals"],
                "uncategorized_count": cat["uncategorized_count"],
            },
            "consistency": {
                "streaks":           compute_streaks(session_dates),
                "workouts_per_week": compute_workouts_per_week(session_dates),
                "heatmap":           compute_heatmap(session_dates),
            },
            "diagnostics": {
                "stalled":   compute_stalled_lifts(exh),
                "balance":   compute_muscle_balance(all_sets_cat),
                "frequency": compute_exercise_frequency(exh),
            },
        })

    @app.route("/api/reset", methods=["POST"])
    def reset():
        reset_all_data(get_conn())
        return "", 204

    @app.route("/api/import", methods=["POST"])
    def import_csv():
        import csv, io
        data = request.get_json(silent=True) or {}
        csv_text = data.get("csv", "").strip()
        if not csv_text:
            return jsonify({"error": "csv field is required"}), 400

        reader = csv.DictReader(io.StringIO(csv_text))
        fieldnames = [f.strip().lower() for f in (reader.fieldnames or [])]
        required = {"date", "exercise", "weight", "reps"}
        if not required.issubset(set(fieldnames)):
            missing = required - set(fieldnames)
            return jsonify({"error": f"Missing columns: {', '.join(sorted(missing))}"}), 400

        db = get_conn()
        imported = 0
        errors = []
        dates_to_exercises = {}  # date -> set of exercise ids

        for i, row in enumerate(reader, start=2):
            try:
                row = {k.strip().lower(): v.strip() for k, v in row.items()}
                ex = get_or_create_exercise(db, name=row["exercise"])
                insert_set(db, ex["id"], row["date"], float(row["weight"]), int(row["reps"]))
                imported += 1
                dates_to_exercises.setdefault(row["date"], set()).add(ex["id"])
            except Exception as e:
                errors.append(f"Row {i}: {e}")

        # Create an "Imported" workout day and wire up sessions for each date
        if dates_to_exercises:
            imported_day = get_or_create_imported_day(db)
            for date_str, ex_ids in dates_to_exercises.items():
                for ex_id in ex_ids:
                    add_exercise_to_day(db, imported_day["id"], ex_id)
                if get_session(db, date_str) is None:
                    insert_session(db, date_str, imported_day["id"])

        return jsonify({"imported": imported, "errors": errors})

    return app


if __name__ == "__main__":
    create_app().run(debug=True)
