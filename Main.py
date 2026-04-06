import os
from flask import Flask, request, jsonify, render_template
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

app = Flask(__name__)
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

SYSTEM_PROMPT = """
You are an AI tutor for car education.

Your job is to teach users about:
- car controls and buttons
- dashboard symbols and warning lights
- basic car parts and their functions
- beginner car maintenance
- common warning signs and car problems
- more advanced vehicle system concepts when appropriate

Rules:
1. Adjust explanations to the user's skill level: beginner, intermediate, or advanced.
2. Be clear, patient, and beginner-friendly unless the user asks for technical detail.
3. If a maintenance task could involve safety risk, clearly warn the user.
4. Never guess vehicle-specific facts if uncertain. Say what information is needed.
5. Use step-by-step explanations when teaching maintenance.
6. When possible, connect answers to the user's car make/model/year.
"""

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/ask", methods=["POST"])
def ask():
    data = request.json

    user_question = data.get("question", "")
    skill_level = data.get("skill_level", "beginner")
    car_year = data.get("car_year", "")
    car_make = data.get("car_make", "")
    car_model = data.get("car_model", "")

    vehicle_context = f"""
User skill level: {skill_level}
Vehicle:
- Year: {car_year}
- Make: {car_make}
- Model: {car_model}
"""

    response = client.responses.create(
        model="gpt-5.4-mini",
        input=[
            {"role": "developer", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": f"{vehicle_context}\n\nUser question: {user_question}"
            }
        ]
    )

    return jsonify({
        "answer": response.output_text
    })

if __name__ == "__main__":
    app.run(debug=True)