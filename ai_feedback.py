import json
import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")
print("API key loaded:", bool(api_key))
print("API key preview:", api_key[:12] if api_key else None)

client = OpenAI(api_key=api_key) if api_key else None


def generate_CorrectandFeedback_message(topic, student_answer, base_feedback):
    print("client:", client)

    if client is None:
        return base_feedback

    try:
        prompt = {
            "topic_title": topic,
            "student_answer": student_answer,
            "base_feedback": base_feedback
        }

        response = client.responses.create(
            model="gpt-5.4-mini",
            input=[
                {"role": "system", "content": "You are an expert car education tutor providing feedback on student quiz answers. Your task is to evaluate the student's answer, determine if it is correct or incorrect, and provide constructive feedback based on the topic of the question. Use the base feedback as a reference for the correct answer, but also consider common misconceptions and partial understanding that students might have."},
                {"role": "user", "content": json.dumps(prompt)}
            ]
        )

        return getattr(response, "output_text", "").strip() or base_feedback
    except Exception as e:
        print("OpenAI error:", e)
        return base_feedback