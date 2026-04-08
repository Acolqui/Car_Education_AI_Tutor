from typing import Any

from flask import jsonify, render_template, request

from config import CURRICULUM_FILE, SESSION_LOG_FILE, STUDENT_STATE_FILE
from storage import load_json, log_session_turn, save_json
from tutor_logic import (
    DEFAULT_CURRICULUM,
    DEFAULT_STUDENT_STATE,
    get_topic_by_id,
    inner_loop,
    outer_loop,
)


def register_routes(app) -> None:
    @app.route("/")
    def home() -> str:
        return render_template("index.html")

    @app.route("/chat", methods=["POST"])
    def chat() -> Any:
        data = request.get_json(silent=True) or {}
        student_message = data.get("message", "").strip()

        if not student_message:
            return jsonify({"error": "Message is required."}), 400

        curriculum = load_json(CURRICULUM_FILE, DEFAULT_CURRICULUM)
        student_state = load_json(STUDENT_STATE_FILE, DEFAULT_STUDENT_STATE)

        current_topic_id = student_state.get("current_topic", "")
        current_topic = get_topic_by_id(curriculum, current_topic_id)

        if current_topic is None:
            topics = curriculum.get("topics", [])
            if not topics:
                return jsonify({"error": "No topics found in curriculum.json"}), 500

            current_topic = topics[0]
            student_state["current_topic"] = current_topic["id"]

            if not student_state.get("mastery"):
                student_state["mastery"] = {
                    topic["id"]: 0.0 for topic in topics
                }

        tutor_reply = inner_loop(student_state, current_topic, student_message)
        planner_update = outer_loop(student_state, curriculum)

        save_json(STUDENT_STATE_FILE, student_state)

        log_session_turn(
            SESSION_LOG_FILE,
            {
                "student_message": student_message,
                "topic": current_topic["id"],
                "tutor_reply": tutor_reply,
                "planner_update": planner_update,
                "student_state_snapshot": student_state,
            },
        )

        return jsonify(
            {
                "tutor_reply": tutor_reply,
                "planner_update": planner_update,
                "student_state": student_state,
            }
        )

    @app.route("/progress", methods=["GET"])
    def progress() -> Any:
        student_state = load_json(STUDENT_STATE_FILE, DEFAULT_STUDENT_STATE)
        return jsonify(student_state)

    @app.route("/reset", methods=["POST"])
    def reset() -> Any:
        curriculum = load_json(CURRICULUM_FILE, DEFAULT_CURRICULUM)
        topics = curriculum.get("topics", [])

        fresh_state = DEFAULT_STUDENT_STATE.copy()
        fresh_state["current_topic"] = topics[0]["id"] if topics else ""
        fresh_state["mastery"] = {topic["id"]: 0.0 for topic in topics}

        save_json(STUDENT_STATE_FILE, fresh_state)
        save_json(SESSION_LOG_FILE, [])

        return jsonify({"message": "Student progress has been reset."})