import json
from pathlib import Path

from tutor_logic import (
    DEFAULT_CURRICULUM,
    DEFAULT_STUDENT_STATE,
    get_topic_by_id,
    inner_loop,
    outer_loop,
)


BASE_DIR = Path(__file__).parent
CURRICULUM_FILE = BASE_DIR / "jsonfiles" / "curriculum.json"
STUDENT_STATE_FILE = BASE_DIR / "jsonfiles" / "student_state.json"


def ensure_file(path, default_data):
    if not path.exists():
        with open(path, "w", encoding="utf-8") as f:
            json.dump(default_data, f, indent=2)


def load_json(path, default_data):
    ensure_file(path, default_data)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def setup_student_state(curriculum, student_state):
    topics = curriculum.get("topics", [])

    if topics and not student_state.get("current_topic"):
        student_state["current_topic"] = topics[0]["id"]

    if topics and not student_state.get("mastery"):
        student_state["mastery"] = {topic["id"]: 0.0 for topic in topics}

    return student_state


def print_state(student_state):
    print("\n--- STUDENT STATE ---")
    print(json.dumps(student_state, indent=2))


def main():
    curriculum = load_json(CURRICULUM_FILE, DEFAULT_CURRICULUM)
    student_state = load_json(STUDENT_STATE_FILE, DEFAULT_STUDENT_STATE)
    student_state = setup_student_state(curriculum, student_state)
    save_json(STUDENT_STATE_FILE, student_state)

    print("Car Education AI Tutor")
    print("Type 'quit' to exit.")
    print("Type 'progress' to view progress.")
    print("Type 'reset' to reset student state.\n")

    while True:
        current_topic = get_topic_by_id(curriculum, student_state.get("current_topic", ""))

        if current_topic is None:
            print("No valid current topic found.")
            break

        user_input = input("You: ").strip()
        
        #Leave the program if the user types 'quit'
        if user_input.lower() == "quit":
            save_json(STUDENT_STATE_FILE, student_state)
            print("Goodbye.")
            break
        #View progress if the user types 'progress'
        if user_input.lower() == "progress":
            print_state(student_state)
            continue

        #Reset progress if the user types 'reset'
        if user_input.lower() == "reset":
            student_state = DEFAULT_STUDENT_STATE.copy()
            student_state = setup_student_state(curriculum, student_state)
            save_json(STUDENT_STATE_FILE, student_state)
            print("Progress reset.")
            continue

        tutor_reply = inner_loop(student_state, current_topic, user_input)
        planner_update = outer_loop(student_state, curriculum)

        save_json(STUDENT_STATE_FILE, student_state)

        print("\nTutor:")
        print(f"Action: {tutor_reply.get('action')}")
        print(f"Message: {tutor_reply.get('message')}")

        if tutor_reply.get("question"):
            print(f"Question: {tutor_reply.get('question')}")

        print(f"Correct: {tutor_reply.get('correct')}")
        print("\nPlanner:")
        print(json.dumps(planner_update, indent=2))
        print()

if __name__ == "__main__":
    main()