import json
from pathlib import Path

from ai_feedback import generate_CorrectandFeedback_message


BASE_DIR = Path(__file__).parent
CURRICULUM_FILE = BASE_DIR / "jsonfiles" / "curriculum.json"
STUDENT_STATE_FILE = BASE_DIR / "jsonfiles" / "student_state.json"


DEFAULT_STUDENT_STATE = {
    "current_module": 1,
    "mastery": {},
    "completed_modules": []
}

#JSON handling functions
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

# AI feedback functions
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


def ai_feedback_update_mastery(student_state, module_id, ai_response):
    result = check_keywords_in_response(ai_response)

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

    if current_score >= 0.75 and module_id not in student_state.get("completed_modules", []):
        student_state.setdefault("completed_modules", []).append(module_id)

    return result, current_score


def check_user_progress(student_state, curriculum):
    current_module_id = student_state.get("current_module", 1)
    mastery = float(student_state.get("mastery", {}).get(str(current_module_id), 0.0))

    if mastery >= 0.75:
        next_module_id = current_module_id + 1
        next_module = get_module_by_id(curriculum, next_module_id)

        if next_module:
            student_state["current_module"] = next_module_id
            return True, f"Great job. Moving to module {next_module_id}."
        return False, "You finished all available modules."

    return True, "Keep practicing this module."


def teach_module(module):
    print(f"\nModule {module['id']}: {module['title']}")
    print(f"Images folder: {module.get('imageDIR', '')}")

    for lesson in module.get("lessons", []):
        print(f"\nLesson: {lesson['title']}")
        print(lesson["content"])
        userInput = input("\nType 'next' to continue to the next lesson or quiz: ").strip().lower()
        while userInput != "next":
            userInput = input("Please type 'next' to continue: ").strip().lower()


def run_quiz(module, quiz, student_state):
    print("\nQuiz Time")

    for question_data in quiz.get("questions", []):
        print(f"\nQuestion: {question_data['question']}")
        user_answer = input("Your answer: ").strip()

        correct_answer = question_data.get("answer", "")
        base_feedback = f"Correct answer: {correct_answer}"

        ai_response = generate_CorrectandFeedback_message(
            module.get("title", "Unknown Topic"),
            user_answer,
            base_feedback
        )

        print("\nAI Feedback:")
        print(ai_response)

        result, mastery_score = ai_feedback_update_mastery(
            student_state,
            module["id"],
            ai_response
        )

        print(f"Result: {result}")
        print(f"Updated mastery for module {module['id']}: {mastery_score}")


def main():
    curriculum = get_modules_from_json()
    student_state = load_json(STUDENT_STATE_FILE, DEFAULT_STUDENT_STATE)

    print("\n\n\n\n\n\n\nWelcome to the Car Education AI Tutor!")

    user_progress = True

    while user_progress:
        current_module_id = student_state.get("current_module", 1)
        module = get_module_by_id(curriculum, current_module_id)
        quiz = get_quiz_by_id(curriculum, current_module_id)

        if not module:
            print("No module found.")
            break

        teach_module(module)

        if quiz:
            run_quiz(module, quiz, student_state)
        else:
            print("No quiz found for this module.")

        save_json(STUDENT_STATE_FILE, student_state)

        user_progress, message = check_user_progress(student_state, curriculum)
        print(f"\n{message}")

    save_json(STUDENT_STATE_FILE, student_state)
    print("Goodbye.")


if __name__ == "__main__":
    main()