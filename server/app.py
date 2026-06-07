"""Flask application — REST API + static client serving."""
import os
from flask import Flask, jsonify, request, send_from_directory, g
from server.db import (
    get_db, get_exercises, get_exercise, insert_exercise, get_history, insert_set, upsert_set,
    get_workout_days, get_workout_day, insert_workout_day, delete_workout_day,
    get_day_exercises, add_exercise_to_day, remove_exercise_from_day, get_or_create_exercise,
    update_exercise_rep_ranges, reset_all_data,
    get_session, insert_session, get_logged_dates_in_month, get_sets_on_date,
)
from server.recommendation import recommend, build_trend
from server.presets import PRESET_EXERCISES, SPLIT_TEMPLATES, REP_RANGES

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

    @app.route("/api/reset", methods=["POST"])
    def reset():
        reset_all_data(get_conn())
        return "", 204

    return app


if __name__ == "__main__":
    create_app().run(debug=True)
