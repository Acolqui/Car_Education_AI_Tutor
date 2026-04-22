from flask import Flask, render_template, request
import json
from pathlib import Path

from ai_feedback import generate_CorrectandFeedback_message

app = Flask(__name__)

BASE_DIR = Path(__file__).parent
CURRICULUM_FILE = BASE_DIR / "jsonfiles" / "curriculum.json"
STUDENT_STATE_FILE = BASE_DIR / "jsonfiles" / "student_state.json"

MASTERY_THRESHOLD = 0.75


def fresh_student_state():
    return {
        "current_module": 1,
        "mastery": {},
        "completed_modules": [],
        "current_lesson_index": 0,
        "quiz_started": False,
        "current_question_index": 0,
        "last_feedback": ""
    }


DEFAULT_STUDENT_STATE = fresh_student_state()


# JSON handling functions *******************
def load_json(path, default_data=None):
    if not path.exists():
        if default_data is None:
            return None
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(default_data, f, indent=2)

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def get_modules_from_json():
    curriculum = load_json(CURRICULUM_FILE, {"modules": [], "quizzes": []})
    return curriculum


def get_module_by_id(curriculum, module_id):
    for module in curriculum.get("modules", []):
        if module.get("id") == module_id:
            return module
    return None


def get_quiz_by_id(curriculum, quiz_id):
    for quiz in curriculum.get("quizzes", []):
        if quiz.get("id") == quiz_id:
            return quiz
    return None


# AI feedback functions *******************
def check_keywords_in_response(ai_response):
    text = ai_response.lower()

    right_keywords = ["correct", "right", "good", "well done"]
    wrong_keywords = ["incorrect", "wrong", "bad", "try again"]
    partially_correct_keywords = ["partially correct", "almost there", "not quite"]

    if any(keyword in text for keyword in partially_correct_keywords):
        return "partial"

    if any(keyword in text for keyword in right_keywords):
        return "correct"

    if any(keyword in text for keyword in wrong_keywords):
        return "wrong"

    return "unknown"


def ai_feedback_update_mastery(student_state, module_id, result):
    mastery = student_state.setdefault("mastery", {})
    key = str(module_id)
    current_score = float(mastery.get(key, 0.0))

    if result == "correct":
        current_score += 0.2
    elif result == "partial":
        current_score += 0.05
    elif result == "wrong":
        current_score -= 0.05

    current_score = max(0.0, min(1.0, round(current_score, 2)))
    mastery[key] = current_score

    if current_score >= MASTERY_THRESHOLD and module_id not in student_state.get("completed_modules", []):
        student_state.setdefault("completed_modules", []).append(module_id)

    return result, current_score


def check_user_progress(student_state, curriculum):
    current_module_id = student_state.get("current_module", 1)
    mastery = float(student_state.get("mastery", {}).get(str(current_module_id), 0.0))

    if mastery >= MASTERY_THRESHOLD:
        next_module_id = current_module_id + 1
        next_module = get_module_by_id(curriculum, next_module_id)

        if next_module:
            student_state["current_module"] = next_module_id
            student_state["current_lesson_index"] = 0
            student_state["quiz_started"] = False
            student_state["current_question_index"] = 0
            student_state["last_feedback"] = ""
            return True, f"Great job. Moving to module {next_module_id}."

        student_state["quiz_started"] = False
        student_state["current_question_index"] = 0
        return False, "You finished all available modules."

    # If mastery is NOT enough, repeat the same module
    student_state["current_lesson_index"] = 0
    student_state["quiz_started"] = False
    student_state["current_question_index"] = 0
    student_state["last_feedback"] = "You did not reach mastery yet, so this module will repeat."
    
    return True, "You did not reach mastery yet, so this module will repeat."


# Lesson / quiz helper functions *******************
def get_current_lesson(module, student_state):
    lessons = module.get("lessons", [])
    lesson_index = student_state.get("current_lesson_index", 0)

    if 0 <= lesson_index < len(lessons):
        return lessons[lesson_index]
    return None


def get_current_question(quiz, student_state):
    if not quiz:
        return None

    questions = quiz.get("questions", [])
    question_index = student_state.get("current_question_index", 0)

    if 0 <= question_index < len(questions):
        return questions[question_index]
    return None


