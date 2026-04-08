from typing import Any, Dict, List, Optional

from ai_feedback import generate_feedback_message

DEFAULT_CURRICULUM = {}
DEFAULT_STUDENT_STATE = {}

def clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


def get_topic_by_id(curriculum: Dict[str, Any], topic_id: str) -> Optional[Dict[str, Any]]:
    for topic in curriculum.get("topics", []):
        if topic.get("id") == topic_id:
            return topic
    return None


def prerequisites_met(student_state: Dict[str, Any], topic: Dict[str, Any]) -> bool:
    completed_topics = set(student_state.get("completed_topics", []))
    prerequisites = topic.get("prerequisites", [])
    return all(prereq in completed_topics for prereq in prerequisites)


def update_mastery(student_state: Dict[str, Any], topic_id: str, delta: float) -> None:
    mastery = student_state.setdefault("mastery", {})
    current_score = float(mastery.get(topic_id, 0.0))
    mastery[topic_id] = round(clamp(current_score + delta), 2)


def keyword_match_score(text: str, keywords: List[str]) -> float:
    if not text or not keywords:
        return 0.0

    lowered_text = text.lower()
    hits = 0

    for keyword in keywords:
        if keyword.lower() in lowered_text:
            hits += 1

    return hits / len(keywords)


def inner_loop(student_state: Dict[str, Any], topic: Dict[str, Any], student_message: str) -> Dict[str, Any]:
    stage = student_state.get("lesson_stage", "teach")
    quiz = topic.get("quiz", {})

    if stage == "teach":
        student_state["lesson_stage"] = "quiz"
        student_state["attempts_on_current_question"] = 0
        student_state["last_topic_studied"] = topic.get("id")

        return {
            "action": "show_material",
            "message": topic.get("content", "No lesson content available."),
            "question": quiz.get("question", "No question available."),
            "correct": None,
            "mastery_delta": 0.0
        }

    if stage == "quiz":
        student_state["attempts_on_current_question"] = (
            student_state.get("attempts_on_current_question", 0) + 1
        )

        accepted_keywords = quiz.get("accepted_keywords", [])
        score = keyword_match_score(student_message, accepted_keywords)

        if score >= 0.5:
            update_mastery(student_state, topic["id"], 0.15)
            student_state["lesson_stage"] = "teach"
            student_state["attempts_on_current_question"] = 0

            base_feedback = f"Correct. The main idea is: {quiz.get('answer', '')}"

            return {
                "action": "feedback",
                "message": generate_feedback_message(
                    topic=topic,
                    student_answer=student_message,
                    correct=True,
                    base_feedback=base_feedback
                ),
                "question": None,
                "correct": True,
                "mastery_delta": 0.15
            }

        if student_state["attempts_on_current_question"] == 1:
            update_mastery(student_state, topic["id"], -0.03)

            base_feedback = (
                f"Not quite. Hint: "
                f"{quiz.get('hint', 'Think about the main purpose of this part of the car.')}"
            )

            return {
                "action": "feedback",
                "message": generate_feedback_message(
                    topic=topic,
                    student_answer=student_message,
                    correct=False,
                    base_feedback=base_feedback
                ),
                "question": quiz.get("question", ""),
                "correct": False,
                "mastery_delta": -0.03
            }

        update_mastery(student_state, topic["id"], -0.02)
        student_state.setdefault("recent_errors", []).append(
            {
                "topic": topic["id"],
                "user_answer": student_message,
                "expected": quiz.get("answer", "")
            }
        )
        student_state["lesson_stage"] = "teach"
        student_state["attempts_on_current_question"] = 0

        base_feedback = f"That was not correct. The correct idea is: {quiz.get('answer', '')}"

        return {
            "action": "feedback",
            "message": generate_feedback_message(
                topic=topic,
                student_answer=student_message,
                correct=False,
                base_feedback=base_feedback
            ),
            "question": None,
            "correct": False,
            "mastery_delta": -0.02
        }

    student_state["lesson_stage"] = "teach"
    student_state["attempts_on_current_question"] = 0

    return {
        "action": "reset",
        "message": "The lesson stage was reset.",
        "question": None,
        "correct": None,
        "mastery_delta": 0.0
    }


def outer_loop(student_state: Dict[str, Any], curriculum: Dict[str, Any]) -> Dict[str, Any]:
    current_topic_id = student_state.get("current_topic", "")
    current_topic = get_topic_by_id(curriculum, current_topic_id)

    if current_topic is None:
        topics = curriculum.get("topics", [])
        if not topics:
            return {
                "advance": False,
                "next_topic": "",
                "reason": "No topics exist in the curriculum."
            }

        first_topic = topics[0]
        student_state["current_topic"] = first_topic["id"]
        student_state["lesson_stage"] = "teach"

        return {
            "advance": False,
            "next_topic": first_topic["id"],
            "reason": "The current topic was missing, so the tutor reset to the first topic."
        }

    current_mastery = float(student_state.get("mastery", {}).get(current_topic_id, 0.0))

    if current_mastery >= 0.75:
        if current_topic_id not in student_state.get("completed_topics", []):
            student_state.setdefault("completed_topics", []).append(current_topic_id)

        next_topic_id = current_topic.get("next_topic", current_topic_id)
        next_topic = get_topic_by_id(curriculum, next_topic_id)

        if next_topic and next_topic_id != current_topic_id and prerequisites_met(student_state, next_topic):
            student_state["current_topic"] = next_topic_id
            student_state["lesson_stage"] = "teach"
            student_state["attempts_on_current_question"] = 0

            return {
                "advance": True,
                "next_topic": next_topic_id,
                "reason": f"Mastery for {current_topic.get('title', current_topic_id)} reached the threshold, so the student advances."
            }

        return {
            "advance": False,
            "next_topic": current_topic_id,
            "reason": f"The student mastered {current_topic.get('title', current_topic_id)}, but there is no new available topic yet."
        }

    if current_mastery < 0.3:
        return {
            "advance": False,
            "next_topic": current_topic_id,
            "reason": f"Mastery for {current_topic.get('title', current_topic_id)} is still low, so the tutor should keep reviewing this topic."
        }

    return {
        "advance": False,
        "next_topic": current_topic_id,
        "reason": f"The student is still practicing {current_topic.get('title', current_topic_id)}."
    }