import json
from openai import OpenAI
from config import OPENAI_API_KEY

client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None


def generate_feedback_message(topic, student_answer, correct, base_feedback):
    if client is None:
        return base_feedback

    try:
        prompt = {
            "topic_title": topic.get("title", "Car Topic"),
            "student_answer": student_answer,
            "correct": correct,
            "base_feedback": base_feedback
        }

        response = client.responses.create(
            model="gpt-5.4-mini",
            input=[
                {"role": "system", "content": "You only generate short feedback for student answers."},
                {"role": "user", "content": json.dumps(prompt)}
            ]
        )

        return getattr(response, "output_text", "").strip() or base_feedback
    except Exception:
        return base_feedback