def normalize_text(text):
    return text.strip().lower()


def answer_matches(user_answer, correct_answer):
    if not user_answer or not correct_answer:
        return False

    user = normalize_text(user_answer)
    correct = normalize_text(correct_answer)

    if user == correct:
        return True

    if user in correct or correct in user:
        return True

    user_words = set(user.split())
    correct_words = set(correct.split())

    if not correct_words:
        return False

    overlap = len(user_words.intersection(correct_words))
    ratio = overlap / len(correct_words)

    return ratio >= 0.5


@app.route("/", methods=["GET", "POST"])
def index():
    curriculum = get_modules_from_json()
    student_state = load_json(STUDENT_STATE_FILE, fresh_student_state())

    module_id = student_state.get("current_module", 1)
    module = get_module_by_id(curriculum, module_id)
    quiz = get_quiz_by_id(curriculum, module_id)

    message = ""
    ai_feedback = ""
    result = None
    mastery_score = None

    if request.method == "POST":
        action = request.form.get("action", "")
        user_answer = request.form.get("user_answer", "").strip()

        if action == "reset":
            student_state = fresh_student_state()
            save_json(STUDENT_STATE_FILE, student_state)
            module = get_module_by_id(curriculum, 1)

            return render_template(
                "index.html",
                module=module,
                lesson=get_current_lesson(module, student_state),
                quiz_started=False,
                question=None,
                student_state=student_state,
                message="Progress reset.",
                ai_feedback="",
                result=None,
                mastery_score=None
            )

        if not module:
            message = "No module found."
        else:
            if action == "next_lesson":
                student_state["current_lesson_index"] = student_state.get("current_lesson_index", 0) + 1

                if student_state["current_lesson_index"] >= len(module.get("lessons", [])):
                    student_state["quiz_started"] = False
                    message = "Lesson complete. You can now start the quiz."
                else:
                    message = "Moved to next lesson."

            elif action == "start_quiz":
                student_state["quiz_started"] = True
                student_state["current_question_index"] = 0
                message = "Quiz started."

            elif action == "submit_answer":
                current_question = get_current_question(quiz, student_state)

                if current_question:
                    correct_answer = current_question.get("answer", "")
                    is_correct = answer_matches(user_answer, correct_answer)

                    if is_correct:
                        base_feedback = f"Good job. That is correct. Correct answer: {correct_answer}"
                        delta_text = "correct"
                    else:
                        base_feedback = f"Not quite. The correct answer is: {correct_answer}"
                        delta_text = "wrong"

                    ai_response = generate_CorrectandFeedback_message(
                        module.get("title", "Unknown Topic"),
                        user_answer,
                        base_feedback
                    )

                    ai_feedback = ai_response
                    student_state["last_feedback"] = ai_response

                    result, mastery_score = ai_feedback_update_mastery(
                        student_state,
                        module["id"],
                        delta_text
                    )

                    student_state["current_question_index"] = student_state.get("current_question_index", 0) + 1

                    if student_state["current_question_index"] >= len(quiz.get("questions", [])):
                        user_progress, progress_message = check_user_progress(student_state, curriculum)

                        if user_progress:
                            message = f"Quiz complete. {progress_message}"
                        else:
                            message = progress_message

                        module_id = student_state.get("current_module", 1)
                        module = get_module_by_id(curriculum, module_id)
                        quiz = get_quiz_by_id(curriculum, module_id)
                    else:
                        message = "Answer submitted."

        save_json(STUDENT_STATE_FILE, student_state)

        module_id = student_state.get("current_module", 1)
        module = get_module_by_id(curriculum, module_id)
        quiz = get_quiz_by_id(curriculum, module_id)

    lesson = None
    question = None

    if module:
        if student_state.get("quiz_started", False):
            question = get_current_question(quiz, student_state)
        else:
            lesson = get_current_lesson(module, student_state)

    return render_template(
        "index.html",
        module=module,
        lesson=lesson,
        quiz_started=student_state.get("quiz_started", False),
        question=question,
        student_state=student_state,
        message=message,
        ai_feedback=ai_feedback,
        result=result,
        mastery_score=mastery_score
    )


if __name__ == "__main__":
    app.run(debug=True)