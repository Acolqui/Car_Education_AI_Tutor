# Car Education AI Tutor

This project is a beginner-level car education tutor that uses ChatGPT through the OpenAI API. It teaches users through lessons and quizzes, then gives AI-generated feedback on quiz answers.

## Files

### app.py
This is the **web version** of the tutor built with Flask.

What it does:
- Loads the curriculum from `jsonfiles/curriculum.json`
- Loads and saves user progress in `jsonfiles/student_state.json`
- Shows lessons one at a time
- Starts a quiz after lessons are finished
- Checks quiz answers
- Sends the student answer to the AI feedback system
- Updates mastery for each module
- Moves the user to the next module if mastery is high enough

Main features:
- Web-based interface
- Reset progress option
- Lesson and quiz flow
- Mastery tracking
- AI feedback after quiz answers

### cli_app.py
This is the **terminal version** of the tutor.

What it does:
- Loads the same curriculum and student progress JSON files
- Prints lessons in the terminal
- Lets the user move through lessons by typing `next`
- Runs quiz questions in the terminal
- Sends answers to the AI feedback system
- Updates mastery scores
- Decides whether the user moves to the next module or repeats the current one

Main features:
- Terminal-based version for testing
- Same lesson and quiz structure as the web version
- AI feedback in the command line
- Mastery tracking with JSON files

## Requirements

Make sure you have:
- Python installed
- Flask installed (for the web application app.py)
- OpenAI package installed
- A valid `OPENAI_API_KEY`
- The JSON files inside the `jsonfiles` folder

## How to Run

### Web version
Run:

```bash
python app.py
