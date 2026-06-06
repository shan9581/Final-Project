"""Flask application — REST API + static client serving."""
import os
from flask import Flask, jsonify, request, send_from_directory, g
from server.db import get_db, get_exercises, get_exercise, insert_exercise, get_history, insert_set
from server.recommendation import recommend, build_trend

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

    return app


if __name__ == "__main__":
    create_app().run(debug=True)
